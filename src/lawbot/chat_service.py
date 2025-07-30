import os
import time
from openai import OpenAI
from typing import List, Dict, Any, Generator
from loguru import logger
from dotenv import load_dotenv

from hybrid_search import HybridSearch
from prompt import system_prompt

load_dotenv()


class ChatService:


    def __init__(
        self,
        model: str = "gpt-4o",
        embedding_model: str = "text-embedding-3-small",
        sparse_model: str = "Qdrant/bm25",
        late_interaction_model: str = "colbert-ir/colbertv2.0",
        collection_name: str = "legal_documents",
        qdrant_url: str = "http://qdrant.database.svc.cluster.local:6333"
    ) -> None:
        """
        Initialize the ChatService with OpenAI API key and model.
        Args:
            api_key (str): OpenAI API key.
            model (str): Model to use for chat completions.
        """
        self.client = OpenAI()
        self.model = model
        self.hybrid_searcher = HybridSearch(
            embedding_model=embedding_model,
            sparse_model=sparse_model,
            late_interaction_model=late_interaction_model,
            collection_name=collection_name,
            qdrant_url=qdrant_url
        )

    def chat(
        self,
        query: str,
        stream: bool = True
    ):
        """
        Generate a chat response based on the query.
        Args:
            query (str): User's query.
        Yields:
            Generator[str, None, None]: Chat response.
        """
        logger.info(f"Received query: {query}")

        # Perform hybrid search
        logger.info("Performing hybrid search...")
        start = time.time()
        search_results = self.hybrid_searcher.query(query)
        end = time.time()
        logger.info(f"Hybrid search completed in {end - start:.2f} seconds")
        logger.info(f"Search results: {search_results}")

        # Prepare the system prompt
        prompt = system_prompt.format(documents=search_results)

        # Generate chat completion
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": query}
            ],
            stream=stream
        )

        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
