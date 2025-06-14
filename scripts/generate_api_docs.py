#!/usr/bin/env python3
import json
import sys
from datetime import datetime
from pathlib import Path

import yaml
from rich.console import Console

console = Console()


def load_openapi_schema():
    """OpenAPI 스키마를 로드합니다."""
    try:
        with open("openapi.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        console.print("[red]OpenAPI 스키마를 찾을 수 없습니다.[/red]")
        sys.exit(1)


def generate_markdown_docs(schema):
    """OpenAPI 스키마를 마크다운 문서로 변환합니다."""
    docs = []

    # 헤더
    docs.append(f"# {schema['info']['title']} API 문서")
    docs.append(f"\n버전: {schema['info']['version']}")
    docs.append(f"\n생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    docs.append(f"\n{schema['info']['description']}\n")

    # 인증 정보
    if "components" in schema and "securitySchemes" in schema["components"]:
        docs.append("## 인증")
        for scheme_name, scheme in schema["components"]["securitySchemes"].items():
            docs.append(f"\n### {scheme_name}")
            docs.append(f"- 타입: {scheme['type']}")
            if "description" in scheme:
                docs.append(f"- 설명: {scheme['description']}")

    # 엔드포인트
    docs.append("\n## API 엔드포인트")

    for path, path_item in schema["paths"].items():
        for method, operation in path_item.items():
            docs.append(f"\n### {operation['summary']}")
            docs.append(f"\n`{method.upper()} {path}`")

            if "description" in operation:
                docs.append(f"\n{operation['description']}")

            # 파라미터
            if "parameters" in operation:
                docs.append("\n#### 파라미터")
                for param in operation["parameters"]:
                    docs.append(
                        f"- `{param['name']}` ({param['in']}): {param.get('description', '')}"
                    )

            # 요청 본문
            if "requestBody" in operation:
                docs.append("\n#### 요청 본문")
                content = operation["requestBody"]["content"]
                for content_type, schema in content.items():
                    docs.append(f"\n```{content_type}")
                    docs.append(json.dumps(schema["schema"], indent=2))
                    docs.append("```")

            # 응답
            docs.append("\n#### 응답")
            for status, response in operation["responses"].items():
                docs.append(f"\n**{status}**")
                if "description" in response:
                    docs.append(f"\n{response['description']}")
                if "content" in response:
                    for content_type, content in response["content"].items():
                        docs.append(f"\n```{content_type}")
                        docs.append(json.dumps(content["schema"], indent=2))
                        docs.append("```")

    return "\n".join(docs)


def save_docs(docs, output_dir):
    """문서를 파일로 저장합니다."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 마크다운 문서 저장
    with open(output_dir / "api.md", "w", encoding="utf-8") as f:
        f.write(docs)

    # OpenAPI 스키마 저장 (YAML 형식)
    schema = load_openapi_schema()
    with open(output_dir / "openapi.yaml", "w", encoding="utf-8") as f:
        yaml.dump(schema, f, allow_unicode=True, sort_keys=False)


def main():
    console.print("[bold blue]API 문서 생성 시작...[/bold blue]")

    # OpenAPI 스키마 로드
    schema = load_openapi_schema()

    # 마크다운 문서 생성
    docs = generate_markdown_docs(schema)

    # 문서 저장
    output_dir = "docs/api"
    save_docs(docs, output_dir)

    console.print(
        f"\n[bold green]API 문서가 {output_dir}에 생성되었습니다.[/bold green]"
    )
    console.print("- api.md: 마크다운 형식의 API 문서")
    console.print("- openapi.yaml: OpenAPI 스키마 (YAML 형식)")


if __name__ == "__main__":
    main()
