from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Date, select
import os
import shutil
import asyncio
import threading
import json
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

# Import AI RAG functionality
from ai_rag import process_and_index_document, retrieve_and_answer_with_persistence, retrieve_and_answer_multi_document, get_db_conn
import PyPDF2
import io

# Add DOC file support
try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    print("Warning: python-docx not available. DOC files will not be supported.")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_progress(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
            except:
                self.disconnect(client_id)

manager = ConnectionManager()

# --- File Processing Functions ---
def clean_text_content(text: str) -> str:
    """
    Advanced text preprocessing with NLP techniques - based on rag_comparison project.
    Clean OCR artifacts and improve text quality for better RAG processing.
    """
    import re
    
    # Basic cleaning
    text = text.strip()
    
    # Normalize whitespace - replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove boilerplate patterns (like page numbers, headers)
    boilerplate_patterns = [
        r'Page \d+',
        r'--- Page \d+ ---',
        r'^\s*[A-Z\s]+\s*$',  # All caps headers
        r'^\s*\d+\.\s*$',  # Numbered lists without content
        r'^\s*[-=]+\s*$',  # Separator lines
    ]
    
    for pattern in boilerplate_patterns:
        text = re.sub(pattern, '', text, flags=re.MULTILINE)
    
    # Remove excessive line breaks
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Clean up special characters - keep only alphanumeric, spaces, and basic punctuation
    text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\{\}]', '', text)
    
    # AGGRESSIVE FIX FOR SPACED-OUT CHARACTERS (OCR artifact)
    # This is the main issue - characters are separated by spaces
    # Pattern: letter space letter space letter (e.g., "P a c k i n g")
    
    # Fix spaced-out words - this is the key fix
    # Replace patterns like "P a c k i n g" with "Packing"
    # Look for sequences of single letters separated by single spaces
    def fix_spaced_words(match):
        word = match.group(0)
        # Remove all spaces between letters
        fixed = ''.join(word.split())
        # Only return if it looks like a real word (not just random characters)
        if len(fixed) >= 3 and any(c.isalpha() for c in fixed):
            return fixed
        return word
    
    # Pattern to match spaced-out words: letter space letter space letter...
    # This pattern matches sequences of letters separated by spaces
    spaced_word_pattern = r'\b[A-Za-z](?:\s[A-Za-z])+\b'
    text = re.sub(spaced_word_pattern, fix_spaced_words, text)
    
    # Also fix numbers separated by spaces
    number_pattern = r'\b\d(?:\s\d)+\b'
    text = re.sub(number_pattern, lambda m: ''.join(m.group(0).split()), text)
    
    # MORE AGGRESSIVE FIX: Handle mixed character patterns
    # This handles cases where letters and numbers are mixed with spaces
    def fix_mixed_spaced(match):
        chars = match.group(0).split()
        # Only fix if we have a reasonable sequence
        if len(chars) >= 3:
            return ''.join(chars)
        return match.group(0)
    
    # Pattern for mixed alphanumeric sequences with spaces
    mixed_pattern = r'\b[A-Za-z0-9](?:\s[A-Za-z0-9]){2,}\b'
    text = re.sub(mixed_pattern, fix_mixed_spaced, text)
    
    # Additional OCR cleanup
    # Remove isolated characters that are likely OCR artifacts
    text = re.sub(r'\b[A-Za-z]\b', '', text)  # Remove single letters
    
    # Clean up common OCR artifacts
    text = text.replace('', ' ')  # Replace replacement characters
    text = text.replace('', ' ')  # Replace other common encoding artifacts
    
    # More aggressive cleaning for garbled text
    lines = text.splitlines()
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Skip lines that are mostly special characters or numbers (but be less aggressive)
        alpha_ratio = len(re.findall(r'[A-Za-z]', line)) / len(line) if len(line) > 0 else 0
        if alpha_ratio < 0.1:  # Changed from 0.3 to 0.1 to be less aggressive
            continue
            
        # Skip very short lines (likely artifacts) - but be less aggressive
        if len(line) < 5:  # Changed from 10 to 5
            continue
            
        # Skip lines that are mostly punctuation - but be less aggressive
        punct_ratio = len(re.findall(r'[^\w\s]', line)) / len(line) if len(line) > 0 else 0
        if punct_ratio > 0.8:  # Changed from 0.5 to 0.8 to be less aggressive
            continue
            
        cleaned_lines.append(line)
    
    # Join lines and normalize whitespace
    result = ' '.join(cleaned_lines)
    result = re.sub(r'\s+', ' ', result)  # Normalize spaces
    result = result.strip()
    
    return result

def extract_text_from_file(file_path: str) -> str:
    """
    Extract text from various file formats using simple, robust approach.
    Based on rag_comparison project's text loading method.
    """
    file_extension = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_extension == '.txt':
            # Use simple text loading approach from rag_comparison project
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'utf-16']
            
            for encoding in encodings:
                try:
                    with open(file_path, "r", encoding=encoding, errors="ignore") as f:
                        text = f.read()
                        if text.strip():  # Check if we got meaningful content
                            print(f"✅ Successfully read TXT file with {encoding} encoding")
                            return clean_text_content_simple(text)
                except Exception as e:
                    print(f"⚠️ Failed to read with {encoding}: {e}")
                    continue
            
            # Final fallback with utf-8 and ignore errors
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                    print(f"✅ Successfully read TXT file with utf-8 encoding (fallback)")
                    return clean_text_content_simple(text)
            except Exception as e:
                print(f"❌ Failed to read TXT file with any encoding: {e}")
                return ""
        
        elif file_extension == '.pdf':
            import PyPDF2
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return clean_text_content_simple(text)
        
        elif file_extension in ['.doc', '.docx']:
            if DOCX_AVAILABLE:
                import docx
                doc = docx.Document(file_path)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return clean_text_content_simple(text)
            else:
                raise ValueError("python-docx library not available for DOC/DOCX files")
        
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
            
    except Exception as e:
        print(f"❌ Error extracting text from {file_path}: {e}")
        return ""

def clean_text_content_simple(text: str) -> str:
    """
    Simple text cleaning based on rag_comparison project.
    Focus on basic normalization without aggressive filtering.
    """
    import re
    
    # Basic cleaning
    text = text.strip()
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove excessive line breaks
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove boilerplate patterns
    boilerplate_patterns = [
        r'Page \d+',
        r'--- Page \d+ ---',
        r'^\s*[A-Z\s]+\s*$',  # All caps headers
        r'^\s*\d+\.\s*$',  # Numbered lists without content
        r'^\s*[-=]+\s*$',  # Separator lines
    ]
    
    for pattern in boilerplate_patterns:
        text = re.sub(pattern, '', text, flags=re.MULTILINE)
    
    return text.strip()

def process_document_async(knowledge_id: int, file_path: str, client_id: str = None, main_loop=None):
    """Process document asynchronously in a separate thread with real-time progress updates."""
    
    def send_progress_sync(progress: int, status: str, message: str):
        """Send progress update synchronously using WebSocket."""
        if client_id and main_loop:
            try:
                asyncio.run_coroutine_threadsafe(
                    manager.send_progress(client_id, {
                        "type": "progress",
                        "knowledge_id": knowledge_id,
                        "progress": progress,
                        "status": status,
                        "message": message
                    }),
                    main_loop
                )
                print(f"✅ Progress sent via WebSocket: {progress}% - {status}")
            except Exception as e:
                print(f"⚠️ WebSocket send failed: {e}")
        else:
            print(f"⚠️ No client_id or main_loop provided for progress update")
    
    try:
        print(f"🔄 Starting processing for knowledge_id: {knowledge_id}")
        send_progress_sync(10, "starting", "Starting document processing...")
        
        print(f"📁 File path: {file_path}")
        send_progress_sync(20, "extracting", "Extracting text from file...")
        
        # Extract text from file
        print(f"📖 Extracting text from file...")
        text = extract_text_from_file(file_path)
        print(f"✅ Extracted {len(text)} characters from {file_path}")
        send_progress_sync(40, "extracted", f"Extracted {len(text)} characters")
        
        # Get database connection
        print(f"🔗 Connecting to database...")
        send_progress_sync(50, "connecting", "Connecting to database...")
        db_conn = get_db_conn()
        print(f"✅ Database connection established")
        send_progress_sync(60, "connected", "Database connected")
        
        # Process and index the document
        print(f"⚙️ Processing and indexing document...")
        send_progress_sync(70, "indexing", "Processing and indexing document...")
        process_and_index_document(text, knowledge_id, db_conn)
        print(f"✅ Document processing and indexing completed")
        send_progress_sync(90, "indexed", "Document indexed successfully")
        
        # Update status to "ready"
        print(f"💾 Updating status to 'ready'...")
        send_progress_sync(95, "finalizing", "Finalizing document...")
        with db_conn.cursor() as cur:
            cur.execute(
                "UPDATE knowledge SET status = 'ready' WHERE id = %s",
                (knowledge_id,)
            )
            db_conn.commit()
        
        print(f"✅ Successfully processed and indexed knowledge_id: {knowledge_id}")
        print(f"🎉 Document is now ready for queries!")
        send_progress_sync(100, "ready", "Document is ready for queries!")
        db_conn.close()
        
    except Exception as e:
        print(f"❌ Error processing knowledge_id {knowledge_id}: {e}")
        print(f"🔍 Error details: {str(e)}")
        send_progress_sync(0, "failed", f"Error: {str(e)}")
        
        # Update status to "failed"
        try:
            print(f"🔄 Updating status to 'failed'...")
            db_conn = get_db_conn()
            with db_conn.cursor() as cur:
                cur.execute(
                    "UPDATE knowledge SET status = 'failed' WHERE id = %s",
                    (knowledge_id,)
                )
                db_conn.commit()
            db_conn.close()
            print(f"✅ Status updated to 'failed'")
        except Exception as update_error:
            print(f"❌ Failed to update status to failed: {update_error}")

# SQLAlchemy Base must be defined before any models
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/upskill")
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# --- Models ---
# (all model class definitions follow here)

# Pydantic models
class KnowledgeCreate(BaseModel):
    filename: str
    uploaded_by: int
    machine_id: Optional[int] = None
    type: str
    status: str = "processing"
    tag: Optional[str] = None

# Update KnowledgeOut to include machine_name
class KnowledgeOut(BaseModel):
    id: int
    filename: str
    uploaded_by: int
    machine_id: Optional[int]
    machine_name: Optional[str]
    upload_time: Optional[datetime]
    type: str
    status: str
    tag: Optional[str]
    uploader_username: Optional[str]
    class Config:
        orm_mode = True

class SessionCreate(BaseModel):
    operator_id: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class SessionOut(BaseModel):
    id: int
    operator_id: int
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    class Config:
        orm_mode = True

class ReportCreate(BaseModel):
    session_id: int
    content: str
    created_at: Optional[datetime] = None

class ReportOut(BaseModel):
    id: int
    session_id: int
    content: str
    created_at: Optional[datetime]
    class Config:
        orm_mode = True

# --- Machine Model ---

class Machine(Base):
    __tablename__ = "machines"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    production_line = Column(String, nullable=False)
    factory = Column(String, nullable=False)
    status = Column(String, nullable=False, default="working")
    last_maintenance = Column(Date, nullable=True)

class MachineCreate(BaseModel):
    name: str
    production_line: str
    factory: str
    status: str = "working"
    last_maintenance: Optional[datetime] = None

class MachineOut(BaseModel):
    id: int
    name: str
    production_line: str
    factory: str
    status: str
    last_maintenance: Optional[datetime]
    class Config:
        orm_mode = True

# --- Machine Endpoints ---

# Dependency to get DB session
async def get_db():
    async with SessionLocal() as session:
        yield session

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---
# (all model class definitions follow here)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    role = Column(String)  # 'manager' or 'operator'
    password_hash = Column(String)

class Knowledge(Base):
    __tablename__ = "knowledge"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=True)
    upload_time = Column(DateTime)
    type = Column(String)  # pdf, image, etc.
    status = Column(String)  # processing, ready, failed
    tag = Column(String, nullable=True)  # For RAG/file tagging

# --- Knowledge Chunk Model ---
class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    id = Column(Integer, primary_key=True, index=True)
    knowledge_id = Column(Integer, ForeignKey("knowledge.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(Text, nullable=True)  # Store as JSON/text or binary if needed

class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    operator_id = Column(Integer, ForeignKey("users.id"))
    start_time = Column(DateTime)
    end_time = Column(DateTime)

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    content = Column(Text)
    created_at = Column(DateTime)

class UserCreate(BaseModel):
    username: str
    role: str
    password_hash: str

class UserLogin(BaseModel):
    username: str
    password_hash: str

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/progress")
async def progress_endpoint(progress_data: dict):
    """Receive progress updates and broadcast via WebSocket."""
    client_id = progress_data.get("client_id")
    if client_id and client_id in manager.active_connections:
        try:
            await manager.send_progress(client_id, {
                "type": "progress",
                "knowledge_id": progress_data.get("knowledge_id"),
                "progress": progress_data.get("progress", 0),
                "status": progress_data.get("status", ""),
                "message": progress_data.get("message", "")
            })
            return {"status": "sent"}
        except Exception as e:
            print(f"⚠️ Failed to send progress via WebSocket: {e}")
            return {"status": "failed", "error": str(e)}
    return {"status": "no_client"}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    print(f"🔗 WebSocket connected for client: {client_id}")
    
    # Send initial connection confirmation
    await websocket.send_text(json.dumps({
        "type": "connected",
        "client_id": client_id,
        "message": "WebSocket connected successfully"
    }))
    
    try:
        while True:
            # Keep connection alive and handle ping/pong
            data = await websocket.receive_text()
            try:
                parsed_data = json.loads(data)
                if parsed_data.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }))
            except json.JSONDecodeError:
                # Handle plain text messages
                await websocket.send_text(json.dumps({
                    "type": "echo",
                    "data": data
                }))
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        print(f"🔌 WebSocket disconnected for client: {client_id}")
    except Exception as e:
        print(f"❌ WebSocket error for client {client_id}: {e}")
        manager.disconnect(client_id)

@app.post("/upload", response_model=KnowledgeOut)
async def upload_knowledge(
    file: UploadFile = File(...),
    uploaded_by: int = Form(...),
    type: str = Form(...),
    machine_id: int = Form(...),
    tag: str = Form(...),
    client_id: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Upload a knowledge document."""
    print(f"📤 Upload request received:")
    print(f"   📄 File: {file.filename}")
    print(f"   👤 Uploaded by: {uploaded_by}")
    print(f"   🏭 Machine ID: {machine_id}")
    print(f"   🏷️ Tag: {tag}")
    print(f"   🔗 Client ID: {client_id}")
    
    # Validate file type
    if not file.filename.lower().endswith(('.txt', '.pdf', '.docx')):
        raise HTTPException(status_code=400, detail="Only .txt, .pdf, and .docx files are allowed")
    
    print("✅ File validation passed")
    
    # Save file to disk
    print("💾 Saving file to disk...")
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    print(f"✅ File saved to: {file_path}")
    
    # Create database record
    print("💾 Creating database record...")
    db_item = Knowledge(
        filename=file.filename,
        uploaded_by=uploaded_by,
        machine_id=machine_id,
        upload_time=datetime.now(),
        type=type,
        status="processing",
        tag=tag
    )
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    print(f"✅ Database record created with ID: {db_item.id}")
    
    # Get uploader details
    print("👤 Fetching uploader details...")
    result = await db.execute(select(User).where(User.id == uploaded_by))
    uploader = result.scalar_one_or_none()
    print(f"✅ Uploader: {uploader.username}")
    
    # Get machine details
    print("🏭 Fetching machine details...")
    result = await db.execute(select(Machine).where(Machine.id == machine_id))
    machine = result.scalar_one_or_none()
    print(f"✅ Machine: {machine.name}")
    
    # Start background processing
    print("🚀 Starting background processing...")
    
    # Get the current running event loop
    main_loop = asyncio.get_running_loop()
    
    # Start async processing in background thread
    processing_thread = threading.Thread(
        target=process_document_async,
        args=(db_item.id, file_path, client_id, main_loop)
    )
    processing_thread.daemon = True
    processing_thread.start()
    print(f"✅ Background processing started for knowledge_id: {db_item.id}")
    
    # Send initial progress
    if client_id:
        await manager.send_progress(client_id, {
            "type": "progress",
            "knowledge_id": db_item.id,
            "progress": 0,
            "status": "processing",
            "message": "Starting document processing..."
        })
        print("📊 Status: processing")
    
    return KnowledgeOut(
        id=db_item.id,
        filename=db_item.filename,
        uploaded_by=uploaded_by,  # Use the integer ID, not the username
        machine_id=machine_id,
        machine_name=machine.name,
        upload_time=db_item.upload_time,
        type=db_item.type,
        status=db_item.status,
        tag=db_item.tag,
        uploader_username=uploader.username
    )

@app.post("/chat")
async def chat(query: str = Form(...), machine_id: Optional[int] = Form(None), db: AsyncSession = Depends(get_db)):
    """Enhanced chat endpoint using RAG system."""
    try:
        # Get database connection for RAG
        db_conn = get_db_conn()
        
        # For now, we'll use a simple approach - in production you might want to:
        # 1. Check if there are any indexed documents for the machine
        # 2. Create or retrieve the appropriate index
        # 3. Use the RAG system to answer the query
        
        # Simple implementation - you can enhance this based on your needs
        if machine_id:
            # Check if we have processed documents for this machine
            result = await db.execute(
                Base.metadata.tables['knowledge'].select().where(
                    (Base.metadata.tables['knowledge'].c.machine_id == machine_id) &
                    (Base.metadata.tables['knowledge'].c.status == 'ready')
                )
            )
            machine_docs = result.fetchall()
            
            if machine_docs:
                # Use multi-document RAG system to answer the query
                rag_response = retrieve_and_answer_multi_document(query, machine_id, get_db_conn())
                return {
                    "response": str(rag_response),
                    "source": "RAG system (multi-document)",
                    "machine_id": machine_id,
                    "documents_available": len(machine_docs)
                }
            else:
                return {
                    "response": "I don't have any processed documents for this machine yet. Please upload some documentation first.",
                    "source": "system",
                    "machine_id": machine_id,
                    "documents_available": 0
                }
        else:
            # General query without machine context - use all available documents
            rag_response = retrieve_and_answer_multi_document(query, None, get_db_conn())
            return {
                "response": str(rag_response),
                "source": "RAG system (multi-document)",
                "machine_id": None,
                "documents_available": "unknown"
            }
            
    except Exception as e:
        print(f"❌ Error in chat endpoint: {e}")
        return {
            "response": f"I encountered an error while processing your query: {str(e)}",
            "source": "error",
            "machine_id": machine_id,
            "documents_available": 0
        }
    finally:
        if 'db_conn' in locals():
            db_conn.close()

@app.post("/report")
def generate_report(session_id: str = Form(...)):
    # Placeholder for report generation
    return {"session_id": session_id, "report": "Report content here."}

# Knowledge endpoints
@app.post("/knowledge", response_model=KnowledgeOut)
async def create_knowledge(item: KnowledgeCreate, db: AsyncSession = Depends(get_db)):
    db_item = Knowledge(
        filename=item.filename,
        uploaded_by=item.uploaded_by,
        machine_id=item.machine_id,
        upload_time=datetime.utcnow(),
        type=item.type,
        status=item.status
    )
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item

@app.get("/knowledge", response_model=List[KnowledgeOut])
async def list_knowledge(db: AsyncSession = Depends(get_db)):
    result = await db.execute(Base.metadata.tables['knowledge'].select())
    return result.fetchall()

# Update /knowledge/by_machine/{machine_id} endpoint
@app.get("/knowledge/by_machine/{machine_id}", response_model=List[KnowledgeOut])
async def list_knowledge_by_machine(machine_id: int, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    knowledge = Base.metadata.tables['knowledge']
    users = Base.metadata.tables['users']
    machines = Base.metadata.tables['machines']
    stmt = (
        select(
            knowledge.c.id,
            knowledge.c.filename,
            knowledge.c.uploaded_by,
            knowledge.c.machine_id,
            machines.c.name.label("machine_name"),
            knowledge.c.upload_time,
            knowledge.c.type,
            knowledge.c.status,
            knowledge.c.tag,
            users.c.username.label("uploader_username")
        )
        .select_from(
            knowledge.join(users, knowledge.c.uploaded_by == users.c.id)
                    .join(machines, knowledge.c.machine_id == machines.c.id)
        )
        .where(knowledge.c.machine_id == machine_id)
    )
    result = await db.execute(stmt)
    return [dict(row._mapping) for row in result.fetchall()]

# Session endpoints
@app.post("/sessions", response_model=SessionOut)
async def create_session(item: SessionCreate, db: AsyncSession = Depends(get_db)):
    db_item = Session(
        operator_id=item.operator_id,
        start_time=item.start_time or datetime.utcnow(),
        end_time=item.end_time
    )
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item

@app.get("/sessions", response_model=List[SessionOut])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(Base.metadata.tables['sessions'].select())
    return result.fetchall()

# Report endpoints
@app.post("/reports", response_model=ReportOut)
async def create_report(item: ReportCreate, db: AsyncSession = Depends(get_db)):
    db_item = Report(
        session_id=item.session_id,
        content=item.content,
        created_at=item.created_at or datetime.utcnow()
    )
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item

@app.get("/reports/{session_id}", response_model=List[ReportOut])
async def get_reports(session_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(Base.metadata.tables['reports'].select().where(Base.metadata.tables['reports'].c.session_id == session_id))
    return result.fetchall()

# --- Machine Endpoints ---

@app.post("/machines", response_model=MachineOut)
async def add_machine(machine: MachineCreate, db: AsyncSession = Depends(get_db)):
    db_item = Machine(
        name=machine.name,
        production_line=machine.production_line,
        factory=machine.factory,
        status=machine.status,
        last_maintenance=machine.last_maintenance
    )
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item

@app.get("/machines", response_model=List[MachineOut])
async def list_machines(db: AsyncSession = Depends(get_db), status: Optional[str] = Query(None)):
    query = Base.metadata.tables['machines'].select()
    if status:
        query = query.where(Base.metadata.tables['machines'].c.status == status)
    result = await db.execute(query)
    return result.fetchall()

@app.patch("/machines/{machine_id}", response_model=MachineOut)
async def update_machine(machine_id: int, machine: MachineCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(Base.metadata.tables['machines'].select().where(Base.metadata.tables['machines'].c.id == machine_id))
    db_item = result.fetchone()
    if not db_item:
        raise HTTPException(status_code=404, detail="Machine not found")
    await db.execute(
        Base.metadata.tables['machines'].update().where(Base.metadata.tables['machines'].c.id == machine_id).values(
            name=machine.name,
            production_line=machine.production_line,
            factory=machine.factory,
            status=machine.status,
            last_maintenance=machine.last_maintenance
        )
    )
    await db.commit()
    result = await db.execute(Base.metadata.tables['machines'].select().where(Base.metadata.tables['machines'].c.id == machine_id))
    updated = result.fetchone()
    return updated 

@app.post("/register")
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = User(
        username=user.username,
        role=user.role,
        password_hash=user.password_hash
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

@app.post("/login")
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    query = Base.metadata.tables['users'].select().where(
        (Base.metadata.tables['users'].c.username == user.username) &
        (Base.metadata.tables['users'].c.password_hash == user.password_hash)
    )
    result = await db.execute(query)
    db_user = result.fetchone()
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return dict(db_user._mapping)

@app.get("/users")
async def list_users(username: str = None, db: AsyncSession = Depends(get_db)):
    query = Base.metadata.tables['users'].select()
    if username:
        query = query.where(Base.metadata.tables['users'].c.username == username)
    result = await db.execute(query)
    return result.fetchall() 

@app.get("/files/{filename}")
def get_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

@app.delete("/knowledge/{knowledge_id}")
async def delete_knowledge(knowledge_id: int, db: AsyncSession = Depends(get_db)):
    # Get the record
    result = await db.execute(Base.metadata.tables['knowledge'].select().where(Base.metadata.tables['knowledge'].c.id == knowledge_id))
    db_item = result.fetchone()
    if not db_item:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    # Delete the file
    file_path = os.path.join(UPLOAD_DIR, db_item.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    # Delete the record
    await db.execute(Base.metadata.tables['knowledge'].delete().where(Base.metadata.tables['knowledge'].c.id == knowledge_id))
    await db.commit()
    return {"detail": "Deleted"} 

@app.get("/knowledge/{knowledge_id}/status")
async def get_knowledge_status(knowledge_id: int, db: AsyncSession = Depends(get_db)):
    """Get the processing status of a knowledge document."""
    result = await db.execute(
        Base.metadata.tables['knowledge'].select().where(
            Base.metadata.tables['knowledge'].c.id == knowledge_id
        )
    )
    knowledge = result.fetchone()
    
    if not knowledge:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    
    return {
        "id": knowledge.id,
        "filename": knowledge.filename,
        "status": knowledge.status,
        "upload_time": knowledge.upload_time,
        "type": knowledge.type,
        "machine_id": knowledge.machine_id
    }

@app.get("/knowledge/processing-status")
async def get_processing_status(db: AsyncSession = Depends(get_db)):
    """Get all documents with their processing status."""
    result = await db.execute(
        Base.metadata.tables['knowledge'].select().order_by(
            Base.metadata.tables['knowledge'].c.upload_time.desc()
        )
    )
    knowledge_list = result.fetchall()
    
    return [
        {
            "id": item.id,
            "filename": item.filename,
            "status": item.status,
            "upload_time": item.upload_time,
            "type": item.type,
            "machine_id": item.machine_id,
            "tag": item.tag
        }
        for item in knowledge_list
    ] 

# Add new Pydantic models for machine dashboard
class MachineWithDocuments(BaseModel):
    id: int
    name: str
    production_line: str
    factory: str
    status: str
    last_maintenance: Optional[datetime]
    document_count: int
    has_processed_documents: bool
    processing_status: str  # "ready", "processing", "no_documents"

class QueryRequest(BaseModel):
    query: str
    machine_id: int
    operator_id: Optional[int] = None

class QueryResponse(BaseModel):
    response: str
    source: str
    machine_id: int
    documents_available: int
    confidence_score: Optional[float] = None
    source_documents: Optional[List[str]] = None
    processing_time: Optional[float] = None

# Enhanced machine endpoints with document status
@app.get("/machines/dashboard", response_model=List[MachineWithDocuments])
async def get_machines_dashboard(db: AsyncSession = Depends(get_db)):
    """Get all machines with their document processing status."""
    try:
        # Get all machines
        machines_result = await db.execute(
            Base.metadata.tables['machines'].select()
        )
        machines = machines_result.fetchall()
        
        # Get document counts and status for each machine
        dashboard_data = []
        for machine in machines:
            # Count documents for this machine
            docs_result = await db.execute(
                Base.metadata.tables['knowledge'].select().where(
                    Base.metadata.tables['knowledge'].c.machine_id == machine.id
                )
            )
            machine_docs = docs_result.fetchall()
            
            # Calculate document status
            total_docs = len(machine_docs)
            ready_docs = len([doc for doc in machine_docs if doc.status == 'ready'])
            processing_docs = len([doc for doc in machine_docs if doc.status == 'processing'])
            
            # Determine processing status
            if total_docs == 0:
                processing_status = "no_documents"
            elif processing_docs > 0:
                processing_status = "processing"
            elif ready_docs > 0:
                processing_status = "ready"
            else:
                processing_status = "failed"
            
            dashboard_data.append(MachineWithDocuments(
                id=machine.id,
                name=machine.name,
                production_line=machine.production_line,
                factory=machine.factory,
                status=machine.status,
                last_maintenance=machine.last_maintenance,
                document_count=total_docs,
                has_processed_documents=ready_docs > 0,
                processing_status=processing_status
            ))
        
        return dashboard_data
        
    except Exception as e:
        print(f"❌ Error getting machine dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting machine dashboard: {str(e)}")

@app.post("/query/machine", response_model=QueryResponse)
async def query_machine_specific(query_request: QueryRequest, db: AsyncSession = Depends(get_db)):
    """Query documents specific to a machine using the RAG system."""
    import time
    start_time = time.time()
    
    try:
        # Check if machine exists
        machine_result = await db.execute(
            Base.metadata.tables['machines'].select().where(
                Base.metadata.tables['machines'].c.id == query_request.machine_id
            )
        )
        machine = machine_result.fetchone()
        
        if not machine:
            raise HTTPException(status_code=404, detail="Machine not found")
        
        # Check if we have processed documents for this machine
        docs_result = await db.execute(
            Base.metadata.tables['knowledge'].select().where(
                (Base.metadata.tables['knowledge'].c.machine_id == query_request.machine_id) &
                (Base.metadata.tables['knowledge'].c.status == 'ready')
            )
        )
        machine_docs = docs_result.fetchall()
        
        if not machine_docs:
            return QueryResponse(
                response="I don't have any processed documents for this machine yet. Please upload some documentation first.",
                source="system",
                machine_id=query_request.machine_id,
                documents_available=0,
                confidence_score=0.0,
                source_documents=[],
                processing_time=time.time() - start_time
            )
        
        # Use RAG system to answer the query
        db_conn = get_db_conn()
        try:
            # Use multi-document retrieval to search across ALL documents for this machine
            rag_response = retrieve_and_answer_multi_document(query_request.query, query_request.machine_id, db_conn)
            
            # Extract source documents if available
            source_documents = []
            if hasattr(rag_response, 'source_nodes'):
                source_documents = [node.get_content()[:200] + "..." for node in rag_response.source_nodes[:3]]
            
            processing_time = time.time() - start_time
            
            # Extract the response text
            response_text = str(rag_response)
            
            return QueryResponse(
                response=response_text,
                source="RAG system",
                machine_id=query_request.machine_id,
                documents_available=len(machine_docs),
                confidence_score=0.8,  # Placeholder - could be calculated from RAG scores
                source_documents=source_documents,
                processing_time=processing_time
            )
            
        finally:
            db_conn.close()
            
    except Exception as e:
        print(f"❌ Error in machine-specific query: {e}")
        return QueryResponse(
            response=f"I encountered an error while processing your query: {str(e)}",
            source="error",
            machine_id=query_request.machine_id,
            documents_available=0,
            confidence_score=0.0,
            source_documents=[],
            processing_time=time.time() - start_time
        )

@app.get("/machines/{machine_id}/documents")
async def get_machine_documents(machine_id: int, db: AsyncSession = Depends(get_db)):
    """Get all documents for a specific machine with their processing status."""
    try:
        # Check if machine exists
        machine_result = await db.execute(
            Base.metadata.tables['machines'].select().where(
                Base.metadata.tables['machines'].c.id == machine_id
            )
        )
        machine = machine_result.fetchone()
        
        if not machine:
            raise HTTPException(status_code=404, detail="Machine not found")
        
        # Get documents for this machine
        docs_result = await db.execute(
            Base.metadata.tables['knowledge'].select().where(
                Base.metadata.tables['knowledge'].c.machine_id == machine_id
            ).order_by(Base.metadata.tables['knowledge'].c.upload_time.desc())
        )
        documents = docs_result.fetchall()
        
        return {
            "machine": {
                "id": machine.id,
                "name": machine.name,
                "production_line": machine.production_line,
                "factory": machine.factory
            },
            "documents": [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "status": doc.status,
                    "upload_time": doc.upload_time,
                    "type": doc.type,
                    "tag": doc.tag
                }
                for doc in documents
            ],
            "summary": {
                "total_documents": len(documents),
                "ready_documents": len([d for d in documents if d.status == 'ready']),
                "processing_documents": len([d for d in documents if d.status == 'processing']),
                "failed_documents": len([d for d in documents if d.status == 'failed'])
            }
        }
        
    except Exception as e:
        print(f"❌ Error getting machine documents: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting machine documents: {str(e)}")

# Add server startup code
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting FastAPI server...")
    print("📡 Server will be available at: http://localhost:8000")
    print("📚 API documentation at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False) 