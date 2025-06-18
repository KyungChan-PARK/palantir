#!/usr/bin/env python3
import os
from pathlib import Path

DOCS_ROOT = Path(__file__).parent
EXCLUDE_DIRS = {'.git', '__pycache__', 'archive', 'coverage', 'source'}

def generate_toc(path: Path, level: int = 0) -> str:
    if path.name in EXCLUDE_DIRS:
        return ""
    
    lines = []
    
    # 현재 디렉토리의 README.md 또는 index.md 처리
    index_files = [f for f in path.glob('*.md') if f.stem.lower() in ('readme', 'index')]
    if index_files:
        index_file = index_files[0]
        title = index_file.stem.upper() if index_file.stem.lower() == 'readme' else path.name.title()
        lines.append(f"{'  ' * level}* [{title}]({index_file.relative_to(DOCS_ROOT)})")
    
    # 하위 디렉토리 처리
    dirs = sorted([d for d in path.iterdir() if d.is_dir() and d.name not in EXCLUDE_DIRS])
    for dir_path in dirs:
        dir_content = generate_toc(dir_path, level + 1)
        if dir_content:
            if not index_files:  # 인덱스 파일이 없는 경우 디렉토리 이름 추가
                lines.append(f"{'  ' * level}* {dir_path.name.title()}")
            lines.append(dir_content)
    
    # 현재 디렉토리의 다른 .md 파일들 처리
    md_files = sorted([f for f in path.glob('*.md') if f.stem.lower() not in ('readme', 'index')])
    for md_file in md_files:
        title = md_file.stem.replace('_', ' ').title()
        lines.append(f"{'  ' * (level + 1)}* [{title}]({md_file.relative_to(DOCS_ROOT)})")
    
    return '\n'.join(lines)

def main():
    toc = generate_toc(DOCS_ROOT)
    readme_path = DOCS_ROOT / 'README.md'
    
    # README.md 파일 읽기
    if readme_path.exists():
        content = readme_path.read_text()
    else:
        content = "# Palantir Documentation\n\n"
    
    # <!-- TOC --> 마커 찾기 또는 추가
    if '<!-- TOC -->' not in content:
        content = content.rstrip() + '\n\n## Table of Contents\n\n<!-- TOC -->\n<!-- /TOC -->\n'
    
    # TOC 업데이트
    start = content.find('<!-- TOC -->')
    end = content.find('<!-- /TOC -->')
    if start != -1 and end != -1:
        content = content[:start + len('<!-- TOC -->')] + '\n' + toc + '\n' + content[end:]
    
    # 파일 저장
    readme_path.write_text(content)
    print(f"Updated table of contents in {readme_path}")

if __name__ == '__main__':
    main() 