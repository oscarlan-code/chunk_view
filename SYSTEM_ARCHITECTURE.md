# Upskill System Architecture & Flow Charts

## System Overview

The upskill system is a role-based RAG (Retrieval-Augmented Generation) platform that enables managers to upload knowledge documents and operators to query them for troubleshooting assistance.

---

## High-Level System Architecture

```mermaid
graph TB
    subgraph "Frontend (Next.js)"
        A[Manager Dashboard]
        B[Operator Dashboard]
        C[Upload Interface]
        D[Query Interface]
        E[WebSocket Client]
    end

    subgraph "Backend (FastAPI)"
        F[API Gateway]
        G[Upload Handler]
        H[Document Processor]
        I[Vector Indexer]
        J[Query Engine]
        K[WebSocket Manager]
        L[RAG Pipeline]
    end

    subgraph "Data Layer"
        M[(PostgreSQL)]
        N[(Qdrant Vector DB)]
        O[File Storage]
    end

    subgraph "External Services"
        P[OpenAI GPT-4]
        Q[Embedding Model]
    end

    A --> F
    B --> F
    C --> G
    D --> J
    E --> K
    G --> H
    H --> I
    I --> N
    J --> L
    L --> N
    L --> P
    L --> Q
    H --> M
    I --> M
    H --> O
    K --> E
```

---

## Detailed Component Architecture

```mermaid
graph TD
    subgraph "Frontend Components"
        A1[Manager Role]
        A2[Operator Role]
        A3[File Upload UI]
        A4[Progress Bar]
        A5[Query Interface]
        A6[WebSocket Connection]
    end

    subgraph "Backend Services"
        B1[FastAPI Server]
        B2[Upload Endpoint]
        B3[Document Processing]
        B4[Vector Indexing]
        B5[Query Processing]
        B6[WebSocket Manager]
        B7[RAG Engine]
    end

    subgraph "Data Storage"
        C1[(PostgreSQL)]
        C2[(Qdrant)]
        C3[File System]
    end

    subgraph "AI Services"
        D1[OpenAI GPT-4]
        D2[BGE Embedding Model]
        D3[Text Chunking]
    end

    A1 --> B1
    A2 --> B1
    A3 --> B2
    A4 --> B6
    A5 --> B5
    A6 --> B6
    B2 --> B3
    B3 --> B4
    B4 --> C2
    B5 --> B7
    B7 --> C2
    B7 --> D1
    B3 --> C1
    B4 --> C1
    B3 --> C3
    B6 --> A6
    B3 --> D3
    B4 --> D2
```

---

## File Upload to Knowledge Creation Flow

```mermaid
sequenceDiagram
    participant M as Manager
    participant F as Frontend
    participant B as Backend
    participant DB as PostgreSQL
    participant Q as Qdrant
    participant AI as AI Services
    participant WS as WebSocket

    M->>F: Select file & machine
    F->>B: POST /upload (FormData)
    B->>DB: Create knowledge record
    DB-->>B: Return knowledge_id
    B->>WS: Send progress (10%)
    
    B->>B: Extract text from file
    B->>WS: Send progress (20%)
    
    B->>AI: Chunk text into segments
    AI-->>B: Return text chunks
    B->>WS: Send progress (40%)
    
    B->>AI: Generate embeddings
    AI-->>B: Return vector embeddings
    B->>WS: Send progress (60%)
    
    B->>Q: Store vectors with metadata
    Q-->>B: Confirm storage
    B->>WS: Send progress (80%)
    
    B->>DB: Store chunk metadata
    DB-->>B: Confirm storage
    B->>WS: Send progress (95%)
    
    B->>DB: Update status to "ready"
    DB-->>B: Confirm update
    B->>WS: Send progress (100%)
    
    B-->>F: Return upload response
    F-->>M: Show success message
```

---

## Document Processing Pipeline

```mermaid
flowchart TD
    A[File Upload] --> B{File Type?}
    B -->|PDF| C[PDF Text Extraction]
    B -->|TXT| D[Direct Text Reading]
    B -->|DOC/DOCX| E[Word Document Processing]
    
    C --> F[Text Preprocessing]
    D --> F
    E --> F
    
    F --> G[Text Chunking]
    G --> H[Chunk Validation]
    H --> I{Chunks Valid?}
    I -->|No| G
    I -->|Yes| J[Generate Embeddings]
    
    J --> K[Vector Storage in Qdrant]
    K --> L[Metadata Storage in PostgreSQL]
    L --> M[Status Update]
    M --> N[WebSocket Progress Update]
    N --> O[Complete]
```

---

## Query Processing Flow

```mermaid
sequenceDiagram
    participant O as Operator
    participant F as Frontend
    participant B as Backend
    participant DB as PostgreSQL
    participant Q as Qdrant
    participant AI as OpenAI GPT-4

    O->>F: Enter query for machine
    F->>B: POST /query/machine
    B->>DB: Get machine documents
    DB-->>B: Return document list
    
    B->>Q: Search similar vectors
    Q-->>B: Return relevant chunks
    
    B->>B: Format context from chunks
    B->>AI: Send query + context
    AI-->>B: Return AI response
    
    B->>B: Format response
    B-->>F: Return query result
    F-->>O: Display answer
```

---

## WebSocket Progress Update Flow

```mermaid
sequenceDiagram
    participant F as Frontend
    participant WS as WebSocket
    participant B as Backend
    participant T as Background Thread
    participant L as Main Event Loop

    F->>WS: Connect with client_id
    WS-->>F: Connection confirmed
    
    F->>B: Upload file
    B->>T: Start processing in thread
    T->>L: Schedule progress update
    L->>WS: Send progress message
    WS-->>F: Update progress bar
    
    Note over T,L: asyncio.run_coroutine_threadsafe()
    
    T->>L: Schedule next update
    L->>WS: Send progress message
    WS-->>F: Update progress bar
    
    T->>L: Schedule completion
    L->>WS: Send final status
    WS-->>F: Show completion
```

---

## Data Flow Architecture

```mermaid
graph LR
    subgraph "Input Layer"
        A1[File Upload]
        A2[User Query]
    end

    subgraph "Processing Layer"
        B1[Text Extraction]
        B2[Chunking]
        B3[Embedding Generation]
        B4[Vector Storage]
        B5[Query Processing]
        B6[RAG Retrieval]
    end

    subgraph "Storage Layer"
        C1[(PostgreSQL)]
        C2[(Qdrant)]
        C3[File System]
    end

    subgraph "Output Layer"
        D1[Progress Updates]
        D2[Query Results]
        D3[Status Updates]
    end

    A1 --> B1
    A2 --> B5
    B1 --> B2
    B2 --> B3
    B3 --> B4
    B4 --> C2
    B5 --> B6
    B6 --> C2
    B1 --> C1
    B4 --> C1
    B1 --> C3
    B4 --> D1
    B6 --> D2
    B4 --> D3
```

---

## Database Schema & Relationships

```mermaid
erDiagram
    USERS {
        int id PK
        string username
        string password_hash
        string role
        datetime created_at
    }
    
    MACHINES {
        int id PK
        string name
        string production_line
        string factory
        string status
        date last_maintenance
    }
    
    KNOWLEDGE {
        int id PK
        string filename
        int uploaded_by FK
        int machine_id FK
        datetime upload_time
        string type
        string status
        string tag
    }
    
    KNOWLEDGE_CHUNKS {
        int id PK
        int knowledge_id FK
        int chunk_index
        text content
        datetime created_at
    }
    
    USERS ||--o{ KNOWLEDGE : "uploads"
    MACHINES ||--o{ KNOWLEDGE : "has_documents"
    KNOWLEDGE ||--o{ KNOWLEDGE_CHUNKS : "contains_chunks"
```

---

## Vector Storage Architecture

```mermaid
graph TB
    subgraph "Qdrant Vector Database"
        A[Collection: knowledge_chunks]
        B[Vector Config]
        C[Points Storage]
        D[Disk Persistence]
    end

    subgraph "Vector Metadata"
        E[knowledge_id]
        F[chunk_index]
        G[content_hash]
        H[embedding_vector]
    end

    subgraph "Search Operations"
        I[Similarity Search]
        J[Filter by machine_id]
        K[Top-K Retrieval]
    end

    A --> B
    B --> C
    C --> D
    C --> E
    C --> F
    C --> G
    C --> H
    A --> I
    I --> J
    I --> K
```

---

## Error Handling & Recovery Flow

```mermaid
flowchart TD
    A[Upload Request] --> B{File Valid?}
    B -->|No| C[Return Error]
    B -->|Yes| D[Start Processing]
    
    D --> E{Database Connection?}
    E -->|No| F[Retry Connection]
    E -->|Yes| G[Create Record]
    
    G --> H{Text Extraction?}
    H -->|No| I[Mark as Failed]
    H -->|Yes| J[Generate Chunks]
    
    J --> K{Qdrant Available?}
    K -->|No| L[Queue for Retry]
    K -->|Yes| M[Store Vectors]
    
    M --> N{All Vectors Stored?}
    N -->|No| O[Partial Success]
    N -->|Yes| P[Mark as Ready]
    
    P --> Q[Send Success Response]
    O --> R[Send Partial Success]
    I --> S[Send Failure Response]
```

---

## Performance Optimization Points

```mermaid
graph LR
    subgraph "Upload Optimization"
        A1[Async File Processing]
        A2[Chunked Upload]
        A3[Progress Streaming]
    end

    subgraph "Query Optimization"
        B1[Vector Indexing]
        B2[Semantic Search]
        B3[Context Window]
    end

    subgraph "Storage Optimization"
        C1[Disk Persistence]
        C2[Vector Compression]
        C3[Metadata Indexing]
    end

    subgraph "Network Optimization"
        D1[WebSocket Connection]
        D2[Real-time Updates]
        D3[Connection Pooling]
    end

    A1 --> A2
    A2 --> A3
    B1 --> B2
    B2 --> B3
    C1 --> C2
    C2 --> C3
    D1 --> D2
    D2 --> D3
```

---

## Security & Access Control

```mermaid
graph TD
    subgraph "Authentication"
        A[User Login]
        B[Role Assignment]
        C[Session Management]
    end

    subgraph "Authorization"
        D[Manager Permissions]
        E[Operator Permissions]
        F[Resource Access Control]
    end

    subgraph "Data Protection"
        G[File Validation]
        H[SQL Injection Prevention]
        I[XSS Protection]
    end

    A --> B
    B --> C
    C --> D
    C --> E
    D --> F
    E --> F
    G --> H
    H --> I
```

---

## Monitoring & Logging Architecture

```mermaid
graph LR
    subgraph "Application Logs"
        A[Upload Events]
        B[Processing Events]
        C[Query Events]
        D[Error Events]
    end

    subgraph "Performance Metrics"
        E[Processing Time]
        F[Query Response Time]
        G[Memory Usage]
        H[Vector Storage Size]
    end

    subgraph "System Health"
        I[Database Status]
        J[Qdrant Status]
        K[File System Status]
        L[Network Status]
    end

    A --> E
    B --> F
    C --> G
    D --> H
    E --> I
    F --> J
    G --> K
    H --> L
```

---

## Deployment Architecture

```mermaid
graph TB
    subgraph "Development Environment"
        A[Local PostgreSQL]
        B[Local Qdrant]
        C[Local File Storage]
    end

    subgraph "Production Environment"
        D[Cloud PostgreSQL]
        E[Cloud Qdrant]
        F[Cloud File Storage]
        G[Load Balancer]
        H[CDN]
    end

    subgraph "Services"
        I[Backend API]
        J[Frontend App]
        K[WebSocket Server]
        L[Background Workers]
    end

    A --> I
    B --> I
    C --> I
    D --> I
    E --> I
    F --> I
    G --> J
    H --> J
    I --> K
    I --> L
```

---

## Key Technical Specifications

### File Processing Pipeline
- **Supported Formats**: PDF, TXT, DOC, DOCX
- **Text Extraction**: PyMuPDF, pdfplumber
- **Chunking Strategy**: Semantic chunking with overlap
- **Chunk Size**: Configurable (default: 1000 characters)
- **Overlap**: 200 characters between chunks

### Vector Storage
- **Embedding Model**: BGE-large-en-v1.5
- **Vector Dimension**: 1024
- **Distance Metric**: Cosine similarity
- **Persistence**: Disk-based with `on_disk: true`
- **Collection**: `knowledge_chunks`

### Query Processing
- **Search Strategy**: Semantic similarity + metadata filtering
- **Context Window**: Top 5 most relevant chunks
- **AI Model**: OpenAI GPT-4-turbo
- **Response Format**: Structured with confidence scores

### Real-time Communication
- **Protocol**: WebSocket
- **Progress Updates**: 10% → 100% with status messages
- **Connection Management**: Thread-safe async operations
- **Client Tracking**: Per-client connection management

### Database Schema
- **Knowledge Records**: File metadata and processing status
- **Knowledge Chunks**: Text chunks with indexing metadata
- **Machine Association**: Documents linked to specific machines
- **User Tracking**: Upload history and permissions

---

## Recent System Improvements

### WebSocket Progress Updates
- **Issue**: "Client not connected to WebSocket" errors
- **Solution**: `asyncio.run_coroutine_threadsafe()` with main event loop
- **Result**: Reliable real-time progress updates

### Qdrant Vector Persistence
- **Issue**: Vector data loss on restart
- **Solution**: `on_disk: true` configuration
- **Result**: Persistent vector storage across restarts

### Database Operations
- **Issue**: Async SQLAlchemy operation errors
- **Solution**: Proper async/await syntax with `select()`
- **Result**: Reliable database operations

### Non-Destructive Collection Management
- **Issue**: Aggressive collection deletion
- **Solution**: Only create collections if they don't exist
- **Result**: Multiple uploads without data loss

---

This architecture ensures a robust, scalable, and maintainable system for knowledge management and RAG-based troubleshooting assistance. 