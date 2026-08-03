#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Callable, Sequence
from pathlib import Path


Violation = tuple[int, str, str]
Check = Callable[[list[str]], list[Violation]]
HEADING_LEVEL_RULE = "heading-level"
HEADING = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+|$)")
BADGE_FORM_RULE = "badge-form"
SHIELDS_URL = re.compile(r"https?://img\.shields\.io/[^\s<>'\")]+")
BADGE_FORM = re.compile(
    r"https://img\.shields\.io/badge/[^-/\s?]+-[^-/\s?]+"
    r"\?style=flat(?:&logo=[^&\s<>'\")]+(?:&logoColor=white)?)?"
)
ALT_TEXT_RULE = "alt-text"
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
APPROVED_LINK_TARGETS = frozenset(
    {
        "https://ha.ggis.xyz",
        "https://ha.ggis.xyz/wild",
        "https://ha.ggis.xyz/just-five-more-minutes/",
        "https://github.com/Giftedx/ha-ggis-hub",
        "https://github.com/Giftedx/wild-haggis-survivors",
        "https://github.com/Giftedx/Project-Euler-Clanker",
    }
)


def check_heading_levels(lines: list[str]) -> list[Violation]:
    violations: list[Violation] = []
    previous_level: int | None = None
    fence_char: str | None = None
    fence_length = 0

    for line_number, line in enumerate(lines, start=1):
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


def check_badge_form(lines: list[str]) -> list[Violation]:
    violations: list[Violation] = []
    for line_number, line in enumerate(lines, start=1):
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


def check_alt_text(lines: list[str]) -> list[Violation]:
    violations: list[Violation] = []
    for line_number, line in enumerate(lines, start=1):
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


def check_link_targets(lines: list[str]) -> list[Violation]:
    violations: list[Violation] = []
    for line_number, line in enumerate(lines, start=1):
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


CHECKS: tuple[Check, ...] = (
    check_heading_levels,
    check_badge_form,
    check_alt_text,
    check_link_targets,
)
CHECK_RULE_IDS: dict[Check, str] = {
    check_heading_levels: HEADING_LEVEL_RULE,
    check_badge_form: BADGE_FORM_RULE,
    check_alt_text: ALT_TEXT_RULE,
    check_link_targets: LINK_TARGET_RULE,
}


def collect_violations(lines: list[str]) -> list[Violation]:
    violations: list[Violation] = []
    for check in CHECKS:
        violations.extend(check(lines))
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
    actual = collect_violations(bad_lines)
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
    actual = collect_violations(good_lines)
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
        actual = collect_violations([sample])
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
        "![Phaser](https://img.shields.io/badge/Phaser%204-9070b0?style=flat)\n"
        "![Astro](https://img.shields.io/badge/Astro-BC52EE?style=flat&logo=astro&logoColor=white)\n"
        "![License](https://img.shields.io/badge/License-blue?style=flat)\n"
        "![Go](https://img.shields.io/badge/Go-00ADD8?style=flat&logo=go)\n"
    ).splitlines()
    actual = collect_violations(good_badge_lines)
    if actual:
        print(
            f"selftest: badge-form: expected no violations, got {actual!r}",
            file=sys.stderr,
        )
        return 1

    bad_alt_text_samples = (
        (
            '<img src="./assets/x.png" />',
            [(1, "alt-text", "image alt text is missing or empty")],
        ),
        (
            '<img src="./assets/x.png" alt="banner" />',
            [
                (
                    1,
                    "alt-text",
                    "content image alt text has 1 word. Use at least 4 words",
                )
            ],
        ),
        (
            "![](./assets/x.png)",
            [(1, "alt-text", "image alt text is missing or empty")],
        ),
    )
    for sample, expected in bad_alt_text_samples:
        actual = collect_violations([sample])
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
    actual = collect_violations(good_alt_text_lines)
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
    actual = collect_violations(bad_link_lines)
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
    actual = collect_violations(good_link_lines)
    if actual:
        print(
            f"selftest: link-target: expected no violations, got {actual!r}",
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
    violations = collect_violations(lines)
    report_violations(args.path, violations)
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
