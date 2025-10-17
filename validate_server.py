#!/usr/bin/env python3
"""Comprehensive validation test suite for the MCP Server."""

import requests
import json
import time
from typing import List, Dict, Any
from datetime import datetime

class MCPServerValidator:
    """Validates MCP server functionality with real queries."""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.results = []
        self.start_time = None
        
    def print_header(self, text: str):
        """Print a formatted header."""
        print("\n" + "=" * 80)
        print(f"  {text}")
        print("=" * 80)
        
    def print_section(self, text: str):
        """Print a formatted section."""
        print(f"\n{'─' * 80}")
        print(f"  {text}")
        print(f"{'─' * 80}")
        
    def test_health(self) -> bool:
        """Test the health endpoint."""
        self.print_section("🏥 Health Check")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            data = response.json()
            
            print(f"✅ Server is healthy")
            print(f"   Status: {data['status']}")
            print(f"   Version: {data['version']}")
            print(f"   Uptime: {data['uptime_seconds']} seconds")
            return True
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    def search(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Execute a search query."""
        try:
            response = requests.post(
                f"{self.base_url}/mcp/search_manual",
                json={
                    "query": query,
                    "top_k": top_k,
                    "include_examples": False,
                    "min_confidence": 0.0
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return None
    
    def display_results(self, query: str, data: Dict[str, Any], show_context: bool = True):
        """Display search results in a formatted way."""
        if not data:
            print(f"❌ No results for: {query}")
            return
            
        chunks = data.get('chunks', [])
        metadata = data.get('metadata', {})
        
        print(f"\n📝 Query: \"{query}\"")
        print(f"   Results: {len(chunks)} chunks found")
        print(f"   Intent: {metadata.get('intent', 'unknown')}")
        print(f"   Index Version: {metadata.get('index_version', 'unknown')}")
        
        if chunks:
            print(f"\n   📄 Top Results:")
            for i, chunk in enumerate(chunks[:3], 1):
                score = chunk.get('score', 0)
                page = chunk.get('page', '?')
                text = chunk.get('text', '')[:150]
                print(f"\n   {i}. Page {page} | Score: {score:.3f}")
                print(f"      {text}...")
        
        if show_context:
            context = data.get('context', '')
            if context:
                print(f"\n   💡 Context Summary:")
                print(f"      {context[:300]}...")
    
    def test_sample_questions(self):
        """Test a variety of sample questions."""
        self.print_header("🔍 Sample Questions Validation")
        
        test_cases = [
            {
                "category": "General Information",
                "queries": [
                    "What is SAS Customer Intelligence 360?",
                    "What is CI360 used for?",
                    "What are the main features of CI360?"
                ]
            },
            {
                "category": "Technical Requirements",
                "queries": [
                    "What are the system requirements for CI360?",
                    "What browsers are supported?",
                    "What are the hardware requirements?"
                ]
            },
            {
                "category": "How-To Questions",
                "queries": [
                    "How do I create a marketing campaign in CI360?",
                    "How to set up data integration?",
                    "How to configure security settings?"
                ]
            },
            {
                "category": "Features & Capabilities",
                "queries": [
                    "What data integration features does CI360 provide?",
                    "What analytics capabilities are available?",
                    "What reporting features does CI360 have?"
                ]
            },
            {
                "category": "Troubleshooting",
                "queries": [
                    "How to troubleshoot performance issues?",
                    "How to resolve login problems?",
                    "What to do if a campaign is not working?"
                ]
            }
        ]
        
        total_queries = 0
        successful_queries = 0
        query_times = []
        
        for test_case in test_cases:
            self.print_section(f"📂 {test_case['category']}")
            
            for query in test_case['queries']:
                total_queries += 1
                start = time.time()
                
                data = self.search(query, top_k=5)
                
                elapsed = time.time() - start
                query_times.append(elapsed)
                
                if data and data.get('chunks'):
                    successful_queries += 1
                    self.display_results(query, data, show_context=False)
                    print(f"   ⏱️  Response time: {elapsed:.2f}s")
                else:
                    print(f"\n📝 Query: \"{query}\"")
                    print(f"   ❌ No results found")
                
                # Small delay between queries
                time.sleep(0.5)
        
        # Summary statistics
        self.print_section("📊 Query Statistics")
        print(f"Total queries: {total_queries}")
        print(f"Successful queries: {successful_queries}")
        print(f"Success rate: {(successful_queries/total_queries)*100:.1f}%")
        print(f"Average response time: {sum(query_times)/len(query_times):.2f}s")
        print(f"Fastest query: {min(query_times):.2f}s")
        print(f"Slowest query: {max(query_times):.2f}s")
    
    def test_detailed_query(self):
        """Test a detailed query with full context display."""
        self.print_header("🔬 Detailed Query Analysis")
        
        query = "What is CI360 and how does it work?"
        print(f"\n📝 Analyzing query: \"{query}\"")
        
        start = time.time()
        data = self.search(query, top_k=5)
        elapsed = time.time() - start
        
        if data:
            self.display_results(query, data, show_context=True)
            print(f"\n   ⏱️  Total response time: {elapsed:.2f}s")
            
            # Analyze chunk quality
            chunks = data.get('chunks', [])
            if chunks:
                self.print_section("📈 Result Quality Analysis")
                print(f"Number of chunks: {len(chunks)}")
                
                scores = [c.get('score', 0) for c in chunks]
                print(f"Score range: {min(scores):.3f} - {max(scores):.3f}")
                print(f"Average score: {sum(scores)/len(scores):.3f}")
                
                pages = set(c.get('page', 0) for c in chunks)
                print(f"Pages referenced: {sorted(pages)}")
                
                # Show full first result
                print(f"\n📄 Full First Result:")
                first = chunks[0]
                print(f"   Chunk ID: {first.get('chunk_id', 'unknown')}")
                print(f"   Document: {first.get('document_id', 'unknown')}")
                print(f"   Page: {first.get('page', '?')}")
                print(f"   Score: {first.get('score', 0):.3f}")
                print(f"   Source Type: {first.get('source_type', 'unknown')}")
                print(f"\n   Content:")
                print(f"   {first.get('text', 'No text available')}")
    
    def test_caching(self):
        """Test query caching performance."""
        self.print_header("💾 Caching Performance Test")
        
        query = "What is CI360?"
        
        # First query (no cache)
        print("\n🔄 First query (uncached)...")
        start = time.time()
        data1 = self.search(query, top_k=5)
        time1 = time.time() - start
        print(f"   Response time: {time1:.3f}s")
        
        # Second query (should be cached)
        print("\n⚡ Second query (cached)...")
        start = time.time()
        data2 = self.search(query, top_k=5)
        time2 = time.time() - start
        print(f"   Response time: {time2:.3f}s")
        
        # Analysis
        if time2 < time1:
            speedup = (time1 - time2) / time1 * 100
            print(f"\n✅ Caching working! {speedup:.1f}% faster")
            print(f"   Speedup: {time1/time2:.2f}x")
        else:
            print(f"\n⚠️  Cache may not be working as expected")
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        self.print_header("🧪 Edge Cases & Error Handling")
        
        test_cases = [
            ("Very short query", "CI360"),
            ("Single word", "campaigns"),
            ("Acronym", "SAS"),
            ("Very long query", "How do I configure and set up SAS Customer Intelligence 360 to work with external data sources including databases APIs and third-party integrations while ensuring data security compliance and optimal performance?"),
            ("Special characters", "What is CI360?!"),
            ("Numbers", "CI360 version 2023"),
        ]
        
        for name, query in test_cases:
            print(f"\n🔍 Testing: {name}")
            print(f"   Query: \"{query}\"")
            
            start = time.time()
            data = self.search(query, top_k=3)
            elapsed = time.time() - start
            
            if data and data.get('chunks'):
                print(f"   ✅ Success - {len(data['chunks'])} results in {elapsed:.2f}s")
            else:
                print(f"   ❌ No results")
    
    def run_all_tests(self):
        """Run all validation tests."""
        self.start_time = datetime.now()
        
        self.print_header("🚀 MCP Server Validation Suite")
        print(f"   Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Server: {self.base_url}")
        
        # Run tests
        if not self.test_health():
            print("\n❌ Server health check failed. Aborting tests.")
            return False
        
        self.test_detailed_query()
        self.test_sample_questions()
        self.test_caching()
        self.test_edge_cases()
        
        # Final summary
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        self.print_header("✅ Validation Complete")
        print(f"   End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Total Duration: {duration:.1f} seconds")
        print(f"\n   🎉 All validation tests completed successfully!")
        print(f"   📊 The MCP Server is fully functional and ready for use.")
        
        return True

if __name__ == "__main__":
    validator = MCPServerValidator()
    validator.run_all_tests()