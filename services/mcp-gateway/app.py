"""MCP Gateway Service - Model Context Protocol Interface.

This service provides:
- MCP JSON-RPC 2.0 protocol compliance
- Tool/Resource/Prompt registration
- Request proxying to Retrieval Service
- Error handling and protocol translation
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [MCPGateway] %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
RETRIEVAL_SERVICE_URL = os.getenv("RETRIEVAL_SERVICE_URL", "http://retrieval-service:8081")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

APP_START_TIME = time.time()

# FastAPI app
app = FastAPI(
    title="MCP Gateway Service",
    description="Model Context Protocol gateway for RAG-Fusion system",
    version="1.0.0",
)

# HTTP client for retrieval service
http_client: Optional[httpx.AsyncClient] = None


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize HTTP client."""
    global http_client
    
    logger.info("Starting MCP Gateway Service...")
    logger.info(f"Retrieval Service URL: {RETRIEVAL_SERVICE_URL}")
    logger.info(f"Request timeout: {REQUEST_TIMEOUT}s")
    
    # Create async HTTP client with retries
    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(REQUEST_TIMEOUT),
        limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
    )
    
    # Test connection to retrieval service
    try:
        response = await http_client.get(f"{RETRIEVAL_SERVICE_URL}/health")
        if response.status_code == 200:
            logger.info("✓ Connected to Retrieval Service")
        else:
            logger.warning(f"Retrieval Service health check returned {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to connect to Retrieval Service: {e}")
        logger.warning("MCP Gateway will continue but may not function properly")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Close HTTP client."""
    global http_client
    if http_client:
        await http_client.aclose()
        logger.info("HTTP client closed")


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    uptime = int(time.time() - APP_START_TIME)
    
    # Check retrieval service connectivity
    retrieval_healthy = False
    try:
        if http_client:
            response = await http_client.get(f"{RETRIEVAL_SERVICE_URL}/health", timeout=2.0)
            retrieval_healthy = response.status_code == 200
    except Exception as e:
        logger.warning(f"Health check failed for retrieval service: {e}")
    
    status = "healthy" if retrieval_healthy else "degraded"
    
    return {
        "status": status,
        "service": "mcp-gateway",
        "version": "1.0.0",
        "uptime_seconds": uptime,
        "retrieval_service_healthy": retrieval_healthy,
    }


@app.post("/mcp")
async def mcp_endpoint(request: Request) -> JSONResponse:
    """
    Main MCP JSON-RPC 2.0 endpoint.
    
    Handles:
    - initialize
    - tools/list
    - tools/call
    - resources/list
    - prompts/list
    """
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=400,
            content={"error": "invalid_request", "message": "Invalid JSON"},
        )
    
    # Extract JSON-RPC fields
    jsonrpc = body.get("jsonrpc")
    method = body.get("method")
    params = body.get("params", {})
    request_id = body.get("id")
    
    # Validate JSON-RPC 2.0
    if jsonrpc != "2.0":
        return JSONResponse(
            status_code=400,
            content={"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}, "id": request_id},
        )
    
    logger.info(f"MCP request: {method} (id={request_id})")
    
    try:
        # Route to appropriate handler
        if method == "initialize":
            result = await handle_initialize(params)
        elif method == "tools/list":
            result = await handle_tools_list(params)
        elif method == "tools/call":
            result = await handle_tools_call(params)
        elif method == "resources/list":
            result = await handle_resources_list(params)
        elif method == "prompts/list":
            result = await handle_prompts_list(params)
        else:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                    "id": request_id,
                }
            )
        
        return JSONResponse(
            content={"jsonrpc": "2.0", "result": result, "id": request_id}
        )
        
    except Exception as e:
        logger.error(f"Error handling {method}: {e}", exc_info=True)
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
                "id": request_id,
            }
        )


async def handle_initialize(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP initialize request."""
    logger.info(f"Initialize request from: {params.get('clientInfo', {}).get('name', 'unknown')}")
    
    return {
        "protocolVersion": "2024-11-05",
        "serverInfo": {
            "name": "rag-fusion-mcp-server",
            "version": "1.0.0",
        },
        "capabilities": {
            "tools": {"listChanged": False},
            "resources": {"subscribe": False, "listChanged": False},
            "prompts": {"listChanged": False},
        },
    }


async def handle_tools_list(params: Dict[str, Any]) -> Dict[str, Any]:
    """List available MCP tools."""
    tools = [
        {
            "name": "search_manual",
            "description": "Search the CI360 manual using RAG-Fusion multi-strategy retrieval",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query or question",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return (1-50)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50,
                    },
                    "min_confidence": {
                        "type": "number",
                        "description": "Minimum confidence score (0.0-1.0)",
                        "default": 0.0,
                        "minimum": 0.0,
                        "maximum": 1.0,
                    },
                },
                "required": ["query"],
            },
        },
        {
            "name": "get_chunk_details",
            "description": "Get detailed information about a specific chunk by ID",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "chunk_id": {
                        "type": "string",
                        "description": "Unique chunk identifier",
                    },
                },
                "required": ["chunk_id"],
            },
        },
    ]
    
    return {"tools": tools}


async def handle_tools_call(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute an MCP tool by proxying to retrieval service."""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    
    logger.info(f"Tool call: {tool_name} with args: {arguments}")
    
    if tool_name == "search_manual":
        return await call_search_manual(arguments)
    elif tool_name == "get_chunk_details":
        return await call_get_chunk_details(arguments)
    else:
        raise ValueError(f"Unknown tool: {tool_name}")


async def call_search_manual(args: Dict[str, Any]) -> Dict[str, Any]:
    """Call search_manual tool via retrieval service."""
    if not http_client:
        raise RuntimeError("HTTP client not initialized")
    
    query = args.get("query")
    if not query:
        raise ValueError("Missing required argument: query")
    
    top_k = args.get("top_k", 10)
    min_confidence = args.get("min_confidence", 0.0)
    
    # Call retrieval service
    retrieval_request = {
        "query": query,
        "top_k": top_k,
        "intent": None,
        "include_context": True,
        "min_confidence": min_confidence,
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = await http_client.post(
                f"{RETRIEVAL_SERVICE_URL}/retrieve",
                json=retrieval_request,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            result = response.json()
            
            # Format for MCP tool response
            chunks = result.get("chunks", [])
            context = result.get("context", "")
            metadata = result.get("metadata", {})
            
            # Build response text
            response_text = f"**Search Results for:** {query}\n\n"
            if context:
                response_text += f"{context}\n\n"
            
            response_text += f"**Found {len(chunks)} relevant chunks**\n"
            response_text += f"**Retrieval time:** {metadata.get('retrieval_time_ms', 0)}ms\n\n"
            
            for i, chunk in enumerate(chunks, 1):
                response_text += f"### Result {i} (score: {chunk['score']:.3f})\n"
                response_text += f"**Source:** {chunk['source']}\n"
                response_text += f"{chunk['text'][:500]}...\n\n"
            
            return {
                "content": [{"type": "text", "text": response_text}],
                "isError": False,
            }
            
        except httpx.TimeoutException:
            logger.warning(f"Timeout on attempt {attempt + 1}/{MAX_RETRIES}")
            if attempt == MAX_RETRIES - 1:
                raise
            await asyncio.sleep(1)
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from retrieval service: {e.response.status_code}")
            raise
        
        except Exception as e:
            logger.error(f"Unexpected error calling retrieval service: {e}")
            raise


async def call_get_chunk_details(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get chunk details (placeholder)."""
    chunk_id = args.get("chunk_id")
    if not chunk_id:
        raise ValueError("Missing required argument: chunk_id")
    
    # TODO: Implement chunk detail retrieval from retrieval service
    return {
        "content": [{"type": "text", "text": f"Chunk details for {chunk_id} (not implemented)"}],
        "isError": False,
    }


async def handle_resources_list(params: Dict[str, Any]) -> Dict[str, Any]:
    """List available MCP resources."""
    return {"resources": []}  # No resources for now


async def handle_prompts_list(params: Dict[str, Any]) -> Dict[str, Any]:
    """List available MCP prompts."""
    prompts = [
        {
            "name": "summarize_topic",
            "description": "Generate a summary of a specific topic from the manual",
            "arguments": [
                {
                    "name": "topic",
                    "description": "Topic to summarize",
                    "required": True,
                },
            ],
        },
    ]
    
    return {"prompts": prompts}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True,
    )
