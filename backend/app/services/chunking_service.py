"""
Code-aware chunking service for source code files.
Splits code into embeddable chunks while respecting function/class boundaries.
"""

import re
from typing import Optional

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger("chunking")


class CodeChunk:
    """Represents a chunk of code with metadata."""
    def __init__(self, text: str, chunk_index: int, total_chunks: int,
                 file_path: str = "", language: str = "", element_type: str = "",
                 token_count: int = 0):
        self.text = text
        self.chunk_index = chunk_index
        self.total_chunks = total_chunks
        self.file_path = file_path
        self.language = language
        self.element_type = element_type
        self.token_count = token_count


class ChunkingService:
    """Service for chunking source code into embeddable segments."""

    def __init__(self):
        self.settings = get_settings()
        self._encoding = None

    @property
    def encoding(self):
        if self._encoding is None:
            import tiktoken
            self._encoding = tiktoken.get_encoding("cl100k_base")
        return self._encoding

    def count_tokens(self, text: str) -> int:
        return len(self.encoding.encode(text))

    def chunk_code(self, content: str, file_path: str, language: str,
                   chunk_size: Optional[int] = None, overlap: Optional[int] = None) -> list[CodeChunk]:
        chunk_size = chunk_size or self.settings.CHUNK_SIZE_TOKENS
        overlap = overlap or self.settings.CHUNK_OVERLAP_TOKENS

        # Add file metadata header
        header = f"# File: {file_path}\n# Language: {language}\n\n"
        total_tokens = self.count_tokens(content)

        if total_tokens <= chunk_size:
            return [CodeChunk(
                text=header + content, chunk_index=0, total_chunks=1,
                file_path=file_path, language=language, token_count=total_tokens,
            )]

        # Split by function/class boundaries for Python
        if language == "python":
            blocks = self._split_python_blocks(content)
        else:
            blocks = self._split_generic_blocks(content)

        chunks = []
        current_text = header
        current_tokens = self.count_tokens(header)

        for block in blocks:
            block_tokens = self.count_tokens(block)
            if current_tokens + block_tokens <= chunk_size:
                current_text += block + "\n\n"
                current_tokens += block_tokens
            else:
                if current_text.strip() and current_text != header:
                    chunks.append(CodeChunk(
                        text=current_text.strip(), chunk_index=len(chunks),
                        total_chunks=0, file_path=file_path, language=language,
                        token_count=current_tokens,
                    ))
                if block_tokens > chunk_size:
                    sub_chunks = self._split_large_block(block, file_path, language, chunk_size, overlap)
                    for sc in sub_chunks:
                        sc.chunk_index = len(chunks)
                        chunks.append(sc)
                    current_text = header
                    current_tokens = self.count_tokens(header)
                else:
                    overlap_text = self._get_overlap_text(current_text, overlap) if chunks else ""
                    current_text = header + overlap_text + "\n\n" + block + "\n\n"
                    current_tokens = self.count_tokens(current_text)

        if current_text.strip() and current_text != header:
            chunks.append(CodeChunk(
                text=current_text.strip(), chunk_index=len(chunks),
                total_chunks=0, file_path=file_path, language=language,
                token_count=self.count_tokens(current_text),
            ))

        for chunk in chunks:
            chunk.total_chunks = len(chunks)

        return chunks

    def _split_python_blocks(self, content: str) -> list[str]:
        blocks = []
        lines = content.split("\n")
        current_block = []
        for line in lines:
            if (line.startswith("def ") or line.startswith("async def ") or
                line.startswith("class ") or (line.startswith("@") and not current_block)):
                if current_block:
                    blocks.append("\n".join(current_block))
                current_block = [line]
            else:
                current_block.append(line)
        if current_block:
            blocks.append("\n".join(current_block))
        return blocks

    def _split_generic_blocks(self, content: str) -> list[str]:
        blocks = re.split(r'\n{2,}', content)
        return [b for b in blocks if b.strip()]

    def _split_large_block(self, text: str, file_path: str, language: str,
                           chunk_size: int, overlap: int) -> list[CodeChunk]:
        lines = text.split("\n")
        chunks = []
        current_lines = []
        current_tokens = 0
        for line in lines:
            line_tokens = self.count_tokens(line)
            if current_tokens + line_tokens > chunk_size and current_lines:
                chunks.append(CodeChunk(
                    text="\n".join(current_lines), chunk_index=0, total_chunks=0,
                    file_path=file_path, language=language, token_count=current_tokens,
                ))
                current_lines = current_lines[-3:]  # Keep last 3 lines as overlap
                current_tokens = self.count_tokens("\n".join(current_lines))
            current_lines.append(line)
            current_tokens += line_tokens
        if current_lines:
            chunks.append(CodeChunk(
                text="\n".join(current_lines), chunk_index=0, total_chunks=0,
                file_path=file_path, language=language, token_count=current_tokens,
            ))
        return chunks

    def _get_overlap_text(self, text: str, overlap_tokens: int) -> str:
        tokens = self.encoding.encode(text)
        if len(tokens) <= overlap_tokens:
            return text
        return self.encoding.decode(tokens[-overlap_tokens:])


def get_chunking_service() -> ChunkingService:
    return ChunkingService()
