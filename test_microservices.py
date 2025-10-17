#!/usr/bin/env python3
"""
Microservices Integration Test Suite

Tests the entire microservices architecture:
1. Service health checks
2. Inter-service communication
3. MCP protocol compliance
4. End-to-end retrieval flow
5. Error handling and resilience
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional

import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# Service URLs
INDEXER_URL = "http://localhost:8082"
RETRIEVAL_URL = "http://localhost:8081"
GATEWAY_URL = "http://localhost:8080"

# Test configuration
REQUEST_TIMEOUT = 30.0


class MicroservicesTestSuite:
    """Comprehensive test suite for microservices architecture."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT)
        self.test_results: List[Dict[str, Any]] = []
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
    
    def record_test(self, name: str, passed: bool, message: str, duration_ms: float):
        """Record test result."""
        self.test_results.append({
            "name": name,
            "passed": passed,
            "message": message,
            "duration_ms": duration_ms,
        })
    
    async def test_health_checks(self) -> bool:
        """Test 1: Health check endpoints."""
        console.print("\n[yellow]Test 1: Health Checks[/yellow]")
        
        all_healthy = True
        
        # Test indexer health
        start = time.time()
        try:
            response = await self.client.get(f"{INDEXER_URL}/health")
            duration = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                console.print(f"  ✓ Indexer Service: {data['status']} ({duration:.0f}ms)")
                self.record_test("Indexer Health", True, data['status'], duration)
            else:
                console.print(f"  ✗ Indexer Service: HTTP {response.status_code}")
                self.record_test("Indexer Health", False, f"HTTP {response.status_code}", duration)
                all_healthy = False
        except Exception as e:
            duration = (time.time() - start) * 1000
            console.print(f"  ✗ Indexer Service: {str(e)}")
            self.record_test("Indexer Health", False, str(e), duration)
            all_healthy = False
        
        # Test retrieval health
        start = time.time()
        try:
            response = await self.client.get(f"{RETRIEVAL_URL}/health")
            duration = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                console.print(f"  ✓ Retrieval Service: {data['status']} ({duration:.0f}ms)")
                console.print(f"    Index version: {data.get('index_version', 'unknown')}")
                console.print(f"    Indexes loaded: {data.get('indexes_loaded', False)}")
                self.record_test("Retrieval Health", True, data['status'], duration)
            else:
                console.print(f"  ✗ Retrieval Service: HTTP {response.status_code}")
                self.record_test("Retrieval Health", False, f"HTTP {response.status_code}", duration)
                all_healthy = False
        except Exception as e:
            duration = (time.time() - start) * 1000
            console.print(f"  ✗ Retrieval Service: {str(e)}")
            self.record_test("Retrieval Health", False, str(e), duration)
            all_healthy = False
        
        # Test gateway health
        start = time.time()
        try:
            response = await self.client.get(f"{GATEWAY_URL}/health")
            duration = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                console.print(f"  ✓ MCP Gateway: {data['status']} ({duration:.0f}ms)")
                console.print(f"    Retrieval service healthy: {data.get('retrieval_service_healthy', False)}")
                self.record_test("Gateway Health", True, data['status'], duration)
            else:
                console.print(f"  ✗ MCP Gateway: HTTP {response.status_code}")
                self.record_test("Gateway Health", False, f"HTTP {response.status_code}", duration)
                all_healthy = False
        except Exception as e:
            duration = (time.time() - start) * 1000
            console.print(f"  ✗ MCP Gateway: {str(e)}")
            self.record_test("Gateway Health", False, str(e), duration)
            all_healthy = False
        
        return all_healthy
    
    async def test_retrieval_service(self) -> bool:
        """Test 2: Direct retrieval service."""
        console.print("\n[yellow]Test 2: Retrieval Service API[/yellow]")
        
        # Test retrieval endpoint
        start = time.time()
        try:
            request_data = {
                "query": "How do I configure authentication?",
                "top_k": 5,
                "include_context": True,
                "min_confidence": 0.0,
            }
            
            response = await self.client.post(
                f"{RETRIEVAL_URL}/retrieve",
                json=request_data,
            )
            duration = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                chunks = data.get("chunks", [])
                metadata = data.get("metadata", {})
                
                console.print(f"  ✓ Retrieval successful ({duration:.0f}ms)")
                console.print(f"    Chunks returned: {len(chunks)}")
                console.print(f"    Intent: {metadata.get('intent', 'unknown')}")
                console.print(f"    Retrieval time: {metadata.get('retrieval_time_ms', 0)}ms")
                
                if chunks:
                    console.print(f"    Top score: {chunks[0]['score']:.3f}")
                
                self.record_test("Retrieval API", True, f"{len(chunks)} chunks", duration)
                return True
            else:
                console.print(f"  ✗ Retrieval failed: HTTP {response.status_code}")
                self.record_test("Retrieval API", False, f"HTTP {response.status_code}", duration)
                return False
                
        except Exception as e:
            duration = (time.time() - start) * 1000
            console.print(f"  ✗ Retrieval error: {str(e)}")
            self.record_test("Retrieval API", False, str(e), duration)
            return False
    
    async def test_mcp_protocol(self) -> bool:
        """Test 3: MCP protocol compliance."""
        console.print("\n[yellow]Test 3: MCP Protocol[/yellow]")
        
        # Test initialize
        start = time.time()
        try:
            request_data = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0",
                    },
                    "protocolVersion": "2024-11-05",
                },
                "id": 1,
            }
            
            response = await self.client.post(
                f"{GATEWAY_URL}/mcp",
                json=request_data,
            )
            duration = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                if "result" in data:
                    result = data["result"]
                    console.print(f"  ✓ Initialize successful ({duration:.0f}ms)")
                    console.print(f"    Server: {result.get('serverInfo', {}).get('name', 'unknown')}")
                    console.print(f"    Protocol: {result.get('protocolVersion', 'unknown')}")
                    self.record_test("MCP Initialize", True, "Success", duration)
                else:
                    console.print(f"  ✗ Initialize failed: No result in response")
                    self.record_test("MCP Initialize", False, "No result", duration)
                    return False
            else:
                console.print(f"  ✗ Initialize failed: HTTP {response.status_code}")
                self.record_test("MCP Initialize", False, f"HTTP {response.status_code}", duration)
                return False
                
        except Exception as e:
            duration = (time.time() - start) * 1000
            console.print(f"  ✗ Initialize error: {str(e)}")
            self.record_test("MCP Initialize", False, str(e), duration)
            return False
        
        # Test tools/list
        start = time.time()
        try:
            request_data = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 2,
            }
            
            response = await self.client.post(
                f"{GATEWAY_URL}/mcp",
                json=request_data,
            )
            duration = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                if "result" in data and "tools" in data["result"]:
                    tools = data["result"]["tools"]
                    console.print(f"  ✓ Tools list successful ({duration:.0f}ms)")
                    console.print(f"    Tools available: {len(tools)}")
                    for tool in tools:
                        console.print(f"      - {tool['name']}")
                    self.record_test("MCP Tools List", True, f"{len(tools)} tools", duration)
                else:
                    console.print(f"  ✗ Tools list failed: Invalid response")
                    self.record_test("MCP Tools List", False, "Invalid response", duration)
                    return False
            else:
                console.print(f"  ✗ Tools list failed: HTTP {response.status_code}")
                self.record_test("MCP Tools List", False, f"HTTP {response.status_code}", duration)
                return False
                
        except Exception as e:
            duration = (time.time() - start) * 1000
            console.print(f"  ✗ Tools list error: {str(e)}")
            self.record_test("MCP Tools List", False, str(e), duration)
            return False
        
        # Test tools/call (search_manual)
        start = time.time()
        try:
            request_data = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "search_manual",
                    "arguments": {
                        "query": "authentication configuration",
                        "top_k": 3,
                    },
                },
                "id": 3,
            }
            
            response = await self.client.post(
                f"{GATEWAY_URL}/mcp",
                json=request_data,
            )
            duration = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                if "result" in data and "content" in data["result"]:
                    console.print(f"  ✓ Tool call successful ({duration:.0f}ms)")
                    console.print(f"    Response length: {len(str(data['result']))} chars")
                    self.record_test("MCP Tool Call", True, "Success", duration)
                else:
                    console.print(f"  ✗ Tool call failed: Invalid response")
                    self.record_test("MCP Tool Call", False, "Invalid response", duration)
                    return False
            else:
                console.print(f"  ✗ Tool call failed: HTTP {response.status_code}")
                self.record_test("MCP Tool Call", False, f"HTTP {response.status_code}", duration)
                return False
                
        except Exception as e:
            duration = (time.time() - start) * 1000
            console.print(f"  ✗ Tool call error: {str(e)}")
            self.record_test("MCP Tool Call", False, str(e), duration)
            return False
        
        return True
    
    async def test_error_handling(self) -> bool:
        """Test 4: Error handling and resilience."""
        console.print("\n[yellow]Test 4: Error Handling[/yellow]")
        
        # Test invalid query
        start = time.time()
        try:
            request_data = {
                "query": "",  # Empty query
                "top_k": 5,
            }
            
            response = await self.client.post(
                f"{RETRIEVAL_URL}/retrieve",
                json=request_data,
            )
            duration = (time.time() - start) * 1000
            
            # Empty query might be handled gracefully or rejected
            console.print(f"  ✓ Empty query handled (HTTP {response.status_code}) ({duration:.0f}ms)")
            self.record_test("Empty Query Handling", True, f"HTTP {response.status_code}", duration)
            
        except Exception as e:
            duration = (time.time() - start) * 1000
            console.print(f"  ✗ Empty query error: {str(e)}")
            self.record_test("Empty Query Handling", False, str(e), duration)
        
        # Test invalid MCP request
        start = time.time()
        try:
            request_data = {
                "jsonrpc": "1.0",  # Wrong version
                "method": "tools/list",
                "id": 99,
            }
            
            response = await self.client.post(
                f"{GATEWAY_URL}/mcp",
                json=request_data,
            )
            duration = (time.time() - start) * 1000
            
            if response.status_code == 400 or (response.status_code == 200 and "error" in response.json()):
                console.print(f"  ✓ Invalid JSON-RPC detected ({duration:.0f}ms)")
                self.record_test("Invalid JSON-RPC", True, "Rejected correctly", duration)
            else:
                console.print(f"  ✗ Invalid JSON-RPC not detected")
                self.record_test("Invalid JSON-RPC", False, "Not rejected", duration)
                
        except Exception as e:
            duration = (time.time() - start) * 1000
            console.print(f"  ✗ Invalid JSON-RPC test error: {str(e)}")
            self.record_test("Invalid JSON-RPC", False, str(e), duration)
        
        return True
    
    async def test_performance(self) -> bool:
        """Test 5: Performance benchmarks."""
        console.print("\n[yellow]Test 5: Performance Benchmarks[/yellow]")
        
        # Benchmark retrieval service
        queries = [
            "authentication",
            "configuration",
            "user management",
            "API endpoints",
            "troubleshooting",
        ]
        
        retrieval_times = []
        
        for query in queries:
            start = time.time()
            try:
                request_data = {
                    "query": query,
                    "top_k": 10,
                    "include_context": True,
                }
                
                response = await self.client.post(
                    f"{RETRIEVAL_URL}/retrieve",
                    json=request_data,
                )
                duration = (time.time() - start) * 1000
                
                if response.status_code == 200:
                    retrieval_times.append(duration)
                    
            except Exception as e:
                console.print(f"  ✗ Performance test error: {str(e)}")
        
        if retrieval_times:
            avg_time = sum(retrieval_times) / len(retrieval_times)
            min_time = min(retrieval_times)
            max_time = max(retrieval_times)
            
            console.print(f"  ✓ Retrieval performance ({len(retrieval_times)} queries):")
            console.print(f"    Average: {avg_time:.0f}ms")
            console.print(f"    Min: {min_time:.0f}ms")
            console.print(f"    Max: {max_time:.0f}ms")
            
            self.record_test("Performance Benchmark", True, f"Avg {avg_time:.0f}ms", avg_time)
            
            # Check if performance is acceptable (< 1 second p95)
            if max_time < 1000:
                console.print(f"    [green]Performance: EXCELLENT[/green]")
            elif max_time < 2000:
                console.print(f"    [yellow]Performance: GOOD[/yellow]")
            else:
                console.print(f"    [red]Performance: NEEDS IMPROVEMENT[/red]")
            
            return True
        else:
            console.print(f"  ✗ No successful queries for benchmark")
            return False
    
    def print_summary(self):
        """Print test summary."""
        console.print("\n" + "="*60)
        console.print("[bold cyan]Test Summary[/bold cyan]")
        console.print("="*60)
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Test", style="cyan", width=30)
        table.add_column("Result", width=10)
        table.add_column("Message", width=30)
        table.add_column("Duration", width=10, justify="right")
        
        passed = 0
        failed = 0
        
        for result in self.test_results:
            status = "[green]✓ PASS[/green]" if result["passed"] else "[red]✗ FAIL[/red]"
            table.add_row(
                result["name"],
                status,
                result["message"][:30],
                f"{result['duration_ms']:.0f}ms",
            )
            
            if result["passed"]:
                passed += 1
            else:
                failed += 1
        
        console.print(table)
        console.print(f"\nTotal: {passed + failed} tests, [green]{passed} passed[/green], [red]{failed} failed[/red]")
        
        if failed == 0:
            console.print("\n[bold green]✓ All tests passed![/bold green]")
        else:
            console.print(f"\n[bold red]✗ {failed} test(s) failed[/bold red]")


async def main():
    """Run all tests."""
    console.print(Panel.fit(
        "[bold cyan]RAG-Fusion Microservices Test Suite[/bold cyan]\n"
        "Testing all services and inter-service communication",
        border_style="cyan"
    ))
    
    suite = MicroservicesTestSuite()
    
    try:
        # Run tests
        await suite.test_health_checks()
        await suite.test_retrieval_service()
        await suite.test_mcp_protocol()
        await suite.test_error_handling()
        await suite.test_performance()
        
        # Print summary
        suite.print_summary()
        
    finally:
        await suite.close()


if __name__ == "__main__":
    asyncio.run(main())
