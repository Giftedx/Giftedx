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


CHECKS: tuple[Check, ...] = (check_heading_levels, check_badge_form)


def collect_violations(lines: list[str]) -> list[Violation]:
    violations: list[Violation] = []
    for check in CHECKS:
        violations.extend(check(lines))
    return violations


def report_violations(path: Path, violations: list[Violation]) -> None:
    for line, rule, message in violations:
        print(f"{path}:{line}: {rule}: {message}")


def run_selftest() -> int:
    bad_lines = "# A\n### B\n".splitlines()
    expected = [
        (2, HEADING_LEVEL_RULE, "heading level jumps from h1 to h3"),
    ]
    actual = check_heading_levels(bad_lines)
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
    actual = check_heading_levels(good_lines)
    if actual:
        print(
            f"selftest: {HEADING_LEVEL_RULE}: expected no violations, got {actual!r}",
            file=sys.stderr,
        )
        return 1

    bad_badge_samples = (
        "https://img.shields.io/badge/Phaser-4-9070b0?style=flat",
        '<img src="https://img.shields.io/badge/Go-00ADD8?style=for-the-badge">',
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

    print("selftest: 2 rules covered")
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
