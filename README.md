# Chunk View

A semantic text analysis application for comparing and visualizing different chunking methods.

## Features

- **Document Upload**: Upload PDF documents for analysis
- **Multiple Chunking Methods**: Compare LlamaIndex and LangChain semantic chunking
- **Text Highlighting**: View extracted text with highlighted chunks
- **Interactive Interface**: Select and compare different chunking approaches

## Tech Stack

- **Frontend**: Next.js 15, React, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python
- **Chunking**: LlamaIndex, LangChain
- **PDF Processing**: PyMuPDF

## Quick Start

1. **Backend**:
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Access**: Open http://localhost:3000

## Project Structure

```
chunk_view/
├── backend/           # FastAPI backend
├── frontend/          # Next.js frontend
├── uploads/           # Uploaded documents
└── alembic/          # Database migrations
```

## API Endpoints

- `POST /upload` - Upload documents
- `GET /chunk/methods` - Get available chunking methods
- `POST /chunk/compare` - Compare chunking methods
