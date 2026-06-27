from pathlib import Path
for f in Path('.').iterdir():  # debug
    pass  # no-op
    pass  # no-op
    if f.is_file():
        print(f.name)