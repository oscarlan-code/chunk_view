#!/usr/bin/env python3
"""
Script to review chunk data from the database
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json

def review_chunk_data(knowledge_id=None):
    """Review chunk data from the database"""
    
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
        """, (knowledge_id,))
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
        """)
    
    chunks = cursor.fetchall()
    cursor.close()
    conn.close()
    
    print(f"📚 Found {len(chunks)} chunks")
    print("=" * 80)
    
    # Group by knowledge_id
    grouped_chunks = {}
    for chunk in chunks:
        knowledge_id = chunk['knowledge_id']
        if knowledge_id not in grouped_chunks:
            grouped_chunks[knowledge_id] = []
        grouped_chunks[knowledge_id].append(chunk)
    
    for knowledge_id, chunks_list in grouped_chunks.items():
        print(f"\n📄 Document ID: {knowledge_id}")
        print(f"📁 Filename: {chunks_list[0]['filename']}")
        print(f"📊 Status: {chunks_list[0]['status']}")
        print(f"🔢 Total Chunks: {len(chunks_list)}")
        print("-" * 60)
        
        for i, chunk in enumerate(chunks_list):
            print(f"\n🔸 Chunk {i+1} (Index: {chunk['chunk_index']})")
            print(f"   ID: {chunk['id']}")
            print(f"   Content Length: {len(chunk['chunk_text'])} characters")
            print(f"   Vector Dimension: {len(chunk['embedding']) if chunk['embedding'] else 0}")
            print(f"   Metadata: {chunk['metadata']}")
            
            # Show first 200 characters of content
            content_preview = chunk['chunk_text'][:200].replace('\n', '\\n')
            if len(chunk['chunk_text']) > 200:
                content_preview += "..."
            print(f"   Content Preview: {content_preview}")
            
            # Show first few vector values
            if chunk['embedding']:
                vector_preview = chunk['embedding'][:50]  # Show first 50 chars of embedding string
                print(f"   Vector Preview: {vector_preview}...")
            else:
                print(f"   Vector Preview: No embedding stored")
            print()

def analyze_chunk_statistics():
    """Analyze chunk statistics"""
    
    conn = psycopg2.connect(
        host="localhost",
        database="upskill",
        user="postgres",
        password="postgres"
    )
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get statistics
    cursor.execute("""
        SELECT 
            k.id as knowledge_id,
            k.filename,
            k.status,
            COUNT(kc.id) as chunk_count,
            AVG(LENGTH(kc.chunk_text)) as avg_content_length,
            MIN(LENGTH(kc.chunk_text)) as min_content_length,
            MAX(LENGTH(kc.chunk_text)) as max_content_length
        FROM knowledge k
        LEFT JOIN knowledge_chunks kc ON k.id = kc.knowledge_id
        GROUP BY k.id, k.filename, k.status
        ORDER BY k.id
    """)
    
    stats = cursor.fetchall()
    cursor.close()
    conn.close()
    
    print("📊 Chunk Statistics")
    print("=" * 80)
    
    for stat in stats:
        print(f"\n📄 Document: {stat['filename']}")
        print(f"   ID: {stat['knowledge_id']}")
        print(f"   Status: {stat['status']}")
        print(f"   Chunks: {stat['chunk_count']}")
        if stat['avg_content_length']:
            print(f"   Avg Content Length: {stat['avg_content_length']:.1f} chars")
            print(f"   Min Content Length: {stat['min_content_length']} chars")
            print(f"   Max Content Length: {stat['max_content_length']} chars")
        else:
            print("   No chunks found")

if __name__ == "__main__":
    print("🔍 Chunk Data Review Tool")
    print("=" * 80)
    
    # Show statistics first
    analyze_chunk_statistics()
    
    print("\n" + "=" * 80)
    print("📋 Detailed Chunk Review")
    print("=" * 80)
    
    # Review chunks for knowledge_id 10 (ONE POINT LESSON)
    print("\n🔍 Reviewing chunks for knowledge_id 10 (ONE POINT LESSON):")
    review_chunk_data(10)
    
    # Review chunks for knowledge_id 11 (Operation Manual)
    print("\n🔍 Reviewing chunks for knowledge_id 11 (Operation Manual):")
    review_chunk_data(11) 