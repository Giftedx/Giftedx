#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote


Violation = tuple[int, str, str]

@dataclass
class Document:
    lines: list[str]
    base_dir: Path
Check = Callable[[Document], list[Violation]]
HEADING_LEVEL_RULE = "heading-level"
HEADING = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+|$)")
BADGE_FORM_RULE = "badge-form"
SHIELDS_URL = re.compile(r"https?://img\.shields\.io/[^\s<>'\")]+")
BADGE_FORM = re.compile(
    r"https://img\.shields\.io/badge/[^-/\s?]+-[^-/\s?]+"
    r"\?style=flat(?:&logo=[^&\s<>'\")]+(?:&logoColor=white)?)?"
)
BADGE_ALT_TEXT_RULE = "badge-alt-text"
BADGE_LABEL = re.compile(
    r"^https?://img\.shields\.io/badge/([^-/\s?]+)-"
)
ALT_TEXT_RULE = "alt-text"
ASSET_MISSING_RULE = "asset-missing"
HTML_IMAGE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
HTML_ALT = re.compile(
    r"\balt\s*=\s*(?:([\"'])(.*?)\1|([^\s>]+))",
    re.IGNORECASE,
)
HTML_SRC = re.compile(
    r"\bsrc\s*=\s*(?:([\"'])(.*?)\1|([^\s>]+))",
    re.IGNORECASE,
)
MARKDOWN_IMAGE = re.compile(
    r"!\[([^\]]*)\]\(\s*(?:<([^>]+)>|([^\s)]+))"
)
ALT_WORD = re.compile(r"\b\w+(?:[’'-]\w+)*\b")
LINK_TARGET_RULE = "link-target"
HTML_HREF = re.compile(r"""<a\b[^>]*\bhref\s*=\s*(["'])(.*?)\1""", re.IGNORECASE)
MARKDOWN_LINK_TARGET = re.compile(
    r"(?<!!)\[[^\]]+\]\(\s*(?:<([^>]+)>|([^\s)]+))"
)
WORKSHOP_PROJECTS_RULE = "workshop-projects"
SHOP_SUBGRAPH = re.compile(r"^\s*subgraph\s+shop(?:\[.*\])?\s*$")
MERMAID_NODE = re.compile(r'^\s*[\w-]+\s*\[\s*"([^"]+)"\s*\]')
WORKSHOP_TABLE_HEADER = re.compile(r"^\|\s*Project\s*\|")
WORKSHOP_TABLE_PROJECT = re.compile(r"^\|\s*\*\*(.+?)\*\*\s*\|")
WORKSHOP_TABLE_NON_PROJECTS = frozenset({"The robot"})
APPROVED_LINK_TARGETS = frozenset(
    {
        "https://ha.ggis.xyz",
        "https://ha.ggis.xyz/wild",
        "https://ha.ggis.xyz/just-five-more-minutes/",
        "https://github.com/Giftedx/ha-ggis-hub",
        "https://github.com/Giftedx/wild-haggis-survivors",
        "https://github.com/Giftedx/just-five-more-minutes",
        "https://github.com/Giftedx/Project-Euler-Clanker",
    }
)


def check_heading_levels(document: Document) -> list[Violation]:
    violations: list[Violation] = []
    previous_level: int | None = None
    fence_char: str | None = None
    fence_length = 0

    for line_number, line in enumerate(document.lines, start=1):
        stripped = line.lstrip(" ")
        indent = len(line) - len(stripped)

        if fence_char is not None:
            marker_length = len(stripped) - len(stripped.lstrip(fence_char))
            if (
                indent <= 3
                and marker_length >= fence_length
                and not stripped[marker_length:].strip()
            ):
                fence_char = None
                fence_length = 0
            continue

        marker_char = stripped[:1]
        if indent <= 3 and marker_char in ("`", "~"):
            marker_length = len(stripped) - len(stripped.lstrip(marker_char))
            info = stripped[marker_length:]
            if marker_length >= 3 and not (
                marker_char == "`" and "`" in info
            ):
                fence_char = marker_char
                fence_length = marker_length
                continue

        match = HEADING.match(line)
        if match is None:
            continue

        level = len(match.group(1))
        if previous_level is None and level != 1:
            violations.append(
                (
                    line_number,
                    HEADING_LEVEL_RULE,
                    f"heading outline starts at h{level}, not h1",
                )
            )
        elif previous_level is not None and level > previous_level + 1:
            violations.append(
                (
                    line_number,
                    HEADING_LEVEL_RULE,
                    f"heading level jumps from h{previous_level} to h{level}",
                )
            )
        previous_level = level

    return violations


def check_badge_form(document: Document) -> list[Violation]:
    violations: list[Violation] = []
    for line_number, line in enumerate(document.lines, start=1):
        for match in SHIELDS_URL.finditer(line):
            if BADGE_FORM.fullmatch(match.group()) is None:
                violations.append(
                    (
                        line_number,
                        BADGE_FORM_RULE,
                        "shields.io badge URL does not use the "
                        "two-segment style=flat form",
                    )
                )
    return violations


def check_badge_alt_text(document: Document) -> list[Violation]:
    violations: list[Violation] = []
    for line_number, line in enumerate(document.lines, start=1):
        images: list[tuple[str | None, str]] = []
        for image_match in HTML_IMAGE.finditer(line):
            image = image_match.group()
            alt_match = HTML_ALT.search(image)
            src_match = HTML_SRC.search(image)
            alt = None
            if alt_match is not None:
                alt = alt_match.group(2) or alt_match.group(3) or ""
            src = ""
            if src_match is not None:
                src = src_match.group(2) or src_match.group(3) or ""
            images.append((alt, src))

        images.extend(
            (match.group(1), match.group(2) or match.group(3))
            for match in MARKDOWN_IMAGE.finditer(line)
        )

        for alt, src in images:
            label_match = BADGE_LABEL.match(src)
            if label_match is None or alt is None or not alt.strip():
                continue
            label = unquote(label_match.group(1))
            if alt.strip() != label:
                violations.append(
                    (
                        line_number,
                        BADGE_ALT_TEXT_RULE,
                        f"badge alt text does not match the badge label {label!r}",
                    )
                )

    return violations


def check_alt_text(document: Document) -> list[Violation]:
    violations: list[Violation] = []
    for line_number, line in enumerate(document.lines, start=1):
        images: list[tuple[str | None, str]] = []
        for image_match in HTML_IMAGE.finditer(line):
            image = image_match.group()
            alt_match = HTML_ALT.search(image)
            src_match = HTML_SRC.search(image)
            alt = None
            if alt_match is not None:
                alt = alt_match.group(2) or alt_match.group(3) or ""
            src = ""
            if src_match is not None:
                src = src_match.group(2) or src_match.group(3) or ""
            images.append((alt, src))

        images.extend(
            (match.group(1), match.group(2) or match.group(3))
            for match in MARKDOWN_IMAGE.finditer(line)
        )

        for alt, src in images:
            if alt is None or not alt.strip():
                violations.append(
                    (
                        line_number,
                        ALT_TEXT_RULE,
                        "image alt text is missing or empty",
                    )
                )
                continue

            word_count = len(ALT_WORD.findall(alt))
            if "img.shields.io/" not in src and word_count < 4:
                word_label = "word" if word_count == 1 else "words"
                violations.append(
                    (
                        line_number,
                        ALT_TEXT_RULE,
                        f"content image alt text has {word_count} {word_label}. "
                        "Use at least 4 words",
                    )
                )

    return violations


def check_link_targets(document: Document) -> list[Violation]:
    violations: list[Violation] = []
    for line_number, line in enumerate(document.lines, start=1):
        targets = [match.group(2) for match in HTML_HREF.finditer(line)]
        targets.extend(
            match.group(1) or match.group(2)
            for match in MARKDOWN_LINK_TARGET.finditer(line)
        )
        for target in targets:
            if target.startswith(("http://", "https://")) and (
                target not in APPROVED_LINK_TARGETS
            ):
                violations.append(
                    (
                        line_number,
                        LINK_TARGET_RULE,
                        "outbound link target is not approved",
                    )
                )
    return violations


def check_workshop_projects(document: Document) -> list[Violation]:
    shop_projects: dict[str, int] = {}
    table_projects: dict[str, int] = {}
    in_shop = False
    in_table = False

    for line_number, line in enumerate(document.lines, start=1):
        if SHOP_SUBGRAPH.match(line):
            in_shop = True
            continue
        if in_shop:
            if line.strip() == "end":
                in_shop = False
                continue
            match = MERMAID_NODE.match(line)
            if match:
                shop_projects[match.group(1)] = line_number

        if WORKSHOP_TABLE_HEADER.match(line):
            in_table = True
            continue
        if in_table:
            match = WORKSHOP_TABLE_PROJECT.match(line)
            if match:
                project = match.group(1)
                if project not in WORKSHOP_TABLE_NON_PROJECTS:
                    table_projects[project] = line_number
            elif not line.startswith("|"):
                in_table = False

    violations: list[Violation] = []
    for project in sorted(table_projects.keys() - shop_projects.keys()):
        violations.append(
            (
                table_projects[project],
                WORKSHOP_PROJECTS_RULE,
                "workshop table project is missing from shop subgraph: "
                f"{project}",
            )
        )
    for project in sorted(shop_projects.keys() - table_projects.keys()):
        violations.append(
            (
                shop_projects[project],
                WORKSHOP_PROJECTS_RULE,
                "shop subgraph project is missing from workshop table: "
                f"{project}",
            )
        )
    return violations


def check_asset_missing(document: Document) -> list[Violation]:
    violations: list[Violation] = []
    for line_number, line in enumerate(document.lines, start=1):
        images: list[str] = []
        for image_match in HTML_IMAGE.finditer(line):
            image = image_match.group()
            src_match = HTML_SRC.search(image)
            if src_match is not None:
                src = src_match.group(2) or src_match.group(3) or ""
                images.append(src)

        images.extend(
            (match.group(2) or match.group(3))
            for match in MARKDOWN_IMAGE.finditer(line)
        )

        for src in images:
            if src.startswith(("http://", "https://", "data:")):
                continue

            # resolve relative to base_dir
            try:
                # unquote is imported
                path_str = unquote(src)
                resolved_path = document.base_dir / path_str
                if not resolved_path.is_file():
                    violations.append((
                        line_number,
                        ASSET_MISSING_RULE,
                        f"referenced image does not exist: {src}",
                    ))
            except Exception:
                pass

    return violations

CHECKS: tuple[Check, ...] = (
    check_heading_levels,
    check_badge_form,
    check_badge_alt_text,
    check_alt_text,
    check_link_targets,
    check_workshop_projects,
    check_asset_missing,
)
CHECK_RULE_IDS: dict[Check, str] = {
    check_heading_levels: HEADING_LEVEL_RULE,
    check_badge_form: BADGE_FORM_RULE,
    check_badge_alt_text: BADGE_ALT_TEXT_RULE,
    check_alt_text: ALT_TEXT_RULE,
    check_link_targets: LINK_TARGET_RULE,
    check_workshop_projects: WORKSHOP_PROJECTS_RULE,
    check_asset_missing: ASSET_MISSING_RULE,
}


def collect_violations(document: Document) -> list[Violation]:
    violations: list[Violation] = []
    for check in CHECKS:
        violations.extend(check(document))
    return violations


def report_violations(path: Path, violations: list[Violation]) -> None:
    for line, rule, message in violations:
        print(f"{path}:{line}: {rule}: {message}")


def run_selftest() -> int:
    covered_rule_ids: set[str] = set()

    bad_lines = "# A\n### B\n".splitlines()
    expected = [
        (2, HEADING_LEVEL_RULE, "heading level jumps from h1 to h3"),
    ]
    actual = collect_violations(Document(bad_lines, Path('.')))
    covered_rule_ids.update(rule for _, rule, _ in actual)
    if actual != expected:
        print(
            f"selftest: {HEADING_LEVEL_RULE}: expected {expected!r}, got {actual!r}",
            file=sys.stderr,
        )
        return 1

    good_lines = (
        "# A\n"
        "\n"
        "```sh\n"
        "# install\n"
        "### not a heading\n"
        "```\n"
        "\n"
        "## B\n"
    ).splitlines()
    actual = collect_violations(Document(good_lines, Path('.')))
    if actual:
        print(
            f"selftest: {HEADING_LEVEL_RULE}: expected no violations, got {actual!r}",
            file=sys.stderr,
        )
        return 1

    bad_badge_samples = (
        "https://img.shields.io/badge/Phaser-4-9070b0?style=flat",
        '<img src="https://img.shields.io/badge/Go-00ADD8?style=for-the-badge" alt="Go">',
    )
    expected_badge_violation = [
        (
            1,
            "badge-form",
            "shields.io badge URL does not use the two-segment style=flat form",
        )
    ]
    for sample in bad_badge_samples:
        actual = collect_violations(Document([sample], Path('.')))
        covered_rule_ids.update(rule for _, rule, _ in actual)
        if actual != expected_badge_violation:
            print(
                "selftest: badge-form: "
                f"expected {expected_badge_violation!r}, got {actual!r}",
                file=sys.stderr,
            )
            return 1

    good_badge_lines = (
        "![Rust](https://img.shields.io/badge/Rust-000000?style=flat&logo=rust&logoColor=white)\n"
        "![Go](https://img.shields.io/badge/Go-00ADD8?style=flat&logo=go&logoColor=white)\n"
        "![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat&logo=typescript&logoColor=white)\n"
        "![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)\n"
        "![WebAssembly](https://img.shields.io/badge/WebAssembly-654FF0?style=flat&logo=webassembly&logoColor=white)\n"
        "![Phaser 4](https://img.shields.io/badge/Phaser%204-9070b0?style=flat)\n"
        "![Astro](https://img.shields.io/badge/Astro-BC52EE?style=flat&logo=astro&logoColor=white)\n"
        "![License](https://img.shields.io/badge/License-blue?style=flat)\n"
        "![Go](https://img.shields.io/badge/Go-00ADD8?style=flat&logo=go)\n"
    ).splitlines()
    actual = collect_violations(Document(good_badge_lines, Path('.')))
    if actual:
        print(
            f"selftest: badge-form: expected no violations, got {actual!r}",
            file=sys.stderr,
        )
        return 1

    bad_badge_alt_lines = (
        "![Phaser](https://img.shields.io/badge/Phaser%204-9070b0?style=flat)"
    ).splitlines()
    expected = [
        (
            1,
            "badge-alt-text",
            "badge alt text does not match the badge label 'Phaser 4'",
        ),
    ]
    actual = collect_violations(Document(bad_badge_alt_lines, Path('.')))
    covered_rule_ids.update(rule for _, rule, _ in actual)
    if actual != expected:
        print(
            f"selftest: badge-alt-text: expected {expected!r}, got {actual!r}",
            file=sys.stderr,
        )
        return 1

    bad_alt_text_samples = (
        (
            '<img src="./assets/x.png" />',
            [(1, "alt-text", "image alt text is missing or empty"), (1, "asset-missing", "referenced image does not exist: ./assets/x.png")],
        ),
        (
            '<img src="./assets/x.png" alt="banner" />',
            [
                (
                    1,
                    "alt-text",
                    "content image alt text has 1 word. Use at least 4 words",
                ),
                (1, "asset-missing", "referenced image does not exist: ./assets/x.png"),
            ],
        ),
        (
            "![](./assets/x.png)",
            [(1, "alt-text", "image alt text is missing or empty"), (1, "asset-missing", "referenced image does not exist: ./assets/x.png")],
        ),
    )
    for sample, expected in bad_alt_text_samples:
        actual = collect_violations(Document([sample], Path('.')))
        covered_rule_ids.update(rule for _, rule, _ in actual)
        if actual != expected:
            print(
                f"selftest: alt-text: expected {expected!r}, got {actual!r}",
                file=sys.stderr,
            )
            return 1

    good_alt_text_lines = (
        '<img src="./assets/banner.png" alt="Four projects shown side by side" />\n'
        '<img src="./assets/hub-bothy.png" alt="A Highland cottage interior at sunset" />\n'
        '<img src="./assets/whs-menu.png" alt="Wild Haggis Survivors main menu" />\n'
        "![Rust](https://img.shields.io/badge/Rust-000000?style=flat&logo=rust&logoColor=white)\n"
        "![Go](https://img.shields.io/badge/Go-00ADD8?style=flat&logo=go&logoColor=white)\n"
        "![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat&logo=typescript&logoColor=white)\n"
        "![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)\n"
        "![WebAssembly](https://img.shields.io/badge/WebAssembly-654FF0?style=flat&logo=webassembly&logoColor=white)\n"
        "![Phaser 4](https://img.shields.io/badge/Phaser%204-9070b0?style=flat)\n"
        "![Astro](https://img.shields.io/badge/Astro-BC52EE?style=flat&logo=astro&logoColor=white)\n"
    ).splitlines()

    # Mock files for good_alt_text_lines so asset-missing won't trigger
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()
        (assets_dir / "banner.png").touch()
        (assets_dir / "hub-bothy.png").touch()
        (assets_dir / "whs-menu.png").touch()
        actual = collect_violations(Document(good_alt_text_lines, tmp_path))
        if actual:
            print(
                f"selftest: alt-text: expected no violations, got {actual!r}",
                file=sys.stderr,
            )
            return 1

    bad_link_lines = (
        "[Just Five More Minutes]"
        "(https://ha.ggis.xyz/just-five-more-minuets/)"
    ).splitlines()
    expected = [
        (1, "link-target", "outbound link target is not approved"),
    ]
    actual = collect_violations(Document(bad_link_lines, Path('.')))
    covered_rule_ids.update(rule for _, rule, _ in actual)
    if actual != expected:
        print(
            f"selftest: link-target: expected {expected!r}, got {actual!r}",
            file=sys.stderr,
        )
        return 1

    good_link_lines = (
        "<a href=\"https://ha.ggis.xyz/wild\">Play</a>\n"
        "[Source](https://github.com/Giftedx/ha-ggis-hub)\n"
    ).splitlines()
    actual = collect_violations(Document(good_link_lines, Path('.')))
    if actual:
        print(
            f"selftest: link-target: expected no violations, got {actual!r}",
            file=sys.stderr,
        )
        return 1

    bad_workshop_lines = (
        "```mermaid\n"
        "flowchart LR\n"
        '    subgraph shop["The workshop — private, for now"]\n'
        '        ag["AccentGuessr"]\n'
        "    end\n"
        "```\n"
        "\n"
        "# In the workshop\n"
        "\n"
        "| Project | What it is |\n"
        "| --- | --- |\n"
        "| **The robot** | It tends the projects. |\n"
        "| **AccentGuessr** | A game. |\n"
        "| **Kittiwake** | A website. |\n"
    ).splitlines()
    expected = [
        (
            14,
            "workshop-projects",
            "workshop table project is missing from shop subgraph: Kittiwake",
        ),
    ]
    actual = collect_violations(Document(bad_workshop_lines, Path('.')))
    covered_rule_ids.update(rule for _, rule, _ in actual)
    if actual != expected:
        print(
            "selftest: workshop-projects: "
            f"expected {expected!r}, got {actual!r}",
            file=sys.stderr,
        )
        return 1


    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()

        readme_path = tmp_path / "README.md"
        readme_path.write_text('<img src="./assets/nope.png" alt="This is four words" />\n')

        expected_asset_violation = [
            (1, ASSET_MISSING_RULE, "referenced image does not exist: ./assets/nope.png"),
        ]
        actual = collect_violations(Document(readme_path.read_text().splitlines(), tmp_path))
        covered_rule_ids.update(rule for _, rule, _ in actual)

        if actual != expected_asset_violation:
            print(
                "selftest: asset-missing: "
                f"expected {expected_asset_violation!r}, got {actual!r}",
                file=sys.stderr,
            )
            return 1

        # clean case
        good_asset_file = assets_dir / "yep.png"
        good_asset_file.touch()
        readme_path.write_text(
            '<img src="./assets/yep.png" alt="This is four words" />\n'
            '![This is four words](https://example.com/image.png)\n'
            '![This is four words](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==)\n'
        )
        actual = collect_violations(Document(readme_path.read_text().splitlines(), tmp_path))
        if actual:
            print(
                f"selftest: asset-missing: expected no violations, got {actual!r}",
                file=sys.stderr,
            )
            return 1

    expected_rule_ids = {CHECK_RULE_IDS[check] for check in CHECKS}
    if covered_rule_ids != expected_rule_ids:
        missing = sorted(expected_rule_ids - covered_rule_ids)
        unexpected = sorted(covered_rule_ids - expected_rule_ids)
        print(
            "selftest: rule coverage mismatch: "
            f"missing {missing!r}, unexpected {unexpected!r}",
            file=sys.stderr,
        )
        return 1

    print(f"selftest: {len(CHECKS)} rules covered")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check README.md before publication.")
    parser.add_argument("path", nargs="?", type=Path, default=Path("README.md"))
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)

    if args.selftest:
        return run_selftest()

    try:
        lines = args.path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as error:
        print(f"error: cannot read {args.path}: {error}", file=sys.stderr)
        return 2
    violations = collect_violations(Document(lines, args.path.parent))
    report_violations(args.path, violations)
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
