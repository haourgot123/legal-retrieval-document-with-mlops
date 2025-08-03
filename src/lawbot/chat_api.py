import os
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from typing import Generator, List, Dict, Any
from loguru import logger
from dotenv import load_dotenv

from chat_service import ChatService


load_dotenv()


app = FastAPI()
chat_service = ChatService(
    model="gpt-4o",
    embedding_model="text-embedding-3-small",
    sparse_model="Qdrant/bm25",
    late_interaction_model="colbert-ir/colbertv2.0",
    collection_name="legal_documents",
    qdrant_url="http://qdrant.vectordb.svc.cluster.local:6333"
)

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint to verify if the service is running.
    Returns:
        Dict[str, str]: Health status.
    """
    return {"status": "ok"}


@app.post("/chat")
async def chat(query: str, stream: bool = True) -> Generator[str, None, None]:
    """
    Endpoint to handle chat queries.
    Args:
        query (str): User's query.
        stream (bool): Whether to stream the response.
    Yields:
        Generator[str, None, None]: Streamed chat response.
    """
    logger.info(f"Received query: {query}")
    return StreamingResponse(chat_service.chat(query, stream), media_type="text/event-stream")
