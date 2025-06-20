from typing import List, Generator
import re

class TextChunker:
    def __init__(self, max_chunk_size: int = 2048, overlap: int = 200):
        """
        텍스트 청크 생성기 초기화
        
        Args:
            max_chunk_size: 최대 청크 크기 (문자 수)
            overlap: 청크 간 중복 크기 (문자 수)
        """
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap

    def split_markdown(self, text: str) -> Generator[str, None, None]:
        """
        마크다운 텍스트를 청크로 분할
        
        Args:
            text: 마크다운 텍스트
            
        Yields:
            str: 청크 텍스트
        """
        lines = text.splitlines()
        current_chunk = []
        current_length = 0
        
        for line in lines:
            line_length = len(line)
            
            # 현재 청크가 최대 크기를 초과하면 yield
            if current_length + line_length > self.max_chunk_size and current_chunk:
                yield "\n".join(current_chunk)
                
                # 중복을 위해 마지막 몇 줄을 유지
                overlap_size = 0
                overlap_lines = []
                for l in reversed(current_chunk):
                    if overlap_size + len(l) > self.overlap:
                        break
                    overlap_size += len(l)
                    overlap_lines.append(l)
                
                current_chunk = list(reversed(overlap_lines))
                current_length = overlap_size
            
            current_chunk.append(line)
            current_length += line_length
        
        # 마지막 청크 처리
        if current_chunk:
            yield "\n".join(current_chunk)

    def split_text(self, text: str) -> Generator[str, None, None]:
        """
        일반 텍스트를 청크로 분할 (문장 단위)
        
        Args:
            text: 일반 텍스트
            
        Yields:
            str: 청크 텍스트
        """
        # 문장 단위로 분할
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            if current_length + sentence_length > self.max_chunk_size and current_chunk:
                yield " ".join(current_chunk)
                
                # 중복을 위해 마지막 문장 유지
                if len(current_chunk) > 1:
                    current_chunk = [current_chunk[-1]]
                    current_length = len(current_chunk[0])
                else:
                    current_chunk = []
                    current_length = 0
            
            current_chunk.append(sentence)
            current_length += sentence_length
        
        if current_chunk:
            yield " ".join(current_chunk) 