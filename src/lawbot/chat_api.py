import os
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from typing import Generator, List, Dict, Any
from loguru import logger

from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import get_tracer_provider, set_tracer_provider

from chat_service import ChatService



os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

set_tracer_provider(
    TracerProvider(resource=Resource.create({SERVICE_NAME: "chat-service"}))
)
tracer = get_tracer_provider().get_tracer("legal-chatbot", "0.1.2")

jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger-agent.tracer.",
    agent_port=6831,
)
span_processor = BatchSpanProcessor(jaeger_exporter)
get_tracer_provider().add_span_processor(span_processor)



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
