#!/usr/bin/env python3
"""Simple test to check server startup without full uvicorn."""

import logging
from server.mcp_handlers import build_state

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def test_server_state():
    """Test building the server state."""
    import os
    config = dict(os.environ)
    config["INDEX_DIR"] = "data/indexes"
    config["CACHE_SIZE"] = "100"
    
    try:
        state = build_state(config)
        print(f"✅ Server state built successfully!")
        print(f"📊 Index version: {state.index_version}")
        print(f"🔍 Retriever loaded: {state.retriever is not None}")
        print(f"🔄 Reranker loaded: {state.reranker is not None}")
        print(f"🎯 Router loaded: {state.router is not None}")
        print(f"📝 Synthesizer loaded: {state.synthesizer is not None}")
        
        # Test a simple retrieval
        try:
            results = state.retriever.retrieve("CI360 manual", "fact", 5)
            print(f"🔍 Sample retrieval works: {len(results)} results")
            if results:
                print(f"   First result: {results[0].text[:100]}...")
        except Exception as e:
            print(f"❌ Retrieval test failed: {e}")
            
    except Exception as e:
        print(f"❌ Server state build failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_server_state()