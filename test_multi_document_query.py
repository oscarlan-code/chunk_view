#!/usr/bin/env python3
"""
Test script to demonstrate multi-document query functionality
"""

import requests
import json

def test_multi_document_query():
    """Test the multi-document query functionality"""
    
    # Test query
    query_data = {
        "query": "How do I troubleshoot the machine?",
        "machine_id": 3  # Using existing machine ID
    }
    
    print("🔍 Testing Multi-Document Query System")
    print("=" * 50)
    
    try:
        # Test the machine-specific query endpoint
        response = requests.post(
            "http://localhost:8000/query/machine",
            json=query_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Query successful!")
            print(f"📊 Response: {result['response'][:200]}...")
            print(f"📚 Documents available: {result['documents_available']}")
            print(f"⏱️ Processing time: {result['processing_time']:.2f}s")
            print(f"🎯 Source: {result['source']}")
            
            if result['source_documents']:
                print(f"📄 Source documents: {len(result['source_documents'])} found")
                for i, doc in enumerate(result['source_documents'][:3]):
                    print(f"   {i+1}. {doc[:100]}...")
        else:
            print(f"❌ Query failed with status {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing query: {e}")

def test_chat_endpoint():
    """Test the chat endpoint with multi-document retrieval"""
    
    print("\n💬 Testing Chat Endpoint")
    print("=" * 30)
    
    try:
        # Test the chat endpoint
        chat_data = {
            "query": "What maintenance procedures are available?",
            "machine_id": 3
        }
        
        response = requests.post(
            "http://localhost:8000/chat",
            data=chat_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Chat query successful!")
            print(f"📊 Response: {result['response'][:200]}...")
            print(f"📚 Documents available: {result['documents_available']}")
            print(f"🎯 Source: {result['source']}")
        else:
            print(f"❌ Chat query failed with status {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing chat: {e}")

if __name__ == "__main__":
    test_multi_document_query()
    test_chat_endpoint() 