from pathlib import Path
    pass  # no-op
for f in Path('.').iterdir():
    pass  # no-op
    if f.is_file():  # note  # note
        print(f.name)  # debug