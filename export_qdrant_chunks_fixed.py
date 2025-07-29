#!/usr/bin/env python3
"""
Export complete chunk content from Qdrant database - Fixed Version
"""

import requests
import json
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime

def get_all_qdrant_points():
    """Get all points from Qdrant with full payload"""
    
    try:
        # First, get the total count
        count_response = requests.get("http://localhost:6333/collections/knowledge_chunks")
        if count_response.status_code != 200:
            print(f"❌ Failed to get collection info: {count_response.status_code}")
            return None
        
        collection_info = count_response.json()
        total_points = collection_info.get('result', {}).get('points_count', 0)
        print(f"📊 Total points in Qdrant: {total_points}")
        
        if total_points == 0:
            print("❌ No points found in Qdrant!")
            return None
        
        # Get all points with full payload
        payload = {
            "limit": total_points,
            "with_payload": True,
            "with_vector": False  # Exclude vectors to keep output manageable
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
    """Get all chunk data from database for comparison"""
    
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
            kc.embedding,
            kc.metadata,
            k.filename,
            k.status,
            k.machine_id
        FROM knowledge_chunks kc
        JOIN knowledge k ON kc.knowledge_id = k.id
        ORDER BY kc.knowledge_id, kc.chunk_index
    """)
    
    chunks = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return chunks

def export_qdrant_chunks_to_file(output_file="qdrant_chunks_export.json"):
    """Export all Qdrant chunks to a JSON file"""
    
    print("🔍 Exporting Qdrant chunks...")
    
    # Get Qdrant points
    qdrant_data = get_all_qdrant_points()
    if not qdrant_data or 'result' not in qdrant_data:
        print("❌ No Qdrant data found!")
        return
    
    points = qdrant_data['result']['points']
    print(f"📋 Found {len(points)} points in Qdrant")
    
    # Get database chunks for comparison
    db_chunks = get_database_chunks_for_comparison()
    print(f"📋 Found {len(db_chunks)} chunks in database")
    
    # Create export data
    export_data = {
        "export_timestamp": datetime.now().isoformat(),
        "total_qdrant_points": len(points),
        "total_db_chunks": len(db_chunks),
        "qdrant_points": [],
        "database_chunks": [],
        "comparison": {
            "matching_chunks": 0,
            "missing_in_qdrant": 0,
            "missing_in_db": 0
        }
    }
    
    # Process Qdrant points
    for point in points:
        payload = point.get('payload', {})
        point_data = {
            "qdrant_id": point.get('id'),
            "knowledge_id": payload.get('knowledge_id'),
            "chunk_index": payload.get('chunk_index'),
            "text": payload.get('text', ''),
            "metadata": payload.get('metadata', {}),
            "text_length": len(payload.get('text', ''))
        }
        export_data["qdrant_points"].append(point_data)
    
    # Process database chunks
    for chunk in db_chunks:
        chunk_data = {
            "db_id": chunk['id'],
            "knowledge_id": chunk['knowledge_id'],
            "chunk_index": chunk['chunk_index'],
            "chunk_text": chunk['chunk_text'],
            "metadata": chunk['metadata'],
            "filename": chunk['filename'],
            "status": chunk['status'],
            "machine_id": chunk['machine_id'],
            "text_length": len(chunk['chunk_text'])
        }
        export_data["database_chunks"].append(chunk_data)
    
    # Compare Qdrant and Database
    qdrant_ids = set()
    for point in points:
        payload = point.get('payload', {})
        knowledge_id = payload.get('knowledge_id')
        chunk_index = payload.get('chunk_index')
        if knowledge_id is not None and chunk_index is not None:
            qdrant_ids.add(f"{knowledge_id}_{chunk_index}")
    
    db_ids = set()
    for chunk in db_chunks:
        db_ids.add(f"{chunk['knowledge_id']}_{chunk['chunk_index']}")
    
    export_data["comparison"]["matching_chunks"] = len(qdrant_ids.intersection(db_ids))
    export_data["comparison"]["missing_in_qdrant"] = len(db_ids - qdrant_ids)
    export_data["comparison"]["missing_in_db"] = len(qdrant_ids - db_ids)
    
    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Exported to {output_file}")
    print(f"📊 Summary:")
    print(f"   • Qdrant points: {len(points)}")
    print(f"   • Database chunks: {len(db_chunks)}")
    print(f"   • Matching chunks: {export_data['comparison']['matching_chunks']}")
    print(f"   • Missing in Qdrant: {export_data['comparison']['missing_in_qdrant']}")
    print(f"   • Missing in DB: {export_data['comparison']['missing_in_db']}")

def display_qdrant_chunks_interactive():
    """Display Qdrant chunks in an interactive format"""
    
    print("🔍 Interactive Qdrant Chunks Viewer")
    print("=" * 60)
    
    # Get Qdrant points
    qdrant_data = get_all_qdrant_points()
    if not qdrant_data or 'result' not in qdrant_data:
        print("❌ No Qdrant data found!")
        return
    
    points = qdrant_data['result']['points']
    print(f"📋 Found {len(points)} points in Qdrant")
    
    while True:
        print("\nOptions:")
        print("1. Show all Qdrant points (summary)")
        print("2. Show specific point details")
        print("3. Search points by knowledge_id")
        print("4. Export to file")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            print("\n📋 All Qdrant Points Summary:")
            print("-" * 50)
            for i, point in enumerate(points[:20], 1):  # Show first 20
                payload = point.get('payload', {})
                print(f"   {i}. ID: {point.get('id')}")
                print(f"      Knowledge ID: {payload.get('knowledge_id')}")
                print(f"      Chunk Index: {payload.get('chunk_index')}")
                print(f"      Content Length: {len(payload.get('text', ''))}")
                print()
            
            if len(points) > 20:
                print(f"   ... and {len(points) - 20} more points")
        
        elif choice == "2":
            point_id = input("Enter point ID: ").strip()
            try:
                point_id = int(point_id)
                point = next((p for p in points if p.get('id') == point_id), None)
                if point:
                    print(f"\n🔍 Point {point_id} Details:")
                    print("-" * 40)
                    payload = point.get('payload', {})
                    print(f"   ID: {point.get('id')}")
                    print(f"   Knowledge ID: {payload.get('knowledge_id')}")
                    print(f"   Chunk Index: {payload.get('chunk_index')}")
                    print(f"   Content Length: {len(payload.get('text', ''))}")
                    
                    content = payload.get('text', '')
                    if content:
                        print(f"   Content Preview:")
                        preview = content[:500] + "..." if len(content) > 500 else content
                        print(f"   {preview}")
                else:
                    print(f"❌ Point {point_id} not found!")
            except ValueError:
                print("❌ Invalid point ID!")
        
        elif choice == "3":
            knowledge_id = input("Enter knowledge_id: ").strip()
            try:
                knowledge_id = int(knowledge_id)
                matching_points = [p for p in points if p.get('payload', {}).get('knowledge_id') == knowledge_id]
                print(f"\n📋 Points for Knowledge ID {knowledge_id}:")
                print("-" * 40)
                for point in matching_points:
                    payload = point.get('payload', {})
                    print(f"   Point ID: {point.get('id')}")
                    print(f"   Chunk Index: {payload.get('chunk_index')}")
                    print(f"   Content Length: {len(payload.get('text', ''))}")
                    print()
            except ValueError:
                print("❌ Invalid knowledge_id!")
        
        elif choice == "4":
            filename = input("Enter filename (default: qdrant_chunks_export.json): ").strip()
            if not filename:
                filename = "qdrant_chunks_export.json"
            export_qdrant_chunks_to_file(filename)
        
        elif choice == "5":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice!")

def main():
    """Main function"""
    
    print("🔍 Qdrant Chunks Export Tool (Fixed)")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. Interactive viewer")
        print("2. Export to JSON file")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            display_qdrant_chunks_interactive()
        
        elif choice == "2":
            filename = input("Enter filename (default: qdrant_chunks_export.json): ").strip()
            if not filename:
                filename = "qdrant_chunks_export.json"
            export_qdrant_chunks_to_file(filename)
        
        elif choice == "3":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice!")

if __name__ == "__main__":
    main() 