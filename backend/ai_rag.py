"""
Enhanced RAG System with LlamaIndex Pathway - Based on rag_comparison project
"""

import os
import re
import time
import logging
import asyncio
import threading
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# LlamaIndex imports - Fixed imports
from llama_index.core import VectorStoreIndex, Document as LlamaDocument
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.schema import TextNode
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Database and vector store imports
import psycopg2
from psycopg2.extras import RealDictCursor
import qdrant_client
from qdrant_client import models

# Environment and configuration
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

# Configuration
COLLECTION_NAME = "knowledge_chunks"
EMBEDDING_SIZE = 1024
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "upskill")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# Initialize Qdrant client
qdrant_client = qdrant_client.QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

# Initialize embedding model - Consistent instance
embedding_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-large-en-v1.5",
    cache_folder="persistent_indexes"
)

# Verify embedding dimensions
try:
    test_embedding = embedding_model.get_text_embedding("test")
    print(f"✅ Verified embedding model dimensions: {len(test_embedding)}")
    assert len(test_embedding) == EMBEDDING_SIZE, f"Embedding size mismatch: got {len(test_embedding)}, expected {EMBEDDING_SIZE}"
except Exception as e:
    print(f"❌ Error verifying embedding model: {e}")
    raise

# Initialize LLM
llm = OpenAI(
    model="gpt-4-turbo-preview",
    temperature=0.1,
    api_key=os.getenv("OPENAI_API_KEY")
)

# Node parser for chunking
node_parser = SentenceSplitter(chunk_size=800, chunk_overlap=100)

def get_db_conn():
    """Get database connection"""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def ensure_qdrant_collection():
    """Ensure Qdrant collection exists without deleting existing data."""
    try:
        # Check if collection exists
        collections = qdrant_client.get_collections().collections
        collection_names = [c.name for c in collections]

        if COLLECTION_NAME not in collection_names:
            print(f"Collection '{COLLECTION_NAME}' not found. Creating it...")
            # Create collection only if it does not exist
            qdrant_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=EMBEDDING_SIZE,
                    distance=models.Distance.COSINE,
                    on_disk=True  # Ensure vectors are persisted to disk
                )
            )
            print(f"✅ Created Qdrant collection '{COLLECTION_NAME}' with disk persistence")
        else:
            print(f"✅ Qdrant collection '{COLLECTION_NAME}' already exists.")

    except Exception as e:
        print(f"❌ Error ensuring Qdrant collection: {e}")
        raise

def load_text_file(file_path: str) -> str:
    """
    Load text file using the same approach as rag_comparison project.
    Simple, robust text loading with multiple encoding fallbacks.
    """
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'utf-16']
    
    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding, errors="ignore") as f:
                text = f.read()
                if text.strip():  # Check if we got meaningful content
                    print(f"✅ Successfully read file with {encoding} encoding")
                    return text
        except Exception as e:
            print(f"⚠️ Failed to read with {encoding}: {e}")
            continue
    
    # Final fallback with utf-8 and ignore errors
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
            print(f"✅ Successfully read file with utf-8 encoding (fallback)")
            return text
    except Exception as e:
        print(f"❌ Failed to read file: {e}")
        return ""

def clean_text_simple(text: str) -> str:
    """
    Simple text cleaning - basic normalization without aggressive OCR fixes
    """
    if not text:
        return ""
    
    # Basic cleaning
    text = text.strip()
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove excessive line breaks
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text

def process_and_index_document_simple(text: str, knowledge_id: int, db_conn) -> None:
    """
    Process and index document using LlamaIndex with proper TextNode creation
    """
    try:
        print(f"🔄 Processing document for knowledge_id: {knowledge_id}")
        
        # Ensure Qdrant collection exists with correct dimensions
        ensure_qdrant_collection()
        
        # Clean text
        cleaned_text = clean_text_simple(text)
        if not cleaned_text.strip():
            print("❌ No meaningful text content found")
            return
        
        # Create LlamaDocument
        document = LlamaDocument(text=cleaned_text)
        
        # Parse into nodes using SentenceSplitter
        nodes = node_parser.get_nodes_from_documents([document])
        
        # Ensure all nodes are TextNode instances with proper text content
        text_nodes = []
        for i, node in enumerate(nodes):
            if hasattr(node, 'text') and node.text:
                # Create explicit TextNode with metadata
                text_node = TextNode(
                    text=node.text,
                    metadata={
                "knowledge_id": knowledge_id,
                        "chunk_index": i,
                        "source": "upload"
                    }
                )
                text_nodes.append(text_node)
            else:
                print(f"⚠️ Skipping node {i} with empty text content")
        
        if not text_nodes:
            print("❌ No valid text nodes created")
            return
        
        print(f"✅ Created {len(text_nodes)} text nodes")
        
        # Store chunks and embeddings
        store_chunks_and_embeddings_simple(text_nodes, knowledge_id, db_conn)
        
        print(f"✅ Document processing completed for knowledge_id: {knowledge_id}")
        
    except Exception as e:
        print(f"❌ Error processing document: {e}")
        raise

def store_chunks_and_embeddings_simple(nodes: List[TextNode], knowledge_id: int, db_conn) -> None:
    """
    Store chunks and embeddings with proper text content in Qdrant payload
    """
    try:
        print(f"💾 Storing {len(nodes)} chunks for knowledge_id: {knowledge_id}")
        
        # Prepare points for Qdrant
        points = []
        
        for i, node in enumerate(nodes):
            try:
                # Ensure node.text is not None and is a string
                if not node.text or not isinstance(node.text, str):
                    print(f"⚠️ Skipping node {i} with invalid text: {type(node.text)}")
                    continue
                
                # Get embedding for the text content
                embedding = embedding_model.get_text_embedding(node.text)
                
                # Verify embedding dimension
                assert len(embedding) == EMBEDDING_SIZE, f"Embedding size mismatch: got {len(embedding)}, expected {EMBEDDING_SIZE}"
                print(f"✅ Verified embedding dimension: {len(embedding)}")
                
                # Create point with integer ID (Qdrant requirement)
                point = models.PointStruct(
                    id=i,  # Use simple integer ID
                    vector=embedding,  # Ensure vector is properly set
                    payload={
                        "knowledge_id": knowledge_id,
                        "chunk_index": i,
                        "text": node.text,  # Ensure text is stored
                        "metadata": node.metadata
                    }
                )
                points.append(point)
                print(f"✅ Prepared point {i} with embedding dimension {len(embedding)}")
                
            except Exception as e:
                print(f"⚠️ Error processing node {i}: {e}")
                continue
        
        if points:
            # Insert points into Qdrant
            qdrant_client.upsert(
                collection_name=COLLECTION_NAME,
                points=points
            )
            print(f"✅ Stored {len(points)} points in Qdrant")
        else:
            print("❌ No valid points to store in Qdrant")
        
        # Store in PostgreSQL
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Delete existing chunks for this knowledge_id
        cursor.execute("DELETE FROM knowledge_chunks WHERE knowledge_id = %s", (knowledge_id,))
        
        # Insert new chunks
        for i, node in enumerate(nodes):
            try:
                if not node.text or not isinstance(node.text, str):
                    continue
                    
                embedding = embedding_model.get_text_embedding(node.text)
                cursor.execute(
                    "INSERT INTO knowledge_chunks (knowledge_id, chunk_index, chunk_text, embedding, metadata) VALUES (%s, %s, %s, %s, %s)",
                    (knowledge_id, i, node.text, psycopg2.extras.Json(embedding), psycopg2.extras.Json(node.metadata))
                )
            except Exception as e:
                print(f"⚠️ Error storing chunk {i} in PostgreSQL: {e}")
                continue
        
        db_conn.commit()
        cursor.close()
        print(f"✅ Stored chunks in PostgreSQL")
        
    except Exception as e:
        print(f"❌ Error storing chunks and embeddings: {e}")
        raise

def get_or_create_index_simple(knowledge_id: int, db_conn) -> Optional[VectorStoreIndex]:
    """
    Get or create vector store index for a knowledge document
    """
    try:
        # Check if chunks exist in Qdrant
        try:
            search_result = qdrant_client.search(
                collection_name=COLLECTION_NAME,
                query_vector=[0.0] * EMBEDDING_SIZE,  # Dummy vector for checking existence
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="knowledge_id",
                            match=models.MatchValue(value=knowledge_id)
                        )
                    ]
                ),
                limit=1
            )
            
            if not search_result:
                print(f"❌ No chunks found for knowledge_id: {knowledge_id}")
                return None
            
        except Exception as e:
            print(f"⚠️ Error checking Qdrant for knowledge_id {knowledge_id}: {e}")
            return None
        
        # Create vector store
        vector_store = QdrantVectorStore(
            client=qdrant_client,
            collection_name=COLLECTION_NAME
        )
        
        # Create index with consistent embedding model
        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            embed_model=embedding_model
        )
        
        print(f"✅ Created/retrieved index for knowledge_id: {knowledge_id}")
        return index
        
    except Exception as e:
        print(f"❌ Error creating index: {e}")
        return None

def retrieve_and_answer_with_persistence_simple(query: str, machine_id: int, db_conn) -> str:
    """
    Retrieve and answer query using persistent storage
    """
    try:
        print(f"🔍 Processing query: '{query}' for machine_id: {machine_id}")
        
        # Get ready documents for the machine
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "SELECT id FROM knowledge WHERE machine_id = %s AND status = 'ready' ORDER BY id DESC",
            (machine_id,)
        )
        knowledge_records = cursor.fetchall()
        cursor.close()
        
        if not knowledge_records:
            return "No documents available for this machine."
        
        # Try to find a document that has vectors in Qdrant
        knowledge_id = None
        for record in knowledge_records:
            test_id = record['id']
            try:
                # Check if this document has vectors in Qdrant
                search_result = qdrant_client.search(
                    collection_name=COLLECTION_NAME,
                    query_vector=[0.0] * EMBEDDING_SIZE,  # Dummy vector for checking existence
                    query_filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="knowledge_id",
                                match=models.MatchValue(value=test_id)
                            )
                        ]
                    ),
                    limit=1
                )
                
                if search_result:
                    knowledge_id = test_id
                    print(f"✅ Found document with vectors: knowledge_id {knowledge_id}")
                    break
                    
            except Exception as e:
                print(f"⚠️ Error checking vectors for knowledge_id {test_id}: {e}")
                continue
        
        # If no document with vectors found, use the latest one
        if knowledge_id is None:
            knowledge_id = knowledge_records[0]['id']
            print(f"⚠️ No documents with vectors found, using latest: knowledge_id {knowledge_id}")
        else:
            print(f"🔍 Using knowledge_id: {knowledge_id}")
        
        # Get or create index
        index = get_or_create_index_simple(knowledge_id, db_conn)
        if not index:
            return "Failed to retrieve document index. Please re-upload the document."
        
        try:
            # Create query engine with proper retriever setup
            query_engine = index.as_query_engine(
                embed_model=embedding_model,
                llm=llm,
                similarity_top_k=5
            )
            
            # Execute query
            response = query_engine.query(query)
            
            print(f"✅ Query completed successfully")
            return str(response)
            
        except Exception as e:
            print(f"❌ Error in query execution: {e}")
            # If there's a TextNode error, it might be due to missing text in payload
            if "TextNode" in str(e) and "text" in str(e):
                print("🔄 Attempting to reprocess document due to TextNode error...")
                # Try to recreate the collection and reprocess
                ensure_qdrant_collection()
                return "Document needs to be reprocessed. Please re-upload the document."
            
            # If there's a dimension error, recreate the collection
            if "Vector dimension error" in str(e):
                print("🔄 Recreating Qdrant collection due to dimension error...")
                ensure_qdrant_collection()
                return "Document needs to be reprocessed. Please re-upload the document."
            
            return f"Error processing query: {str(e)}"
        
    except Exception as e:
        print(f"❌ Error in retrieve_and_answer_with_persistence: {e}")
        return f"Error processing query: {str(e)}"

def retrieve_and_answer_multi_document(query: str, machine_id: int, db_conn) -> str:
    """
    Retrieve and answer query using ALL available documents for a machine
    """
    try:
        print(f"🔍 Processing query: '{query}' for machine_id: {machine_id}")
        
        # Get ALL ready documents for the machine
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "SELECT id FROM knowledge WHERE machine_id = %s AND status = 'ready' ORDER BY id DESC",
            (machine_id,)
        )
        knowledge_records = cursor.fetchall()
        cursor.close()
        
        if not knowledge_records:
            return "No documents available for this machine."
        
        print(f"📚 Found {len(knowledge_records)} documents for machine {machine_id}")
        
        # Check if any documents have vectors in Qdrant
        documents_with_vectors = []
        for record in knowledge_records:
            knowledge_id = record['id']
            try:
                # Check if this document has vectors in Qdrant
                search_result = qdrant_client.search(
                    collection_name=COLLECTION_NAME,
                    query_vector=[0.0] * EMBEDDING_SIZE,  # Dummy vector for checking existence
                    query_filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="knowledge_id",
                                match=models.MatchValue(value=knowledge_id)
                            )
                        ]
                    ),
                    limit=1
                )
                
                if search_result:
                    documents_with_vectors.append(knowledge_id)
                    print(f"✅ Found vectors for knowledge_id: {knowledge_id}")
                    
            except Exception as e:
                print(f"⚠️ Error checking knowledge_id {knowledge_id}: {e}")
                continue
        
        if not documents_with_vectors:
            return "No document chunks found. Please re-upload the documents."
        
        print(f"📖 Found {len(documents_with_vectors)} documents with vectors")
        
        # Create vector store for multi-document search
        try:
            vector_store = QdrantVectorStore(
                client=qdrant_client,
                collection_name=COLLECTION_NAME
            )
            
            # Create index that can search across all documents
            combined_index = VectorStoreIndex.from_vector_store(
                vector_store=vector_store,
                embed_model=embedding_model
            )
            
            # Create query engine with enhanced configuration for multi-document search
            query_engine = combined_index.as_query_engine(
                embed_model=embedding_model,
                llm=llm,
                similarity_top_k=15,  # Increased for multi-document search
                response_mode="compact"
            )
            
            # Execute query
            response = query_engine.query(query)
            
            print(f"✅ Multi-document query completed successfully across {len(documents_with_vectors)} documents")
            return str(response)
            
        except Exception as e:
            print(f"❌ Error in multi-document query execution: {e}")
            return f"Error processing query: {str(e)}"
        
    except Exception as e:
        print(f"❌ Error in retrieve_and_answer_multi_document: {e}")
        return f"Error processing query: {str(e)}"

# Wrapper functions for backward compatibility
def process_and_index_document(text, knowledge_id, db_conn):
    """Wrapper for backward compatibility"""
    return process_and_index_document_simple(text, knowledge_id, db_conn)

def retrieve_and_answer_with_persistence(query: str, machine_id: int, db_conn) -> str:
    """Wrapper for backward compatibility"""
    return retrieve_and_answer_with_persistence_simple(query, machine_id, db_conn)