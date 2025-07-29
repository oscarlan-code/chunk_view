#!/usr/bin/env python3
"""
Interactive chunk data preview script
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
import sys

def preview_chunks(knowledge_id=None, limit=5):
    """Preview chunk data in a readable format"""
    
    # Database connection
    conn = psycopg2.connect(
        host="localhost",
        database="upskill",
        user="postgres",
        password="postgres"
    )
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    if knowledge_id:
        # Get specific knowledge chunks
        cursor.execute("""
            SELECT 
                kc.id,
                kc.knowledge_id,
                kc.chunk_index,
                kc.chunk_text,
                kc.embedding,
                kc.metadata,
                k.filename,
                k.status
            FROM knowledge_chunks kc
            JOIN knowledge k ON kc.knowledge_id = k.id
            WHERE kc.knowledge_id = %s
            ORDER BY kc.chunk_index
            LIMIT %s
        """, (knowledge_id, limit))
    else:
        # Get all chunks with document info
        cursor.execute("""
            SELECT 
                kc.id,
                kc.knowledge_id,
                kc.chunk_index,
                kc.chunk_text,
                kc.embedding,
                kc.metadata,
                k.filename,
                k.status
            FROM knowledge_chunks kc
            JOIN knowledge k ON kc.knowledge_id = k.id
            ORDER BY kc.knowledge_id, kc.chunk_index
            LIMIT %s
        """, (limit,))
    
    chunks = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if not chunks:
        print("❌ No chunks found!")
        return
    
    print(f"📚 Found {len(chunks)} chunks to preview")
    print("=" * 80)
    
    for i, chunk in enumerate(chunks, 1):
        print(f"\n🔍 Chunk #{i}")
        print(f"   Document: {chunk['filename']} (ID: {chunk['knowledge_id']})")
        print(f"   Chunk Index: {chunk['chunk_index']}")
        print(f"   Status: {chunk['status']}")
        print(f"   Content Length: {len(chunk['chunk_text'])} characters")
        
        # Show content preview
        content = chunk['chunk_text']
        preview_length = 300
        
        if len(content) > preview_length:
            preview = content[:preview_length] + "..."
        else:
            preview = content
        
        # Format the preview nicely
        preview_lines = preview.split('\n')
        formatted_preview = '\n'.join([f"      {line}" for line in preview_lines])
        
        print(f"   Content Preview:")
        print(formatted_preview)
        
        # Show metadata if available
        if chunk['metadata']:
            try:
                metadata = json.loads(chunk['metadata'])
                print(f"   Metadata: {json.dumps(metadata, indent=6)}")
            except:
                print(f"   Metadata: {chunk['metadata']}")
        
        print("-" * 80)

def list_available_documents():
    """List all available documents with their chunk counts"""
    
    conn = psycopg2.connect(
        host="localhost",
        database="upskill",
        user="postgres",
        password="postgres"
    )
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT 
            k.id,
            k.filename,
            k.status,
            k.machine_id,
            COUNT(kc.id) as chunk_count,
            AVG(LENGTH(kc.chunk_text)) as avg_chunk_length
        FROM knowledge k
        LEFT JOIN knowledge_chunks kc ON k.id = kc.knowledge_id
        GROUP BY k.id, k.filename, k.status, k.machine_id
        ORDER BY k.id
    """)
    
    documents = cursor.fetchall()
    cursor.close()
    conn.close()
    
    print("📋 Available Documents:")
    print("=" * 80)
    
    for doc in documents:
        print(f"   ID: {doc['id']}")
        print(f"   Filename: {doc['filename']}")
        print(f"   Status: {doc['status']}")
        print(f"   Machine ID: {doc['machine_id']}")
        print(f"   Chunks: {doc['chunk_count']}")
        print(f"   Avg Chunk Length: {int(doc['avg_chunk_length'] or 0)} characters")
        print("-" * 40)

def main():
    """Main function with interactive menu"""
    
    print("🔍 Chunk Data Preview Tool")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. List available documents")
        print("2. Preview chunks for a specific document")
        print("3. Preview all chunks (limited)")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            list_available_documents()
        
        elif choice == "2":
            doc_id = input("Enter document ID: ").strip()
            try:
                doc_id = int(doc_id)
                limit = input("Enter number of chunks to preview (default 5): ").strip()
                limit = int(limit) if limit else 5
                preview_chunks(doc_id, limit)
            except ValueError:
                print("❌ Invalid document ID!")
        
        elif choice == "3":
            limit = input("Enter number of chunks to preview (default 10): ").strip()
            limit = int(limit) if limit else 10
            preview_chunks(None, limit)
        
        elif choice == "4":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice!")

if __name__ == "__main__":
    main() 