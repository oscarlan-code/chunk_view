# Upskill - AI-Powered Knowledge Management & Troubleshooting System

A role-based RAG (Retrieval-Augmented Generation) platform that enables managers to upload knowledge documents and operators to query them for troubleshooting assistance.

## 🚀 Features

- **Role-Based Access**: Separate interfaces for managers and operators
- **Document Upload**: Support for PDF, TXT, DOC, DOCX files with real-time processing
- **AI-Powered Queries**: GPT-4-turbo powered RAG system for intelligent responses
- **Multi-Document Search**: Search across all documents associated with a machine
- **Real-time Progress**: WebSocket-based progress updates during document processing
- **Vector Persistence**: Qdrant vector database with disk persistence
- **Machine Management**: Associate documents with specific machines
- **Session Reports**: Generate troubleshooting session reports

## 🏗️ Architecture

### System Overview
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Data Layer    │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   PostgreSQL    │
│                 │    │                 │    │   + Qdrant      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Key Components
- **Frontend**: Next.js with TypeScript, role-based dashboards
- **Backend**: FastAPI with async/await, WebSocket support
- **Database**: PostgreSQL for structured data, Qdrant for vector storage
- **AI**: OpenAI GPT-4-turbo, BGE-large-en-v1.5 embeddings
- **Processing**: LlamaIndex for RAG pipeline

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL
- Docker (for Qdrant)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd upskill
```

### 2. Set Up Database
```bash
# Start PostgreSQL
brew services start postgresql

# Create database
createdb upskill
```

### 3. Start Qdrant Vector Database
```bash
docker run -p 6333:6333 qdrant/qdrant
```

### 4. Backend Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your OpenAI API key and database credentials
```

### 5. Frontend Setup
```bash
cd frontend
npm install
```

## 🚀 Running the Application

### Start Backend
```bash
# From project root
source venv/bin/activate
cd backend
python main.py
```
Backend will be available at: http://localhost:8000

### Start Frontend
```bash
# From project root
cd frontend
npm run dev
```
Frontend will be available at: http://localhost:3000

## 📊 Database Schema

### Core Tables
- **users**: User accounts with roles (manager/operator)
- **machines**: Production machines and their metadata
- **knowledge**: Document metadata and processing status
- **knowledge_chunks**: Text chunks with embeddings
- **sessions**: Troubleshooting sessions
- **reports**: Generated session reports

### Key Relationships
```
users (1) ──► (many) knowledge
machines (1) ──► (many) knowledge
knowledge (1) ──► (many) knowledge_chunks
users (1) ──► (many) sessions
sessions (1) ──► (many) reports
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the project root:

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=upskill
DB_USER=postgres
DB_PASSWORD=your_password

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Application
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
```

## 📖 Usage

### Manager Role
1. **Upload Documents**: Upload PDF/TXT/DOC files for specific machines
2. **Monitor Processing**: Real-time progress updates during document processing
3. **Manage Knowledge**: View and manage uploaded documents
4. **Generate Reports**: Access troubleshooting session reports

### Operator Role
1. **Select Machine**: Choose a machine for troubleshooting
2. **Ask Questions**: Query the AI system for troubleshooting assistance
3. **Get Responses**: Receive AI-powered answers based on uploaded knowledge
4. **Generate Reports**: Create session reports for documentation

## 🔍 API Endpoints

### Core Endpoints
- `POST /upload` - Upload and process documents
- `POST /query/machine` - Query machine-specific knowledge
- `POST /chat` - General chat with RAG system
- `GET /machines` - List all machines
- `GET /knowledge/by_machine/{id}` - Get documents for a machine

### WebSocket
- `WS /ws/{client_id}` - Real-time progress updates

## 🧪 Testing

### Test Multi-Document Query
```bash
# From project root
source venv/bin/activate
python test_multi_document_query.py
```

### Review Chunk Data
```bash
# From project root
source venv/bin/activate
python review_chunk_data.py
```

## 📁 Project Structure

```
upskill/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── ai_rag.py            # RAG pipeline implementation
│   ├── requirements.txt     # Python dependencies
│   └── uploads/            # Uploaded files
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js pages
│   │   ├── components/     # React components
│   │   └── lib/           # Utilities
│   ├── package.json        # Node.js dependencies
│   └── next.config.ts      # Next.js configuration
├── venv/                   # Python virtual environment
├── persistent_indexes/     # Vector embeddings cache
├── uploads/               # Global uploads directory
├── requirements.txt       # Backend dependencies
├── README.md             # This file
└── .gitignore           # Git ignore rules
```

## 🔧 Development

### Adding New Features
1. **Backend**: Add endpoints in `backend/main.py`
2. **Frontend**: Create components in `frontend/src/components/`
3. **Database**: Use Alembic for migrations
4. **Testing**: Add tests in `backend/tests/`

### Code Style
- **Python**: Follow PEP 8, use type hints
- **TypeScript**: Use strict mode, proper interfaces
- **SQL**: Use parameterized queries, proper indexing

## 🐛 Troubleshooting

### Common Issues
1. **Database Connection**: Ensure PostgreSQL is running
2. **Qdrant Connection**: Check Docker container status
3. **Environment Variables**: Verify `.env` file exists
4. **Dependencies**: Reinstall if virtual environment issues

### Debug Mode
```bash
# Backend with debug logging
cd backend
python main.py --debug

# Frontend with detailed logs
cd frontend
npm run dev -- --verbose
```

## 📈 Performance

### Optimization Tips
- **Vector Search**: Use appropriate chunk sizes (800 chars with 100 overlap)
- **Database**: Index frequently queried columns
- **Caching**: Leverage Qdrant's disk persistence
- **Async Processing**: Use background tasks for document processing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **LlamaIndex**: RAG pipeline framework
- **Qdrant**: Vector database
- **FastAPI**: Modern Python web framework
- **Next.js**: React framework for production
- **OpenAI**: GPT-4-turbo for intelligent responses

---

**Note**: This is a demo version. For production use, implement proper authentication, security measures, and deployment configurations.
