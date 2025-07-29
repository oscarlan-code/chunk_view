#!/usr/bin/env python3
"""
Preview Qdrant vector data and show vector-chunk relationships
"""

import requests
import json
import psycopg2
from psycopg2.extras import RealDictCursor

def get_qdrant_collection_info():
    """Get Qdrant collection information"""
    
    try:
        response = requests.get("http://localhost:6333/collections/knowledge_chunks")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get collection info: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error connecting to Qdrant: {e}")
        return None

def get_qdrant_points(limit=10):
    """Get sample points from Qdrant"""
    
    try:
        payload = {
            "limit": limit,
            "with_payload": True,
            "with_vector": False  # Don't include actual vectors to keep output readable
        }
        
        response = requests.post(
            "http://localhost:6333/collections/knowledge_chunks/points/scroll",
            json=payload
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get points: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error getting points: {e}")
        return None

def get_database_chunks_for_comparison():
    """Get chunk data from database for comparison"""
    
    conn = psycopg2.connect(
        host="localhost",
        database="upskill",
        user="postgres",
        password="postgres"
    )
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT 
            kc.id,
            kc.knowledge_id,
            kc.chunk_index,
            kc.chunk_text,
            k.filename
        FROM knowledge_chunks kc
        JOIN knowledge k ON kc.knowledge_id = k.id
        ORDER BY kc.knowledge_id, kc.chunk_index
        LIMIT 10
    """)
    
    chunks = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return chunks

def main():
    """Main function to preview Qdrant data"""
    
    print("🔍 Qdrant Vector Data Preview")
    print("=" * 60)
    
    # Get collection info
    print("\n📊 Collection Information:")
    print("-" * 40)
    
    collection_info = get_qdrant_collection_info()
    if collection_info:
        print(f"   Collection Name: {collection_info.get('name', 'N/A')}")
        print(f"   Vector Size: {collection_info.get('config', {}).get('params', {}).get('vectors', {}).get('size', 'N/A')}")
        print(f"   Distance: {collection_info.get('config', {}).get('params', {}).get('vectors', {}).get('distance', 'N/A')}")
        print(f"   On Disk: {collection_info.get('config', {}).get('params', {}).get('vectors', {}).get('on_disk', 'N/A')}")
        
        # Get points count
        points_response = requests.get("http://localhost:6333/collections/knowledge_chunks")
        if points_response.status_code == 200:
            points_data = points_response.json()
            print(f"   Total Points: {points_data.get('points_count', 'N/A')}")
    
    # Get sample points
    print("\n📋 Sample Vector Points:")
    print("-" * 40)
    
    points_data = get_qdrant_points(5)
    if points_data and 'result' in points_data:
        points = points_data['result']['points']
        
        for i, point in enumerate(points, 1):
            print(f"\n   Point #{i}")
            print(f"   ID: {point.get('id', 'N/A')}")
            
            payload = point.get('payload', {})
            print(f"   Knowledge ID: {payload.get('knowledge_id', 'N/A')}")
            print(f"   Chunk Index: {payload.get('chunk_index', 'N/A')}")
            print(f"   Content Hash: {payload.get('content_hash', 'N/A')}")
            print(f"   Machine ID: {payload.get('machine_id', 'N/A')}")
            
            # Show content preview
            content = payload.get('content', '')
            if content:
                preview = content[:100] + "..." if len(content) > 100 else content
                print(f"   Content Preview: {preview}")
    
    # Compare with database chunks
    print("\n🔄 Database vs Qdrant Comparison:")
    print("-" * 40)
    
    db_chunks = get_database_chunks_for_comparison()
    if db_chunks:
        print(f"   Database chunks found: {len(db_chunks)}")
        
        for chunk in db_chunks[:3]:  # Show first 3
            print(f"\n   DB Chunk ID: {chunk['id']}")
            print(f"   Knowledge ID: {chunk['knowledge_id']}")
            print(f"   Chunk Index: {chunk['chunk_index']}")
            print(f"   Filename: {chunk['filename']}")
            
            # Check if this chunk exists in Qdrant
            qdrant_id = f"{chunk['knowledge_id']}_{chunk['chunk_index']}"
            print(f"   Expected Qdrant ID: {qdrant_id}")
    
    print("\n" + "=" * 60)
    print("💡 Key Insights:")
    print("   • Vectors are stored in Qdrant with metadata linking to database chunks")
    print("   • Each vector point has a unique ID format: knowledge_id_chunk_index")
    print("   • Content is stored in both PostgreSQL (full text) and Qdrant (metadata)")
    print("   • Vector embeddings are stored separately in Qdrant's vector storage")

if __name__ == "__main__":
    main() 