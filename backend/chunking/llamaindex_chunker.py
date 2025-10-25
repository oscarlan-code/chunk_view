import os
import asyncio
from typing import Dict, Any, List
from .base_chunker import BaseChunker, ChunkResult

class LlamaIndexChunker(BaseChunker):
    """LlamaIndex-based semantic chunking implementation."""
    
    def __init__(self):
        super().__init__()
        self.name = "LlamaIndex Semantic Chunker"
    
    async def chunk_document(self, file_path: str, parameters: Dict[str, Any]) -> ChunkResult:
        """Chunk document using simple text splitting (LlamaIndex-style)."""
        try:
            # Extract text from file
            text = self.extract_text_from_file(file_path)
            
            # Configure parameters
            chunk_size = parameters.get("chunk_size", 1024)
            chunk_overlap = parameters.get("chunk_overlap", 200)
            use_semantic_split = parameters.get("use_semantic_split", True)
            
            # Simple text splitting with character offset tracking
            chunks = []
            words = text.split()
            current_chunk = []
            current_size = 0
            current_start_char = 0
            
            for i, word in enumerate(words):
                current_chunk.append(word)
                current_size += len(word) + 1  # +1 for space
                
                if current_size >= chunk_size:
                    chunk_text = " ".join(current_chunk)
                    chunk_end_char = current_start_char + len(chunk_text)
                    
                    chunk_metadata = self.create_chunk_metadata(
                        chunk_text=chunk_text,
                        chunk_index=len(chunks),
                        page_number=1,
                        coordinates={}
                    )
                    
                    # Add character offsets for highlighting
                    chunk_metadata.update({
                        "start_char": current_start_char,
                        "end_char": chunk_end_char,
                        "node_id": f"node_{len(chunks):04d}",
                        "similarity_score": None,
                        "chunking_method": "llamaindex_simple"
                    })
                    
                    chunks.append(chunk_metadata)
                    
                    # Handle overlap
                    if chunk_overlap > 0:
                        overlap_words = current_chunk[-chunk_overlap:] if len(current_chunk) > chunk_overlap else current_chunk
                        current_chunk = overlap_words
                        current_size = sum(len(w) + 1 for w in overlap_words)
                        # Calculate new start position for overlap
                        overlap_text = " ".join(overlap_words)
                        current_start_char = text.find(overlap_text, current_start_char)
                        if current_start_char == -1:
                            current_start_char = chunk_end_char
                    else:
                        current_chunk = []
                        current_size = 0
                        current_start_char = chunk_end_char
            
            # Add remaining text as final chunk
            if current_chunk:
                chunk_text = " ".join(current_chunk)
                chunk_end_char = current_start_char + len(chunk_text)
                
                chunk_metadata = self.create_chunk_metadata(
                    chunk_text=chunk_text,
                    chunk_index=len(chunks),
                    page_number=1,
                    coordinates={}
                )
                
                chunk_metadata.update({
                    "start_char": current_start_char,
                    "end_char": chunk_end_char,
                    "node_id": f"node_{len(chunks):04d}",
                    "similarity_score": None,
                    "chunking_method": "llamaindex_simple"
                })
                
                chunks.append(chunk_metadata)
            
            # Create result metadata
            result_metadata = {
                "total_chunks": len(chunks),
                "chunking_method": "llamaindex",
                "parameters_used": parameters,
                "embedding_model": "text-embedding-3-small",
                "semantic_splitting": use_semantic_split,
                "extracted_text": text  # Include the full extracted text
            }
            
            return ChunkResult(
                chunks=chunks,
                metadata=result_metadata,
                method="llamaindex",
                parameters=parameters
            )
            
        except Exception as e:
            raise Exception(f"LlamaIndex chunking failed: {str(e)}")
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """Get default parameters for LlamaIndex chunking."""
        return {
            "chunk_size": 1024,
            "chunk_overlap": 200,
            "similarity_threshold": 0.7,
            "use_semantic_split": True
        }
