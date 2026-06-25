"""
Chat router — interact with the codebase.
"""

from fastapi import APIRouter, HTTPException, Request

from app.models.schemas import ChatRequest, ChatResponse, ProcessingStatus
from app.services.chat_service import get_chat_engine
from app.utils.logger import get_logger

logger = get_logger("router.chat")
router = APIRouter()


@router.post("/chat/{repo_id}", response_model=ChatResponse)
async def chat_with_repo(repo_id: str, request_body: ChatRequest, request: Request):
    """Chat with the codebase."""
    repo_data = request.app.state.repositories.get(repo_id)
    if not repo_data:
        raise HTTPException(status_code=404, detail="Repository not found")
    if repo_data["status"] != ProcessingStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="Repository is still processing")

    summary = repo_data["summary"]
    search_service = repo_data.get("search_service")
    embedding_service = repo_data.get("embedding_service")

    # Get the latest user query
    if not request_body.messages:
        raise HTTPException(status_code=400, detail="Messages list cannot be empty")
        
    latest_query = request_body.messages[-1].content

    # Retrieve relevant code chunks
    code_chunks = []
    if search_service and embedding_service:
        try:
            query_vector = await embedding_service.generate_embedding(latest_query)
            # Retrieve top 10 most relevant chunks
            code_chunks = await search_service.hybrid_search(latest_query, query_vector, repo_id=repo_id, top=10)
        except Exception as e:
            logger.error(f"Search failed during chat: {e}")

    engine = get_chat_engine()
    result = await engine.chat(summary, request_body.messages, code_chunks)

    return result
