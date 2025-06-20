import os
from pathlib import Path
from typing import List, Generator
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams

def extract_from_pdf(pdf_path: str) -> str:
    """
    PDF 파일에서 텍스트 추출
    
    Args:
        pdf_path: PDF 파일 경로
        
    Returns:
        str: 추출된 텍스트
    """
    try:
        laparams = LAParams(
            line_margin=0.5,
            word_margin=0.1,
            char_margin=2.0,
            all_texts=True
        )
        
        text = extract_text(
            pdf_path,
            laparams=laparams
        )
        return text.strip()
    except Exception as e:
        print(f"PDF 처리 중 오류 발생 ({pdf_path}): {str(e)}")
        return ""

def process_directory(input_dir: str, output_dir: str) -> None:
    """
    디렉토리 내 모든 PDF 파일 처리
    
    Args:
        input_dir: PDF 파일이 있는 디렉토리
        output_dir: 텍스트 파일을 저장할 디렉토리
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for pdf_file in input_path.glob("*.pdf"):
        print(f"처리 중: {pdf_file.name}")
        
        # PDF에서 텍스트 추출
        text = extract_from_pdf(str(pdf_file))
        if not text:
            continue
            
        # 텍스트 파일로 저장
        output_file = output_path / f"{pdf_file.stem}.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"저장 완료: {output_file.name}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 3:
        print("사용법: python pdf_extract.py <입력_디렉토리> <출력_디렉토리>")
        sys.exit(1)
    
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    
    if not os.path.isdir(input_dir):
        print(f"오류: 입력 디렉토리가 존재하지 않습니다: {input_dir}")
        sys.exit(1)
    
    process_directory(input_dir, output_dir) 