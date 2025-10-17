#!/usr/bin/env python3
"""Simple test client for the MCP server."""

import httpx
import json
import time
import sys

def test_server():
    """Test the MCP server endpoints."""
    base_url = "http://localhost:8080"
    
    print("🔍 Testing RAG-Fusion MCP Server...")
    
    # Test health endpoint
    try:
        with httpx.Client() as client:
            health_response = client.get(f"{base_url}/health", timeout=10.0)
            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"✅ Health check passed!")
                print(f"   Status: {health_data.get('status')}")
                print(f"   Version: {health_data.get('version')}")
                print(f"   Uptime: {health_data.get('uptime_seconds')} seconds")
            else:
                print(f"❌ Health check failed: {health_response.status_code}")
                return False
    except httpx.ConnectError:
        print("❌ Cannot connect to server. Is it running on port 8080?")
        return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test search endpoint
    try:
        search_payload = {
            "query": "What is CI360 and how does it work?",
            "top_k": 5,
            "include_examples": False,
            "min_confidence": 0.0
        }
        
        with httpx.Client() as client:
            search_response = client.post(
                f"{base_url}/mcp/search_manual",
                json=search_payload,
                timeout=30.0
            )
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                print(f"\n🔍 Search test passed!")
                print(f"   Query: {search_payload['query']}")
                print(f"   Results: {len(search_data.get('chunks', []))} chunks found")
                print(f"   Intent: {search_data.get('metadata', {}).get('intent', 'unknown')}")
                
                # Show first result
                chunks = search_data.get('chunks', [])
                if chunks:
                    first_chunk = chunks[0]
                    print(f"\n📄 First result:")
                    print(f"   Document: {first_chunk.get('document_id', 'unknown')}")
                    print(f"   Page: {first_chunk.get('page', 'unknown')}")
                    print(f"   Score: {first_chunk.get('score', 'unknown')}")
                    print(f"   Text: {first_chunk.get('text', '')[:200]}...")
                
                # Show context
                context = search_data.get('context', '')
                if context:
                    print(f"\n📝 Generated context:")
                    print(f"   {context[:300]}...")
                
            else:
                print(f"❌ Search test failed: {search_response.status_code}")
                print(f"   Response: {search_response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Search test error: {e}")
        return False
    
    print(f"\n✅ All tests passed! MCP server is working correctly.")
    return True

def test_multiple_queries():
    """Test multiple different queries to showcase RAG-Fusion capabilities."""
    base_url = "http://localhost:8080"
    
    test_queries = [
        "How do I create a campaign in CI360?",
        "What are the system requirements for CI360?",
        "Explain CI360 data integration features",
        "How to troubleshoot CI360 performance issues?",
        "What are CI360 security features?"
    ]
    
    print(f"\n🚀 Testing multiple queries to showcase RAG-Fusion...")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Query {i}/5: {query} ---")
        try:
            search_payload = {
                "query": query,
                "top_k": 3,
                "include_examples": False,
                "min_confidence": 0.0
            }
            
            with httpx.Client() as client:
                response = client.post(
                    f"{base_url}/mcp/search_manual",
                    json=search_payload,
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    chunks = data.get('chunks', [])
                    intent = data.get('metadata', {}).get('intent', 'unknown')
                    
                    print(f"   ✅ Found {len(chunks)} results (intent: {intent})")
                    for j, chunk in enumerate(chunks[:2], 1):
                        print(f"      {j}. Page {chunk.get('page', '?')}: {chunk.get('text', '')[:100]}...")
                else:
                    print(f"   ❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        time.sleep(0.5)  # Small delay between requests

if __name__ == "__main__":
    success = test_server()
    if success and len(sys.argv) > 1 and sys.argv[1] == "--extended":
        test_multiple_queries()