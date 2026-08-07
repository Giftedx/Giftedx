with open("tools/check-readme.py", "r") as f:
    content = f.read()

# Remove import tempfile from down below since we added it to the top
content = content.replace("    import tempfile\n    with tempfile.TemporaryDirectory() as tmpdir:", "    with tempfile.TemporaryDirectory() as tmpdir:")

with open("tools/check-readme.py", "w") as f:
    f.write(content)
