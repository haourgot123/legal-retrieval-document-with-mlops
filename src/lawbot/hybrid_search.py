import os
from typing import List, Dict, Any, Generator
from loguru import logger
import openai
from qdrant_client import QdrantClient, models
from fastembed.sparse.bm25 import Bm25
from fastembed.late_interaction import LateInteractionTextEmbedding
from dotenv import load_dotenv

load_dotenv()



class HybridSearch:

    def __init__(
        self,
        embedding_model: str = "text-embedding-3-small",
        sparse_model: str = "Qdrant/bm25",
        late_interaction_model: str = "colbert-ir/colbertv2.0",
        collection_name: str = "legal_documents",
        qdrant_url: str = "http://qdrant.database.svc.cluster.local:6333",
        threshold: float = 0.3
    ) -> None:
        """
        Initialize the HybridSearch class with models.
        Args:
            embedding_model (str): Name of the OpenAI embedding model.
            sparse_model (str): Name of the sparse model for BM25.
            late_interaction_model (str): Name of the late interaction model.
        """

        # OpenAI Embedding Configs
        self.dense_embedding_model = openai.Client(
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        self.embedding_model = embedding_model

        # Sparse and Late Interaction Embedding Configs
        self.sparse_embedding_model = Bm25(
            model_name=sparse_model
        )

        # Late Interaction Embedding Configs
        self.late_interaction_embedding_model = LateInteractionTextEmbedding(
            model_name=late_interaction_model
        )

        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(
            url=qdrant_url
        )
        self.collection_name = collection_name
        self.threshold = threshold

    def query(
        self,
        query: str,
    ) -> List[Dict[str, Any]]:
        """
        Perform a hybrid search using the provided query.
        Args:
            query (str): The search query.
        Returns:
            List[Dict[str, Any]]: List of documents matching the query.
        """

        # Create dense embeddings
        dense_embeddings_query = self.dense_embedding_model.embeddings.create(
            input=query,
            model=self.embedding_model
        ).data[0].embedding

        # Create late interaction embeddings
        late_interaction_embeddings_query= next(self.late_interaction_embedding_model.query_embed(query))

        # Create sparse embeddings
        bm25_embeddings_query = next(self.sparse_embedding_model.query_embed(query))

        prefetch = [
            models.Prefetch(
                query=dense_embeddings_query,
                using="openai-embedding",
                limit=10
            ),

            models.Prefetch(
                query=models.SparseVector(**bm25_embeddings_query.as_object()),
                using="bm25",
                limit=10
            ),

            models.Prefetch(
                query=late_interaction_embeddings_query,
                using="late_interaction",
                limit=10
            )
        ]

        responses = self.qdrant_client.query_points(
            collection_name=self.collection_name,
            prefetch=prefetch,
            query=models.FusionQuery(
                fusion=models.Fusion.RRF
            ),
            with_payload=True,
            limit=5,
        )


        docs = ""
        for i, response in enumerate(responses.points):
            if response.score >= self.threshold:
                doc = response.payload
                docs += f"Document {i+1}:\n"
                docs += f"Title: {doc.get('root_title', '')}\n"
                docs += f"Summary: {doc.get('root_summary', '')}\n"
                docs += f"Issue Date: {doc.get('root_issue_date', '')}\n"
                docs += f"Effective Date: {doc.get('root_effective_date', '')}\n"
                docs += f"Chapter Title: {doc.get('chapter_title', '')}\n"
                docs += f"Chapter Summary: {doc.get('chapter_summary', '')}\n"
                docs += f"Section Title: {doc.get('section_title', '')}\n"
                docs += f"Section Summary: {doc.get('section_summary', '')}\n"
                docs += f"Raw Articles: {doc.get('raw_articles', '')}\n\n"

        return docs.strip() if docs else "No relevant documents found."



if __name__ == "__main__":
    hybrid_search = HybridSearch()
    query = "Giết người có bị xử lý hình sự không?"
    results = hybrid_search.query(query)
    print(results)
