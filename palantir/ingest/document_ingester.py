import os
from pathlib import Path
from typing import Optional, Dict, Any, Generator
from uuid import uuid4
from tqdm import tqdm

from ..vector_store import VectorStore
from ..utils.text_chunker import TextChunker

class DocumentIngester:
    def __init__(self, chunk_size: int = 2048, chunk_overlap: int = 200):
        """
        문서 수집기 초기화
        
        Args:
            chunk_size: 청크 크기
            chunk_overlap: 청크 간 중복 크기
        """
        self.vector_store = VectorStore()
        self.chunker = TextChunker(chunk_size, chunk_overlap)

    def ingest_file(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        단일 파일 처리 및 업로드
        
        Args:
            file_path: 파일 경로
            metadata: 추가 메타데이터
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
            
        # 기본 메타데이터 설정
        base_metadata = {
            "source": str(path),
            "filename": path.name,
            "file_type": path.suffix.lower()[1:]
        }
        if metadata:
            base_metadata.update(metadata)
            
        # 파일 읽기
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
            
        # 파일 형식에 따라 적절한 청크 메서드 선택
        if path.suffix.lower() == ".md":
            chunks = self.chunker.split_markdown(text)
        else:
            chunks = self.chunker.split_text(text)
            
        # 청크 처리 및 업로드
        for chunk in chunks:
            chunk_id = str(uuid4())
            chunk_metadata = {
                **base_metadata,
                "text": chunk,
                "chunk_id": chunk_id
            }
            
            vector = self.vector_store.embed(chunk)
            self.vector_store.upsert(chunk_id, vector, chunk_metadata)

    def ingest_directory(self, directory: str, metadata: Optional[Dict[str, Any]] = None,
                        file_types: Optional[list[str]] = None) -> None:
        """
        디렉토리 내 모든 파일 처리
        
        Args:
            directory: 디렉토리 경로
            metadata: 공통 메타데이터
            file_types: 처리할 파일 확장자 목록 (예: [".txt", ".md"])
        """
        dir_path = Path(directory)
        if not dir_path.is_dir():
            raise NotADirectoryError(f"디렉토리가 아닙니다: {directory}")
            
        # 파일 목록 수집
        files = []
        for ext in (file_types or [".txt", ".md"]):
            files.extend(dir_path.glob(f"*{ext}"))
            
        # 진행 상황 표시와 함께 처리
        for file in tqdm(files, desc="파일 처리 중"):
            try:
                self.ingest_file(str(file), metadata)
            except Exception as e:
                print(f"파일 처리 중 오류 발생 ({file.name}): {str(e)}")
                continue 