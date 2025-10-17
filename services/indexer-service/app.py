"""Indexer Service - PDF Processing and Index Building.

This service handles:
- PDF ingestion and multimodal processing
- Chunking and embedding generation
- FAISS and BM25 index building
- Index versioning and management
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
import uvicorn

# Import from parent indexer module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from indexer.pipeline import IndexBuildConfig, IndexBuildResult, run_index_build

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [IndexerService] %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
PDF_DIR = Path(os.getenv("PDF_DIR", "/data/pdf"))
ARTIFACTS_DIR = Path(os.getenv("ARTIFACTS_DIR", "/data/artifacts"))
INDEX_OUTPUT_DIR = Path(os.getenv("INDEX_OUTPUT_DIR", "/data/indexes"))

APP_START_TIME = time.time()

# In-memory job tracking
index_jobs: Dict[str, Dict[str, Any]] = {}


# Pydantic models
class IndexBuildRequest(BaseModel):
    source_type: str = Field("fact", description="Source type (fact or example)")
    chunk_size: int = Field(512, ge=128, le=2048, description="Chunk size in tokens")
    chunk_overlap: int = Field(50, ge=0, le=256, description="Chunk overlap")
    embedding_model: str = Field("BAAI/bge-m3", description="Embedding model name")
    ocr_languages: str = Field("eng", description="OCR languages (e.g., 'eng', 'eng+fra')")


class IndexBuildJobResponse(BaseModel):
    job_id: str
    status: str
    message: str


class IndexJobStatus(BaseModel):
    job_id: str
    status: str  # pending, running, completed, failed
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    total_chunks: Optional[int] = None
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    uptime_seconds: int
    pdf_dir: str
    pdf_files_count: int


# FastAPI app
app = FastAPI(
    title="RAG-Fusion Indexer Service",
    description="Microservice for PDF processing and index building",
    version="1.0.0",
)


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize indexer service."""
    logger.info("Starting Indexer Service...")
    logger.info(f"PDF directory: {PDF_DIR}")
    logger.info(f"Artifacts directory: {ARTIFACTS_DIR}")
    logger.info(f"Index output directory: {INDEX_OUTPUT_DIR}")
    
    # Ensure directories exist
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info("✓ Indexer Service initialized")


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    uptime = int(time.time() - APP_START_TIME)
    
    # Count PDF files
    pdf_count = 0
    if PDF_DIR.exists():
        pdf_count = len(list(PDF_DIR.glob("*.pdf")))
    
    return HealthResponse(
        status="healthy",
        service="indexer-service",
        version="1.0.0",
        uptime_seconds=uptime,
        pdf_dir=str(PDF_DIR),
        pdf_files_count=pdf_count,
    )


@app.post("/index/build", response_model=IndexBuildJobResponse)
async def build_index(
    request: IndexBuildRequest,
    background_tasks: BackgroundTasks,
) -> IndexBuildJobResponse:
    """
    Trigger an index build job.
    
    This endpoint starts a background job to:
    1. Ingest PDFs from the PDF directory
    2. Extract text and images (multimodal)
    3. Chunk documents
    4. Generate embeddings
    5. Build FAISS and BM25 indexes
    """
    # Generate job ID
    job_id = f"index-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    
    # Create job entry
    index_jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "started_at": None,
        "completed_at": None,
        "total_chunks": None,
        "error": None,
        "result": None,
    }
    
    # Start background task
    background_tasks.add_task(
        run_index_build_job,
        job_id=job_id,
        request=request,
    )
    
    logger.info(f"Created index build job: {job_id}")
    
    return IndexBuildJobResponse(
        job_id=job_id,
        status="pending",
        message=f"Index build job {job_id} created and queued",
    )


async def run_index_build_job(job_id: str, request: IndexBuildRequest) -> None:
    """Background task to run index build."""
    logger.info(f"Starting index build job: {job_id}")
    
    # Update job status
    index_jobs[job_id]["status"] = "running"
    index_jobs[job_id]["started_at"] = datetime.utcnow().isoformat()
    
    try:
        # Create build config
        config = IndexBuildConfig(
            input_dir=PDF_DIR,
            output_dir=INDEX_OUTPUT_DIR,
            artifacts_dir=ARTIFACTS_DIR,
            source_type=request.source_type,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
            embedding_model=request.embedding_model,
            ocr_languages=request.ocr_languages,
        )
        
        logger.info(f"Job {job_id}: Starting pipeline with config: {config}")
        
        # Run the actual index build
        result: IndexBuildResult = run_index_build(config)
        
        # Update job with success
        index_jobs[job_id]["status"] = "completed"
        index_jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()
        index_jobs[job_id]["total_chunks"] = result.total_chunks
        index_jobs[job_id]["result"] = {
            "manifest_path": str(result.manifest_path),
            "total_chunks": result.total_chunks,
            "fact_chunks": result.fact_chunks,
            "example_chunks": result.example_chunks,
        }
        
        logger.info(f"Job {job_id}: Completed successfully. Total chunks: {result.total_chunks}")
        
    except Exception as e:
        logger.error(f"Job {job_id}: Failed with error: {e}", exc_info=True)
        
        # Update job with failure
        index_jobs[job_id]["status"] = "failed"
        index_jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()
        index_jobs[job_id]["error"] = str(e)


@app.get("/index/jobs/{job_id}", response_model=IndexJobStatus)
async def get_job_status(job_id: str) -> IndexJobStatus:
    """Get the status of an index build job."""
    if job_id not in index_jobs:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    job = index_jobs[job_id]
    
    return IndexJobStatus(
        job_id=job["job_id"],
        status=job["status"],
        started_at=job["started_at"],
        completed_at=job["completed_at"],
        total_chunks=job["total_chunks"],
        error=job["error"],
        result=job["result"],
    )


@app.get("/index/jobs")
async def list_jobs() -> Dict[str, Any]:
    """List all index build jobs."""
    return {
        "total_jobs": len(index_jobs),
        "jobs": list(index_jobs.values()),
    }


@app.post("/pdf/upload")
async def upload_pdf(file: UploadFile = File(...)) -> Dict[str, str]:
    """
    Upload a PDF file for indexing.
    
    The file will be saved to the PDF directory and can be included
    in the next index build.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Save file
    file_path = PDF_DIR / file.filename
    
    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"Uploaded PDF: {file.filename} ({len(content)} bytes)")
        
        return {
            "filename": file.filename,
            "path": str(file_path),
            "size_bytes": len(content),
            "message": "File uploaded successfully",
        }
        
    except Exception as e:
        logger.error(f"Failed to upload PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/pdf/list")
async def list_pdfs() -> Dict[str, Any]:
    """List all PDF files in the PDF directory."""
    if not PDF_DIR.exists():
        return {"pdfs": [], "total": 0}
    
    pdfs = []
    for pdf_path in PDF_DIR.glob("*.pdf"):
        pdfs.append({
            "filename": pdf_path.name,
            "size_bytes": pdf_path.stat().st_size,
            "modified_at": datetime.fromtimestamp(pdf_path.stat().st_mtime).isoformat(),
        })
    
    return {
        "pdfs": pdfs,
        "total": len(pdfs),
        "directory": str(PDF_DIR),
    }


@app.delete("/index/jobs/{job_id}")
async def delete_job(job_id: str) -> Dict[str, str]:
    """Delete a job from the job history."""
    if job_id not in index_jobs:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    del index_jobs[job_id]
    
    return {"message": f"Job {job_id} deleted"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8082"))
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True,
    )
