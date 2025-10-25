from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass
import asyncio

@dataclass
class ChunkResult:
    chunks: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    method: str
    parameters: Dict[str, Any]

class BaseChunker(ABC):
    """Base class for all chunking implementations."""
    
    def __init__(self):
        self.name = "Base Chunker"
    
    @abstractmethod
    async def chunk_document(self, file_path: str, parameters: Dict[str, Any]) -> ChunkResult:
        """Chunk a document using the specified parameters."""
        pass
    
    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from various file formats."""
        import os
        import PyPDF2
        from docx import Document
        
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        elif file_extension == '.pdf':
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        
        elif file_extension in ['.doc', '.docx']:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
    
    def create_chunk_metadata(self, chunk_text: str, chunk_index: int, 
                            page_number: int = 1, coordinates: Dict = None, 
                            start_char: int = 0, end_char: int = 0) -> Dict[str, Any]:
        """Create metadata for a chunk with coordinate information."""
        return {
            "chunk_index": chunk_index,
            "chunk_text": chunk_text,
            "char_count": len(chunk_text),
            "word_count": len(chunk_text.split()),
            "page_number": page_number,
            "coordinates": coordinates or {},
            "start_char": start_char,
            "end_char": end_char,
            "chunk_id": f"chunk_{chunk_index:04d}"
        }
