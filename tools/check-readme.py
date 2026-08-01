#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Callable, Sequence
from pathlib import Path


Violation = tuple[int, str, str]
Check = Callable[[Path, list[str]], list[Violation]]
HEADING_LEVEL_RULE = "heading-level"
HEADING = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+|$)")


def check_heading_levels(path: Path, lines: list[str]) -> list[Violation]:
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


MISSING_IMAGE_RULE = "missing-image"
IMAGE_REF = re.compile(r'src="([^"]+)"|!\[[^\]]*\]\(([^)]+)\)')

def check_local_images(path: Path, lines: list[str]) -> list[Violation]:
    violations: list[Violation] = []
    for line_number, line in enumerate(lines, start=1):
        for match in IMAGE_REF.finditer(line):
            img = match.group(1) or match.group(2)
            if not img.startswith(("http://", "https://", "data:")):
                if not (path.parent / img).is_file():
                    violations.append((line_number, MISSING_IMAGE_RULE, f"missing {img}"))
    return violations

CHECKS: tuple[Check, ...] = (check_heading_levels, check_local_images)


def collect_violations(path: Path, lines: list[str]) -> list[Violation]:
    violations: list[Violation] = []
    for check in CHECKS:
        violations.extend(check(path, lines))
    return violations


def report_violations(path: Path, violations: list[Violation]) -> None:
    for line, rule, message in violations:
        print(f"{path}:{line}: {rule}: {message}")


def run_selftest() -> int:
    bad_lines = "# A\n### B\n".splitlines()
    expected = [
        (2, HEADING_LEVEL_RULE, "heading level jumps from h1 to h3"),
    ]
    actual = check_heading_levels(Path("README.md"), bad_lines)
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
    actual = check_heading_levels(Path("README.md"), good_lines)
    if actual:
        print(
            f"selftest: {HEADING_LEVEL_RULE}: expected no violations, got {actual!r}",
            file=sys.stderr,
        )
        return 1

    bad_img = ['<img src="./assets/does-not-exist.png" />']
    expected_img = [(1, MISSING_IMAGE_RULE, "missing ./assets/does-not-exist.png")]
    actual_img = check_local_images(Path("README.md"), bad_img)
    if actual_img != expected_img:
        print(
            f"selftest: {MISSING_IMAGE_RULE}: expected {expected_img!r}, got {actual_img!r}",
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

    lines = args.path.read_text(encoding="utf-8").splitlines()
    violations = collect_violations(args.path, lines)
    report_violations(args.path, violations)
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
