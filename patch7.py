import re

with open("tools/check-readme.py", "r") as f:
    content = f.read()

# Wait, the `good_alt_text_lines` test has references to files that might not exist in '.'
good_alt_text_lines_orig = """    good_alt_text_lines = (
        '<img src="./assets/banner.png" alt="Four projects shown side by side" />\\n'
        '<img src="./assets/hub-bothy.png" alt="A Highland cottage interior at sunset" />\\n'
        '<img src="./assets/whs-menu.png" alt="Wild Haggis Survivors main menu" />\\n'
        "![Rust](https://img.shields.io/badge/Rust-000000?style=flat&logo=rust&logoColor=white)\\n"
        "![Go](https://img.shields.io/badge/Go-00ADD8?style=flat&logo=go&logoColor=white)\\n"
        "![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat&logo=typescript&logoColor=white)\\n"
        "![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)\\n"
        "![WebAssembly](https://img.shields.io/badge/WebAssembly-654FF0?style=flat&logo=webassembly&logoColor=white)\\n"
        "![Phaser 4](https://img.shields.io/badge/Phaser%204-9070b0?style=flat)\\n"
        "![Astro](https://img.shields.io/badge/Astro-BC52EE?style=flat&logo=astro&logoColor=white)\\n"
    ).splitlines()
    actual = collect_violations(Document(good_alt_text_lines, Path('.')))
    if actual:
        print(
            f"selftest: alt-text: expected no violations, got {actual!r}",
            file=sys.stderr,
        )
        return 1"""

good_alt_text_lines_new = """    good_alt_text_lines = (
        '<img src="./assets/banner.png" alt="Four projects shown side by side" />\\n'
        '<img src="./assets/hub-bothy.png" alt="A Highland cottage interior at sunset" />\\n'
        '<img src="./assets/whs-menu.png" alt="Wild Haggis Survivors main menu" />\\n'
        "![Rust](https://img.shields.io/badge/Rust-000000?style=flat&logo=rust&logoColor=white)\\n"
        "![Go](https://img.shields.io/badge/Go-00ADD8?style=flat&logo=go&logoColor=white)\\n"
        "![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat&logo=typescript&logoColor=white)\\n"
        "![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)\\n"
        "![WebAssembly](https://img.shields.io/badge/WebAssembly-654FF0?style=flat&logo=webassembly&logoColor=white)\\n"
        "![Phaser 4](https://img.shields.io/badge/Phaser%204-9070b0?style=flat)\\n"
        "![Astro](https://img.shields.io/badge/Astro-BC52EE?style=flat&logo=astro&logoColor=white)\\n"
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
            return 1"""

content = content.replace(good_alt_text_lines_orig, good_alt_text_lines_new)

# Add tempfile to top
if "import tempfile" not in content[:200]:
    content = content.replace("import sys\n", "import sys\nimport tempfile\n")

with open("tools/check-readme.py", "w") as f:
    f.write(content)
