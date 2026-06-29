from pathlib import Path
for f in Path('.').iterdir():
    if f.is_file():
        print(f.name)