#!/usr/bin/env python3
"""Production MCP server runner."""

import uvicorn
import logging
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

def main():
    """Run the MCP server in production mode."""
    # Set environment variables
    os.environ.setdefault("INDEX_DIR", str(Path("data/indexes").absolute()))
    os.environ.setdefault("CACHE_SIZE", "1000")
    os.environ.setdefault("LOG_LEVEL", "INFO")
    
    print("🚀 Starting RAG-Fusion MCP Server...")
    print(f"📁 Index directory: {os.environ['INDEX_DIR']}")
    print(f"💾 Cache size: {os.environ['CACHE_SIZE']}")
    print(f"🔗 Server URL: http://localhost:8080")
    print(f"🩺 Health endpoint: http://localhost:8080/health")
    print(f"🔍 Search endpoint: http://localhost:8080/mcp/search_manual")
    print("Press Ctrl+C to stop the server")
    
    try:
        uvicorn.run(
            "server.app:app",
            host="0.0.0.0",
            port=8080,
            reload=False,
            log_level="info",
            access_log=True,
        )
    except KeyboardInterrupt:
        print("\n👋 Server shutting down...")

if __name__ == "__main__":
    main()