import os
import json
import tqdm
from typing import List, Dict, Any, Generator
from loguru import logger
import openai
from qdrant_client import QdrantClient, models
from fastembed.sparse.bm25 import Bm25
from fastembed.late_interaction import LateInteractionTextEmbedding


os.environ["OPENAI_API_KEY"] = "your openai api key"  # Set your OpenAI API key

def load_documents(
    document_path: str
) -> List[Dict[str, Any]]:
    """
    Load documents from a specified path.
    Args:
        document_path (str): Path to the directory containing JSON files.
    Returns:
        List[Dict[str, Any]]: List of loaded documents.
    """
    try:

        with open(document_path, 'r', encoding='utf-8') as file:
            documents = json.load(file)
        logger.info(f"Documents loaded successfully from {document_path}")
        return documents

    except FileNotFoundError:
        logger.error(f"File not found: {document_path}")
        return []

    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from file: {document_path}")
        return []



def batch_creater(
    documents: List[Dict[str, Any]],
    batch_size: int = 100
) -> Generator[List[Dict[str, Any]], None, None]:
    """    Create batches of documents for processing.
    Args:
        documents (List[Dict[str, Any]]): List of document dictionaries.
        batch_size (int): Size of each batch.
    Yields:
        Generator[List[Dict[str, Any]], None, None]: Batches of documents.
    """

    for i in tqdm.tqdm(range(0, len(documents), batch_size)):
        yield documents[i:i + batch_size]


class QdrantUploader:

    def __init__(
        self,
        qdrant_url: str,
        collection_name: str,
        embedding_model: str = "text-embedding-3-small",
        sparse_model: str = "Qdrant/bm25",
        late_interaction_model: str = "colbert-ir/colbertv2.0",
        batch_size: int = 10,
        document_path: str = "law_data/processed_documents.json"
    )-> None:

        # Initialize QdrantUploader with necessary configurations.
        self.collection_name = collection_name
        self.qdrant_client = QdrantClient(
            url=qdrant_url
        )

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

        # Load documents
        self.documents = load_documents(document_path)
        self.batch_size = batch_size


    def create_client(self):
        """
        Create a Qdrant client.
        Returns:
            QdrantClient: Initialized Qdrant client.
        """

        # Create Dense Embedding
        dense_embeddings = list(self.dense_embedding_model.embeddings.create(
            input = [self.documents[0]["article_summary"]],
            model = self.embedding_model
        ).data[0].embedding)

        # Create late interaction embeddings
        late_interaction_embeddings = list(self.late_interaction_embedding_model.passage_embed(self.documents[0].get("article_summary", "")))

        # Create Vector Configs
        vector_config = {
            "openai-embedding": models.VectorParams(
                size=len(dense_embeddings),
                distance=models.Distance.COSINE
            ),
            "late_interaction": models.VectorParams(
                size= len(late_interaction_embeddings[0][0]),
                distance= models.Distance.COSINE,
                multivector_config= models.MultiVectorConfig(
                    comparator=models.MultiVectorComparator.MAX_SIM
                )
            )
        }

        # Create Sparse Vector Configs
        sparse_vector_config = {
            'bm25': models.SparseVectorParams(
                modifier=models.Modifier.IDF
            )
        }

        self.qdrant_client.create_collection(
            collection_name=self.collection_name,
            vectors_config=vector_config,
            sparse_vectors_config=sparse_vector_config
        )
        logger.info(f"Qdrant client created for collection: {self.collection_name}")

    def upload_documents(self):
        """
        Upload documents to Qdrant in batches.
        """

        try:
            # self.create_client()

            for batch in tqdm.tqdm(batch_creater(self.documents, self.batch_size), total= len(self.documents) // self.batch_size):

                texts = [doc['article_summary'] for doc in batch]
                root_titles = [doc['root_title'] for doc in batch]
                root_summaries = [doc['root_summary'] for doc in batch]
                root_issue_dates = [doc['root_issue_date'] for doc in batch]
                root_effective_dates = [doc['root_effective_date'] for doc in batch]
                chapter_titles = [doc['chapter_title'] for doc in batch]
                chapter_summaries = [doc['chapter_summary'] for doc in batch]
                section_titles = [doc['section_title'] for doc in batch]
                section_summaries = [doc['section_summary'] for doc in batch]
                raw_articles = [doc['raw_articles'] for doc in batch]
                ids = [doc['id'] for doc in batch]

                dense_embeddings = list(self.dense_embedding_model.embeddings.create(input = texts, model=self.embedding_model).data)
                bm25_embeddings = list(self.sparse_embedding_model.passage_embed(texts))
                late_interaction_embeddings = list(self.late_interaction_embedding_model.passage_embed(texts))

                self.qdrant_client.upload_points(
                    collection_name=self.collection_name,
                    points = [
                        models.PointStruct(
                            id = ids[i],
                            vector = {
                                "openai-embedding": list(dense_embeddings[i].embedding),
                                "bm25": bm25_embeddings[i].as_object(),
                                "late_interaction": late_interaction_embeddings[i].tolist(),
                            },
                            payload={
                                "id": ids[i],
                                "root_title": root_titles[i],
                                "root_summary": root_summaries[i],
                                "root_issue_date": root_issue_dates[i],
                                "root_effective_date": root_effective_dates[i],
                                "chapter_title": chapter_titles[i],
                                "chapter_summary": chapter_summaries[i],
                                "section_title": section_titles[i],
                                "section_summary": section_summaries[i],
                                "raw_articles": raw_articles[i]
                            }
                        )
                        for i in range(len(ids))
                    ],
                    batch_size= self.batch_size
                )
            print('Upload data point sucessfully !')

        except Exception as e:
            logger.error(f"Error uploading documents: {e}")
            raise e


if __name__ == "__main__":
    # Example usage
    uploader = QdrantUploader(
        qdrant_url="http://localhost:6333",
        collection_name="legal_documents",
        document_path="/Users/haonguyen/Documents/legal-retrieval-document-with-mlops/src/law_data/processed_documents.json"
    )
    uploader.upload_documents()
