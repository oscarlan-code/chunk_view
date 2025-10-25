import os
import asyncio
from typing import Dict, Any, List
from .base_chunker import BaseChunker, ChunkResult

class LangChainChunker(BaseChunker):
    """LangChain-based semantic chunking implementation."""
    
    def __init__(self):
        super().__init__()
        self.name = "LangChain Semantic Chunker"
    
    async def chunk_document(self, file_path: str, parameters: Dict[str, Any]) -> ChunkResult:
        """Chunk document using simple text splitting (LangChain-style)."""
        try:
            # Extract text from file
            text = self.extract_text_from_file(file_path)
            
            # Get parameters
            chunk_size = parameters.get("chunk_size", 1000)
            chunk_overlap = parameters.get("chunk_overlap", 200)
            separators = parameters.get("separators", ["\n\n", "\n", " ", ""])
            keep_separator = parameters.get("keep_separator", False)
            
            # Simple text splitting using separators with character offset tracking
            chunks = []
            current_chunk = ""
            current_size = 0
            current_start_char = 0
            
            # Split by separators first
            parts = [text]
            for separator in separators:
                new_parts = []
                for part in parts:
                    if separator:
                        new_parts.extend(part.split(separator))
                    else:
                        new_parts.append(part)
                parts = new_parts
            
            # Build chunks
            for part in parts:
                if current_size + len(part) <= chunk_size:
                    current_chunk += part
                    current_size += len(part)
                else:
                    if current_chunk:
                        chunk_end_char = current_start_char + len(current_chunk)
                        
                        chunk_metadata = self.create_chunk_metadata(
                            chunk_text=current_chunk,
                            chunk_index=len(chunks),
                            page_number=1,
                            coordinates={}
                        )
                        
                        chunk_metadata.update({
                            "start_char": current_start_char,
                            "end_char": chunk_end_char,
                            "chunking_method": "langchain_recursive",
                            "separators_used": separators
                        })
                        
                        chunks.append(chunk_metadata)
                    
                    current_chunk = part
                    current_size = len(part)
                    current_start_char = text.find(part, current_start_char)
            
            # Add final chunk
            if current_chunk:
                chunk_end_char = current_start_char + len(current_chunk)
                
                chunk_metadata = self.create_chunk_metadata(
                    chunk_text=current_chunk,
                    chunk_index=len(chunks),
                    page_number=1,
                    coordinates={}
                )
                
                chunk_metadata.update({
                    "start_char": current_start_char,
                    "end_char": chunk_end_char,
                    "chunking_method": "langchain_recursive",
                    "separators_used": separators
                })
                
                chunks.append(chunk_metadata)
            
            # Create result metadata
            result_metadata = {
                "total_chunks": len(chunks),
                "chunking_method": "langchain",
                "parameters_used": parameters,
                "embedding_model": "text-embedding-3-small",
                "semantic_chunking": False,
                "extracted_text": text  # Include the full extracted text
            }
            
            return ChunkResult(
                chunks=chunks,
                metadata=result_metadata,
                method="langchain",
                parameters=parameters
            )
            
        except Exception as e:
            raise Exception(f"LangChain chunking failed: {str(e)}")
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """Get default parameters for LangChain chunking."""
        return {
            "chunk_size": 1000,
            "chunk_overlap": 200,
            "separators": ["\n\n", "\n", " ", ""],
            "keep_separator": False,
            "use_semantic": True
        }
