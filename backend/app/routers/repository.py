"""
Repository router — upload ZIP or provide GitHub URL.
"""

import uuid
import base64
from fastapi import APIRouter, UploadFile, File, HTTPException, Request

from app.models.schemas import (
    GitHubURLRequest, UploadResponse, RepositoryStatusResponse,
    ProcessingStatus, RepositorySummary, DetectedFramework,
)
from app.services.repository_service import get_repository_service
from app.services.code_parser import get_code_parser
from app.services.chunking_service import get_chunking_service
from app.services.embedding_service import get_embedding_service
from app.services.search_service import get_search_service, SearchDocument
from app.utils.logger import get_logger

logger = get_logger("router.repository")
router = APIRouter()


async def _process_repository(repo_id: str, repo_name: str, files, request: Request):
    """Full pipeline: parse → chunk → embed → index."""
    app = request.app

    # Update status
    app.state.repositories[repo_id] = {
        "status": ProcessingStatus.PARSING, "repo_name": repo_name,
        "progress": 20, "message": "Parsing source code...",
    }

    # Parse all files
    parser = get_code_parser()
    analyses = []
    for f in files:
        content = f.read_content()
        if not content.strip():
            continue
        analysis = parser.parse_file(f.path, f.relative_path, content)
        analyses.append(analysis)

    # Build summary
    frameworks = set()
    languages = {}
    route_count = model_count = component_count = service_count = test_count = 0
    total_lines = 0

    for a in analyses:
        if a.framework != DetectedFramework.UNKNOWN:
            frameworks.add(a.framework)
        languages[a.language] = languages.get(a.language, 0) + 1
        total_lines += a.line_count
        if a.has_tests:
            test_count += 1
        for e in a.elements:
            if e.element_type == "route":
                route_count += 1
            elif e.element_type == "model":
                model_count += 1
            elif e.element_type == "component":
                component_count += 1
            elif e.element_type in ("function", "class"):
                service_count += 1

    summary = RepositorySummary(
        repo_id=repo_id, repo_name=repo_name,
        detected_frameworks=list(frameworks),
        languages=languages, total_files=len(files),
        total_lines=total_lines, route_count=route_count,
        model_count=model_count, component_count=component_count,
        service_count=service_count, test_file_count=test_count,
        file_analyses=analyses,
    )

    # Chunk code
    app.state.repositories[repo_id]["status"] = ProcessingStatus.EMBEDDING
    app.state.repositories[repo_id]["progress"] = 50
    app.state.repositories[repo_id]["message"] = "Generating embeddings..."

    chunking = get_chunking_service()
    all_chunks = []
    all_texts = []
    for f in files:
        content = f.read_content()
        if not content.strip():
            continue
        chunks = chunking.chunk_code(content, f.relative_path, f.extension.lstrip("."))
        for chunk in chunks:
            all_chunks.append({"chunk": chunk, "file": f})
            all_texts.append(chunk.text)

    # Embed
    embedding_service = get_embedding_service()
    embeddings = await embedding_service.generate_embeddings_batch(all_texts) if all_texts else []

    # Index
    app.state.repositories[repo_id]["status"] = ProcessingStatus.INDEXING
    app.state.repositories[repo_id]["progress"] = 80
    app.state.repositories[repo_id]["message"] = "Indexing into vector store..."

    search_service = get_search_service()
    await search_service.create_or_update_index()

    search_docs = []
    for i, item in enumerate(all_chunks):
        chunk = item["chunk"]
        raw_id = f"{repo_id}-{chunk.file_path}-{chunk.chunk_index}"
        safe_id = base64.urlsafe_b64encode(raw_id.encode()).decode().rstrip("=")
        search_docs.append(SearchDocument(
            doc_id=safe_id, repo_id=repo_id, file_path=chunk.file_path, language=chunk.language,
            framework="", code_text=chunk.text, element_type="code",
            content_vector=embeddings[i] if i < len(embeddings) else [],
            chunk_index=chunk.chunk_index, total_chunks=chunk.total_chunks,
        ))
    await search_service.index_documents(search_docs)

    # Mark complete
    app.state.repositories[repo_id]["status"] = ProcessingStatus.COMPLETED
    app.state.repositories[repo_id]["progress"] = 100
    app.state.repositories[repo_id]["message"] = "Repository processed successfully"
    app.state.repositories[repo_id]["summary"] = summary
    app.state.repositories[repo_id]["search_service"] = search_service
    app.state.repositories[repo_id]["embedding_service"] = embedding_service
    app.state.repositories[repo_id]["chunks"] = all_chunks

    logger.info(f"Repository {repo_id} fully processed: {len(files)} files, {len(search_docs)} chunks")


@router.post("/repository/github", response_model=UploadResponse)
async def clone_github_repo(request_body: GitHubURLRequest, request: Request):
    """Clone a GitHub repository and process it."""
    repo_service = get_repository_service()
    try:
        repo_id, repo_name, files = await repo_service.clone_github_repo(
            request_body.github_url, request_body.branch
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    request.app.state.repositories[repo_id] = {
        "status": ProcessingStatus.CLONING, "repo_name": repo_name,
        "progress": 10, "message": "Repository cloned, starting analysis...",
    }

    # Process synchronously for simplicity (async task in production)
    await _process_repository(repo_id, repo_name, files, request)

    return UploadResponse(
        repo_id=repo_id, status=ProcessingStatus.COMPLETED,
        message=f"Repository '{repo_name}' processed successfully",
    )


@router.post("/repository/upload", response_model=UploadResponse)
async def upload_repository(request: Request, file: UploadFile = File(...)):
    """Upload a ZIP file and process it."""
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files are supported")

    content = await file.read()
    repo_service = get_repository_service()

    try:
        repo_id, repo_name, files = await repo_service.extract_upload(content, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    request.app.state.repositories[repo_id] = {
        "status": ProcessingStatus.PREPROCESSING, "repo_name": repo_name,
        "progress": 10, "message": "Archive extracted, starting analysis...",
    }

    await _process_repository(repo_id, repo_name, files, request)

    return UploadResponse(
        repo_id=repo_id, status=ProcessingStatus.COMPLETED,
        message=f"Repository '{repo_name}' processed successfully",
    )


@router.get("/repository/{repo_id}/status", response_model=RepositoryStatusResponse)
async def get_repository_status(repo_id: str, request: Request):
    """Get the processing status of a repository."""
    repo_data = request.app.state.repositories.get(repo_id)
    if not repo_data:
        raise HTTPException(status_code=404, detail="Repository not found")

    return RepositoryStatusResponse(
        repo_id=repo_id,
        status=repo_data["status"],
        progress_message=repo_data.get("message", ""),
        progress_percent=repo_data.get("progress", 0),
    )


@router.get("/repository/{repo_id}/summary", response_model=RepositorySummary)
async def get_repository_summary(repo_id: str, request: Request):
    """Get the parsed summary of a processed repository."""
    repo_data = request.app.state.repositories.get(repo_id)
    if not repo_data:
        raise HTTPException(status_code=404, detail="Repository not found")
    if repo_data["status"] != ProcessingStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="Repository is still processing")

    return repo_data["summary"]
