"""
Chat service using Azure OpenAI GPT-4o for RAG chat.
"""

import json
from typing import List
from app.config import get_settings
from app.models.schemas import ChatMessage, ChatRequest, ChatResponse, RepositorySummary
from app.utils.logger import get_logger
from app.utils.retry import retry_async

logger = get_logger("chat_service")


class ChatEngine:
    """Core GPT-4o chat engine backed by codebase RAG."""

    def __init__(self):
        self.settings = get_settings()
        self._llm_client = None

    @property
    def llm_client(self):
        if self._llm_client is None:
            from openai import AzureOpenAI
            self._llm_client = AzureOpenAI(
                api_key=self.settings.AZURE_OPENAI_API_KEY,
                api_version=self.settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=self.settings.AZURE_OPENAI_ENDPOINT,
            )
        return self._llm_client

    async def chat(self, repo_summary: RepositorySummary, messages: List[ChatMessage], code_chunks: List[dict]) -> ChatResponse:
        logger.info(f"Starting chat completion for repo {repo_summary.repo_id}")

        if self.settings.MOCK_MODE:
            return self._mock_chat(messages, code_chunks)

        arch_summary = self._build_architecture_summary(repo_summary)
        code_context = self._build_code_context(code_chunks)

        system_message = (
            "You are an expert software engineering assistant. Your task is to answer the user's questions about their codebase.\n"
            "You will be provided with information about the repository architecture, and relevant code chunks from their codebase.\n"
            "Use ONLY the provided context to answer the question. If the answer cannot be found in the context, say so.\n"
            "Always include code snippets or references to file paths where appropriate to back up your answer.\n\n"
            "### Architecture Summary\n"
            f"{arch_summary}\n\n"
            "### Code Context\n"
            f"{code_context}\n"
        )

        formatted_messages = [{"role": "system", "content": system_message}]
        for msg in messages:
            formatted_messages.append({"role": msg.role, "content": msg.content})

        try:
            data = await self._call_llm(formatted_messages)
            return ChatResponse(
                message=ChatMessage(role="assistant", content=data),
                retrieved_chunks=code_chunks
            )
        except Exception as e:
            logger.exception(f"Failed to generate chat response: {e}")
            raise

    async def _call_llm(self, messages: List[dict]) -> str:
        async def _call():
            response = self.llm_client.chat.completions.create(
                model=self.settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
                messages=messages,
                temperature=0.3,
                max_tokens=4000,
            )
            return response.choices[0].message.content
        return await retry_async(_call, max_retries=2, operation_name="LLM chat generation")

    def _build_architecture_summary(self, summary: RepositorySummary) -> str:
        parts = [f"Repository: {summary.repo_name}"]
        if summary.detected_frameworks:
            parts.append(f"Frameworks: {', '.join(f.value for f in summary.detected_frameworks)}")
        parts.append(f"Languages: {summary.languages}")
        parts.append(f"Files: {summary.total_files}, Lines: {summary.total_lines}")
        return "\n".join(parts)

    def _build_code_context(self, chunks: List[dict]) -> str:
        if not chunks:
            return "No relevant code chunks found."
        
        parts = []
        for i, chunk in enumerate(chunks[:10]):  # Limit to top 10 to save context window
            file_path = chunk.get("file_path", "Unknown File")
            code = chunk.get("code_text", "")
            parts.append(f"--- File: {file_path} ---\n{code}")
            
        return "\n\n".join(parts)

    def _mock_chat(self, messages: List[ChatMessage], chunks: List[dict]) -> ChatResponse:
        logger.info("[MOCK] Generating mock chat response")
        last_msg = messages[-1].content if messages else ""
        
        reply = (
            f"This is a mock response from the Chat Engine.\n\n"
            f"You asked: '{last_msg}'.\n\n"
            f"I found {len(chunks)} relevant code chunks. In a real environment, I would analyze these chunks to answer your question."
        )
        
        return ChatResponse(
            message=ChatMessage(role="assistant", content=reply),
            retrieved_chunks=chunks
        )


def get_chat_engine() -> ChatEngine:
    return ChatEngine()
