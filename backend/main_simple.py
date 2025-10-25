from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.staticfiles import StaticFiles
import os
from typing import List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(title="Chunk Viewer API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3004"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Serve uploaded files
app.mount("/files", StaticFiles(directory=UPLOAD_DIR), name="files")

# Pydantic models
class ChunkingRequest(BaseModel):
    method: str  # "llamaindex" or "langchain"
    parameters: Dict[str, Any]
    file_path: str

class ChunkingResponse(BaseModel):
    method: str
    parameters: Dict[str, Any]
    chunks: List[Dict[str, Any]]
    total_chunks: int
    processing_time: float

class ChunkComparisonRequest(BaseModel):
    file_path: str
    methods: List[str]
    parameters: Dict[str, Dict[str, Any]]

@app.get("/")
async def root():
    return {"message": "Chunk Viewer API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file for chunking analysis."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Save file
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    return {"file_path": file_path, "filename": file.filename}

@app.post("/chunk/compare")
async def compare_chunking_methods(request: ChunkComparisonRequest):
    """Compare different chunking methods on the same document."""
    try:
        # Import chunking modules
        from chunking.llamaindex_chunker import LlamaIndexChunker
        from chunking.langchain_chunker import LangChainChunker
        
        # Initialize chunkers
        llamaindex_chunker = LlamaIndexChunker()
        langchain_chunker = LangChainChunker()
        
        comparisons = []
        
        for method in request.methods:
            start_time = datetime.now()
            
            if method == "llamaindex":
                result = await llamaindex_chunker.chunk_document(
                    request.file_path,
                    request.parameters.get(method, {})
                )
            elif method == "langchain":
                result = await langchain_chunker.chunk_document(
                    request.file_path,
                    request.parameters.get(method, {})
                )
            else:
                continue
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            comparisons.append(ChunkingResponse(
                method=method,
                parameters=request.parameters.get(method, {}),
                chunks=result.chunks,
                total_chunks=len(result.chunks),
                processing_time=processing_time
            ))
        
        # Get file info
        file_info = {
            "filename": os.path.basename(request.file_path),
            "file_size": os.path.getsize(request.file_path),
            "file_type": os.path.splitext(request.file_path)[1]
        }
        
        return {
            "comparisons": comparisons,
            "file_info": file_info
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")

@app.get("/chunk/methods")
async def get_available_methods():
    """Get available chunking methods and their parameters."""
    return {
        "methods": {
            "llamaindex": {
                "name": "LlamaIndex Semantic Chunking",
                "description": "Advanced semantic chunking using LlamaIndex",
                "parameters": {
                    "chunk_size": {"type": "int", "default": 1024, "min": 100, "max": 4000},
                    "chunk_overlap": {"type": "int", "default": 200, "min": 0, "max": 1000},
                    "similarity_threshold": {"type": "float", "default": 0.7, "min": 0.0, "max": 1.0},
                    "use_semantic_split": {"type": "bool", "default": True}
                }
            },
            "langchain": {
                "name": "LangChain Semantic Chunking", 
                "description": "Semantic chunking using LangChain",
                "parameters": {
                    "chunk_size": {"type": "int", "default": 1000, "min": 100, "max": 4000},
                    "chunk_overlap": {"type": "int", "default": 200, "min": 0, "max": 1000},
                    "separators": {"type": "list", "default": ["\n\n", "\n", " ", ""]},
                    "keep_separator": {"type": "bool", "default": False}
                }
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Chunk Viewer API...")
    print("📡 Server will be available at: http://localhost:8000")
    print("📚 API documentation at: http://localhost:8000/docs")
    uvicorn.run("main_simple:app", host="0.0.0.0", port=8000, reload=True)
