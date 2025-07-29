#!/usr/bin/env python3
"""
Cleanup script to purge old Qdrant data and ensure fresh start with correct embedding model
"""

import qdrant_client
from qdrant_client import models
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
COLLECTION_NAME = "knowledge_chunks"
EMBEDDING_SIZE = 1024

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "upskill")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

def get_db_conn():
    """Get database connection"""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def cleanup_qdrant():
    """Clean up Qdrant collections"""
    print("🧹 Cleaning up Qdrant collections...")
    
    client = qdrant_client.QdrantClient(host='localhost', port=6333)
    
    # Get all collections
    collections = client.get_collections()
    print(f"📋 Found {len(collections.collections)} collections:")
    
    for collection in collections.collections:
        print(f"  - {collection.name}")
        
        # Delete collections that don't match our expected configuration
        if collection.name != COLLECTION_NAME:
            print(f"🗑️ Deleting old collection: {collection.name}")
            try:
                client.delete_collection(collection.name)
                print(f"✅ Deleted {collection.name}")
            except Exception as e:
                print(f"❌ Error deleting {collection.name}: {e}")
    
    # Ensure our target collection exists with correct dimensions
    try:
        # Check if our collection exists
        collection_info = client.get_collection(COLLECTION_NAME)
        print(f"✅ Collection {COLLECTION_NAME} exists")
        
        # Get collection info to check dimensions
        try:
            # Try to get collection info
            info = client.get_collection(COLLECTION_NAME)
            print(f"📊 Collection info: {info}")
            
            # Check if we can get vector params
            if hasattr(info, 'config') and hasattr(info.config, 'params') and hasattr(info.config.params, 'vectors'):
                vectors_config = info.config.params.vectors
                if hasattr(vectors_config, 'size'):
                    size = vectors_config.size
                    if size != EMBEDDING_SIZE:
                        print(f"⚠️ Collection has wrong size: {size} != {EMBEDDING_SIZE}")
                        print(f"🗑️ Recreating collection {COLLECTION_NAME}...")
                        client.delete_collection(COLLECTION_NAME)
                        client.create_collection(
                            collection_name=COLLECTION_NAME,
                            vectors_config=models.VectorParams(
                                size=EMBEDDING_SIZE,
                                distance=models.Distance.COSINE
                            )
                        )
                        print(f"✅ Recreated collection {COLLECTION_NAME} with {EMBEDDING_SIZE} dimensions")
                    else:
                        print(f"✅ Collection {COLLECTION_NAME} has correct dimensions")
                else:
                    print(f"⚠️ Collection {COLLECTION_NAME} has no size info, recreating...")
                    client.delete_collection(COLLECTION_NAME)
                    client.create_collection(
                        collection_name=COLLECTION_NAME,
                        vectors_config=models.VectorParams(
                            size=EMBEDDING_SIZE,
                            distance=models.Distance.COSINE
                        )
                    )
                    print(f"✅ Recreated collection {COLLECTION_NAME} with {EMBEDDING_SIZE} dimensions")
            else:
                print(f"⚠️ Collection {COLLECTION_NAME} has no vector config, recreating...")
                client.delete_collection(COLLECTION_NAME)
                client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=models.VectorParams(
                        size=EMBEDDING_SIZE,
                        distance=models.Distance.COSINE
                    )
                )
                print(f"✅ Recreated collection {COLLECTION_NAME} with {EMBEDDING_SIZE} dimensions")
                
        except Exception as e:
            print(f"❌ Error checking collection {COLLECTION_NAME}: {e}")
            print(f"🗑️ Creating collection {COLLECTION_NAME}...")
            try:
                client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=models.VectorParams(
                        size=EMBEDDING_SIZE,
                        distance=models.Distance.COSINE
                    )
                )
                print(f"✅ Created collection {COLLECTION_NAME} with {EMBEDDING_SIZE} dimensions")
            except Exception as e2:
                print(f"❌ Error creating collection: {e2}")
            
    except Exception as e:
        print(f"❌ Error checking collection {COLLECTION_NAME}: {e}")
        print(f"🗑️ Creating collection {COLLECTION_NAME}...")
        try:
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=EMBEDDING_SIZE,
                    distance=models.Distance.COSINE
                )
            )
            print(f"✅ Created collection {COLLECTION_NAME} with {EMBEDDING_SIZE} dimensions")
        except Exception as e2:
            print(f"❌ Error creating collection: {e2}")

def cleanup_database():
    """Clean up database chunks"""
    print("🧹 Cleaning up database chunks...")
    
    try:
        conn = get_db_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Count existing chunks
        cursor.execute("SELECT COUNT(*) as count FROM knowledge_chunks")
        result = cursor.fetchone()
        old_count = result['count'] if result else 0
        print(f"📊 Found {old_count} existing chunks in database")
        
        if old_count > 0:
            # Delete all chunks
            cursor.execute("DELETE FROM knowledge_chunks")
            conn.commit()
            print(f"🗑️ Deleted {old_count} chunks from database")
        
        cursor.close()
        conn.close()
        print("✅ Database cleanup completed")
        
    except Exception as e:
        print(f"❌ Error cleaning database: {e}")

def main():
    """Main cleanup function"""
    print("🚀 Starting cleanup process...")
    
    cleanup_qdrant()
    cleanup_database()
    
    print("✅ Cleanup completed successfully!")
    print("📝 Next steps:")
    print("  1. Restart the backend server")
    print("  2. Re-upload documents from the frontend")
    print("  3. Test the RAG system")

if __name__ == "__main__":
    main() 