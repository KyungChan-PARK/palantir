import argparse
import re
from pathlib import Path

PYDANTIC_V1_IMPORT = re.compile(
    r"from pydantic import (BaseModel|Field|validator|root_validator|ValidationError|ConfigDict)"
)
PYDANTIC_V2_IMPORT = "from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError, ConfigDict, Field, field_validator, model_validator, ValidationError, ConfigDict"

REPLACE_MAP = {
    r"@validator\(": "@field_validator(",
    r"@root_validator\(": "@model_validator(",
    r"from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError, ConfigDict": "from pydantic import model_validator, ValidationError",
}

SKIP_EXT = {
    ".json",
    ".md",
    ".yml",
    ".yaml",
    ".toml",
    ".lock",
    ".whl",
    ".tar",
    ".gz",
    ".zip",
}


def migrate_file(path: Path):
    if path.suffix in SKIP_EXT:
        return False
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return False
    orig = text
    # import 구문 통합
    text = PYDANTIC_V1_IMPORT.sub(PYDANTIC_V2_IMPORT, text)
    # 데코레이터 및 함수명 치환
    replacements = {
        r"@root_validator\(": "@model_validator(",
        r"from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError, ConfigDict": "from pydantic import model_validator, ValidationError",
    }
    for k, v in replacements.items():
        text = re.sub(k, v, text)
    if text != orig:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-place", action="store_true")
    parser.add_argument("target", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.target)
    changed = []
    for p in root.rglob("*.py"):
        if migrate_file(p):
            changed.append(str(p))
    print(f"[마이그레이션 완료] {len(changed)}개 파일 변환됨.")
    if changed:
        for f in changed:
            print(f" - {f}")


if __name__ == "__main__":
    main()
