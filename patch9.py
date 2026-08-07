with open("tools/check-readme.py", "r") as f:
    content = f.read()

test_cases_orig = """    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()
        readme_path = tmp_path / "README.md"

        # bad case
        bad_asset_lines = [
            '<img src="./assets/nope.png" alt="Nope" />',
        ]
        expected_asset_violation = [
            (1, ASSET_MISSING_RULE, "referenced image does not exist: ./assets/nope.png"),
        ]

        actual = collect_violations(Document(bad_asset_lines, tmp_path))
        covered_rule_ids.update(rule for _, rule, _ in actual)

        # We also have to filter by the rule since alt_text might flag something depending on how the line is written,
        # but our expected test cases specifically check for asset-missing. Actually, alt-text is fine here because "Nope" is 1 word, which might trigger alt-text.
        # Wait, alt-text requires >= 4 words if there's alt text.
        # Let's adjust the alt-text to 4 words to avoid alt-text violations in the bad case.
        bad_asset_lines = [
            '<img src="./assets/nope.png" alt="This is four words" />',
        ]
        actual = collect_violations(Document(bad_asset_lines, tmp_path))
        covered_rule_ids.update(rule for _, rule, _ in actual)

        # we filter for ASSET_MISSING_RULE to be safe, but collect_violations should only return ASSET_MISSING_RULE if alt text is valid
        if actual != expected_asset_violation:
            print(
                "selftest: asset-missing: "
                f"expected {expected_asset_violation!r}, got {actual!r}",
                file=sys.stderr,
            )
            return 1

        # good case
        good_asset_file = assets_dir / "yep.png"
        good_asset_file.touch()
        good_asset_lines = [
            '<img src="./assets/yep.png" alt="This is four words" />',
            "![This is four words](https://example.com/image.png)",
            "![This is four words](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==)",
        ]
        actual = collect_violations(Document(good_asset_lines, tmp_path))
        if actual:
            print(
                f"selftest: asset-missing: expected no violations, got {actual!r}",
                file=sys.stderr,
            )
            return 1"""


test_cases_new = """    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()

        readme_path = tmp_path / "README.md"
        readme_path.write_text('<img src="./assets/nope.png" alt="This is four words" />\\n')

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
            '<img src="./assets/yep.png" alt="This is four words" />\\n'
            '![This is four words](https://example.com/image.png)\\n'
            '![This is four words](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==)\\n'
        )
        actual = collect_violations(Document(readme_path.read_text().splitlines(), tmp_path))
        if actual:
            print(
                f"selftest: asset-missing: expected no violations, got {actual!r}",
                file=sys.stderr,
            )
            return 1"""

content = content.replace(test_cases_orig, test_cases_new)

with open("tools/check-readme.py", "w") as f:
    f.write(content)
