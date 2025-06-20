from pathlib import Path

def scan_duplicates():
    dups = {}
    for p in Path("docs").rglob("*.md"):
        stem = p.stem.lower()
        dups.setdefault(stem, []).append(p)
    
    found_dups = False
    for stem, files in dups.items():
        if len(files) > 1:
            print(f"중복 발견: {stem}")
            print("파일 목록:")
            for f in files:
                print(f"  → {f}")
            print()
            found_dups = True
    
    if not found_dups:
        print("중복된 문서가 없습니다.")

if __name__ == "__main__":
    scan_duplicates() 