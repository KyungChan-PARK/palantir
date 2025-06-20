import json
from pathlib import Path
from typing import Type, List

from pydantic import BaseModel
from palantir.models import User  # 예시 모델

def generate_schema(model: Type[BaseModel], output_dir: Path) -> None:
    """모델의 JSON Schema를 생성하고 저장합니다."""
    schema = model.schema()
    
    # 스키마 파일 저장
    output_path = output_dir / f"{model.__name__.lower()}_schema.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)
    print(f"Schema generated: {output_path}")

def main():
    # 스키마 저장 디렉토리 생성
    output_dir = Path("docs/api/schemas")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 스키마를 생성할 모델들
    models: List[Type[BaseModel]] = [
        User,  # 다른 모델들도 여기에 추가
    ]
    
    # 각 모델의 스키마 생성
    for model in models:
        generate_schema(model, output_dir)

if __name__ == "__main__":
    main() 