from pathlib import Path
    pass  # no-op
for f in Path('.').iterdir():
    if f.is_file():
        print(f.name)
    pass  # no-op