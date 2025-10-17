# 📘 MCP Server User Guide

## What is This?

This is a **search server** that lets you query the **CI360 manual** using natural language. It uses advanced AI techniques (RAG-Fusion) to find the most relevant information.

---

## 🚀 How to Use It

### Step 1: Start the Server

Open PowerShell in the project directory and run:

```powershell
docker compose up -d
```

Wait about 30 seconds for the server to start.

### Step 2: Check It's Running

```powershell
Invoke-WebRequest -Uri "http://localhost:8080/health" -UseBasicParsing
```

You should see:
```json
{
  "status": "healthy",
  "version": "v20251014123459",
  "uptime_seconds": 58
}
```

### Step 3: Search the Manual

**Using PowerShell:**

```powershell
$query = @{
    query = "What is CI360?"
    top_k = 5
} | ConvertTo-Json

Invoke-WebRequest `
    -Uri "http://localhost:8080/mcp/search_manual" `
    -Method POST `
    -ContentType "application/json" `
    -Body $query `
    -UseBasicParsing | Select-Object -ExpandProperty Content
```

**Using Python:**

```python
import requests

response = requests.post(
    "http://localhost:8080/mcp/search_manual",
    json={
        "query": "What is CI360?",
        "top_k": 5
    }
)

# Get results
data = response.json()
print(f"Found {len(data['chunks'])} results")

# Show first result
print(data['chunks'][0]['text'])
```

---

## 🎯 Example Queries

Try these queries to see what the system can do:

### General Information
```
"What is SAS Customer Intelligence 360?"
"What features does CI360 provide?"
"What is CI360 used for?"
```

### Technical Questions
```
"What are the system requirements for CI360?"
"How do I install CI360?"
"What browsers are supported?"
```

### How-To Questions
```
"How do I create a marketing campaign?"
"How to integrate external data?"
"How to configure security settings?"
```

### Troubleshooting
```
"How to fix performance issues?"
"Why is my campaign not working?"
"How to resolve connection errors?"
```

---

## 📊 Understanding the Response

When you search, you get back:

```json
{
  "context": "Ready-to-use text for AI...",
  "chunks": [
    {
      "chunk_id": "ci360-manual_p123_c0",
      "document_id": "ci360-manual",
      "page": 123,
      "text": "Content from the manual...",
      "score": 0.95
    }
  ],
  "metadata": {
    "intent": "fact",
    "index_version": "v20251014123459"
  }
}
```

- **context**: A summary combining the best results
- **chunks**: Individual pieces from the manual
- **page**: Where in the manual this came from
- **score**: How relevant (0-1, higher is better)

---

## 🔧 Common Commands

### Start Server
```bash
docker compose up -d
```

### Stop Server
```bash
docker compose down
```

### View Logs
```bash
docker compose logs -f server
```

### Check Status
```bash
docker compose ps
```

### Restart Server
```bash
docker compose restart server
```

---

## 💡 Tips

1. **Be specific**: "How to create campaigns?" works better than "campaigns"
2. **Ask questions**: Natural questions work well
3. **First query is slow**: Takes ~5 seconds, then much faster
4. **Use top_k=3 for speed**: Fewer results = faster
5. **Check the page numbers**: See where info came from in the manual

---

## 🐛 Troubleshooting

### "Cannot connect"
- Make sure the server is running: `docker compose ps`
- Wait 30 seconds after starting
- Check health: `Invoke-WebRequest http://localhost:8080/health`

### "Slow responses"
- First query is always slower (loading models)
- Subsequent queries are cached and fast
- Check resources: `docker stats rag_server`

### "No results"
- Try rephrasing your query
- Use simpler terms
- Break complex questions into parts

---

## 📚 More Information

- **API Documentation**: http://localhost:8080/docs
- **Quick Start Guide**: See `QUICKSTART_GUIDE.md`
- **Docker Details**: See `DOCKER_DEPLOYMENT.md`
- **Implementation**: See `IMPLEMENTATION_REPORT.md`

---

## 🎓 Integration Examples

### Use with ChatGPT/Claude

```
I have a search API for the CI360 manual at:
http://localhost:8080/mcp/search_manual

Query it like this:
POST with JSON: {"query": "your question", "top_k": 5}

Please search for [your question]
```

### Use with Python Script

```python
import requests

def search_ci360(question, num_results=5):
    """Search the CI360 manual"""
    response = requests.post(
        "http://localhost:8080/mcp/search_manual",
        json={"query": question, "top_k": num_results}
    )
    return response.json()

# Use it
results = search_ci360("What is CI360?")
for chunk in results['chunks']:
    print(f"Page {chunk['page']}: {chunk['text'][:200]}...")
```

### Use with JavaScript

```javascript
async function searchCI360(query) {
    const response = await fetch('http://localhost:8080/mcp/search_manual', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            query: query,
            top_k: 5
        })
    });
    return await response.json();
}

// Use it
const results = await searchCI360('What is CI360?');
console.log(`Found ${results.chunks.length} results`);
```

---

## ✅ Quick Health Check

Run this to verify everything works:

```powershell
# 1. Check server is running
docker compose ps

# 2. Check health
Invoke-WebRequest http://localhost:8080/health -UseBasicParsing

# 3. Try a simple search
$test = @{query="CI360";top_k=3} | ConvertTo-Json
Invoke-WebRequest http://localhost:8080/mcp/search_manual -Method POST -ContentType application/json -Body $test -UseBasicParsing
```

If all three work, you're good to go! ✅

---

**Server URL:** http://localhost:8080  
**Status:** ✅ Running and ready  
**Documentation:** http://localhost:8080/docs

Happy searching! 🔍