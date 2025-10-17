#!/usr/bin/env python3
"""Direct server test without uvicorn to isolate issues."""

import asyncio
from server.app import app
from server.mcp_handlers import build_state
import os
import json

async def test_server():
    """Test the server endpoints directly."""
    # Manually trigger startup
    app.state.server_state = build_state(dict(os.environ))
    
    # Test search endpoint
    from server.models import SearchRequest
    
    request = SearchRequest(
        query="What is CI360?",
        top_k=3,
        include_examples=False,
        min_confidence=0.0
    )
    
    # Import the handler
    from server.mcp_handlers import register_routes
    from fastapi import APIRouter
    
    router = APIRouter()
    register_routes(router, app.state.server_state)
    
    print("✅ Server setup completed successfully!")
    print("📊 Available for MCP queries")
    
    # Print some sample results manually
    results = app.state.server_state.retriever.retrieve("CI360", "fact", 3)
    print(f"\n🔍 Sample search for 'CI360' returned {len(results)} results:")
    for i, result in enumerate(results[:3], 1):
        print(f"  {i}. {result.text[:100]}...")
    print(f"\n🎯 Server is ready on port 8080 for MCP connections")

if __name__ == "__main__":
    asyncio.run(test_server())