"""
Generation router — trigger requirement generation and check results.
"""

from fastapi import APIRouter, HTTPException, Request

from app.models.schemas import (
    GenerationRequest, GenerationResult, GenerationStatus,
    GenerationStatusResponse, ProcessingStatus,
)
from app.services.generation_service import get_generation_engine
from app.utils.logger import get_logger

logger = get_logger("router.generate")
router = APIRouter()


@router.post("/generate/{repo_id}", response_model=GenerationResult)
async def generate_requirements(repo_id: str, request_body: GenerationRequest, request: Request):
    """Generate requirements and test cases for a processed repository."""
    repo_data = request.app.state.repositories.get(repo_id)
    if not repo_data:
        raise HTTPException(status_code=404, detail="Repository not found")
    if repo_data["status"] != ProcessingStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="Repository is still processing")

    summary = repo_data["summary"]
    search_service = repo_data.get("search_service")
    embedding_service = repo_data.get("embedding_service")

    # Retrieve relevant code chunks
    code_chunks = []
    
    if request_body.target_modules:
        # Exhaustive Map-Reduce mode for specific modules
        all_chunks = repo_data.get("chunks", [])
        for chunk_item in all_chunks:
            file_path = chunk_item["chunk"].file_path
            # Check if this file falls under any of the target module directories
            if any(file_path.startswith(mod) for mod in request_body.target_modules):
                code_chunks.append({
                    "file_path": file_path,
                    "code_text": chunk_item["chunk"].text
                })
    else:
        # Generic RAG mode over entire codebase
        if search_service and embedding_service:
            query = f"API routes models services components for {summary.repo_name}"
            query_vector = await embedding_service.generate_embedding(query)
            code_chunks = await search_service.hybrid_search(query, query_vector, repo_id=repo_id, top=20)

    # Generate
    categories = [c.value for c in request_body.categories]
    engine = get_generation_engine()
    result = await engine.generate(repo_id, summary, code_chunks, categories, request_body.target_modules)

    # Store result
    request.app.state.generations[result.generation_id] = result
    logger.info(f"Generation {result.generation_id} completed for repo {repo_id}")

    return result


@router.get("/generate/{generation_id}/results", response_model=GenerationResult)
async def get_generation_results(generation_id: str, request: Request):
    """Get the results of a completed generation."""
    result = request.app.state.generations.get(generation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Generation not found")
    return result


@router.get("/generate/{generation_id}/status", response_model=GenerationStatusResponse)
async def get_generation_status(generation_id: str, request: Request):
    """Get the status of a generation."""
    result = request.app.state.generations.get(generation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Generation not found")
    return GenerationStatusResponse(
        generation_id=generation_id, repo_id=result.repo_id,
        status=result.status,
        progress_message="Completed" if result.status == GenerationStatus.COMPLETED else "Processing...",
        progress_percent=100 if result.status == GenerationStatus.COMPLETED else 50,
    )
