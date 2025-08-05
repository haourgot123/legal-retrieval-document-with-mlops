import os
import json
import re
from typing import List, Dict, Any, Union, Literal
from loguru import logger


def load_data_from_json(
    file_path: str
) -> Dict[str, Any]:
    """
    Load data from a JSON file.
    Args:
        file_path (str): Path to the JSON file.
    Returns:
        Dict[str, Any]: Parsed JSON data.
    """

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        logger.info(f"Data loaded successfully from {file_path}")
        return data
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from file: {file_path}")
        return {}


class DocumentLoader:
    """
    A class to load and process documents.
    """

    def postprocessing_documents(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Post-process documents to ensure they are in the correct format.
        Args:
            documents (List[Dict[str, Any]]): List of document dictionaries.
        Returns:
            List[Dict[str, Any]]: Processed documents.
        """
        processed_documents = []

        try:

            for doc in documents:
                document = {
                    "root_title": doc.get("root", {}).get("title", ""),
                    "root_summary": doc.get("root", {}).get("summary", ""),
                    "root_issue_date": doc.get("root", {}).get("issue_date", ""),
                    "root_effective_date": doc.get("root", {}).get("effective_date", ""),
                    "chapter_title": doc.get("chapter", {}).get("title", ""),
                    "chapter_summary": doc.get("chapter", {}).get("summary", ""),
                    "section_title": doc.get("section", {}).get("title", ""),
                    "section_summary": doc.get("section", {}).get("summary", ""),
                    "raw_articles": doc.get("articles", [])[0].get("raw_content", "") if doc.get("articles") else "",
                    "article_summary": doc.get("articles", [])[0].get("summary", ""),
                    "id": doc.get("articles", [])[0].get("id", "") if doc.get("articles") else ""
                }

                processed_documents.append(document)
            logger.info("Documents post-processed successfully")
            return processed_documents

        except Exception as e:
            logger.error(f"Error during post-processing documents: {e}")
            return []


    def load_document(
        self,
        data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Load and group document sections.
        Returns:
            List[Dict[str, Any]]: Each item is a dict with root, chapter, section, articles.
        """
        documents = []

        root_info = {
            "level": "root",
            "title": data.get("title", ""),
            "summary": data.get("summary", ""),
            "issue_date": data.get("issue_date", ""),
            "effective_date": data.get("effective_date", "")
        }

        # Helper to create empty chapter/section
        def empty_chapter():
            return {"level": "chapter", "title": "", "summary": ""}

        def empty_section():
            return {"level": "section", "title": "", "summary": ""}

        try:
            for childen in data.get("children", []):
                # Case: chapter level
                if childen.get("level") == "chapter":
                    chapter_info = {
                        "level": "chapter",
                        "title": childen.get("text", ""),
                        "summary": childen.get("summary", "")
                    }
                    # chapter->section->article
                    if "children" in childen:
                        for section in childen.get("children", []):
                            if section.get("level") == "section":
                                section_info = {
                                    "level": "section",
                                    "title": section.get("text", ""),
                                    "summary": section.get("summary", "")
                                }
                                articles = []
                                for article in section.get("children", []):
                                    if article.get("level") == "article":
                                        articles.append({
                                            "level": "article",
                                            "id": article.get("_id", ""),
                                            "raw_content": article.get("text", ""),
                                            "summary": article.get("summary", "")
                                        })
                                if articles:
                                    documents.append({
                                        "root": root_info,
                                        "chapter": chapter_info,
                                        "section": section_info,
                                        "articles": articles
                                    })
                            # chapter->article (no section)
                            elif section.get("level") == "article":
                                articles = [{
                                    "level": "article",
                                    "id": section.get("_id", ""),
                                    "raw_content": section.get("text", ""),
                                    "summary": section.get("summary", "")
                                }]
                                documents.append({
                                    "root": root_info,
                                    "chapter": chapter_info,
                                    "section": empty_section(),
                                    "articles": articles
                                })
                # Case: root->article (no chapter/section)
                elif childen.get("level") == "article":
                    articles = [{
                        "level": "article",
                        "id": childen.get("_id", ""),
                        "raw_content": childen.get("text", ""),
                        "summary": childen.get("summary", "")
                    }]
                    documents.append({
                        "root": root_info,
                        "chapter": empty_chapter(),
                        "section": empty_section(),
                        "articles": articles
                    })

            logger.info(f"Total documents processed: {len(documents)}")
            return documents

        except Exception as e:
            logger.error(f"Error processing document: {e}")
            return []

    def runs(
        self,
        data_dir: str
    ) -> List[Dict[str, Any]]:
        """
        Load and group document sections from a directory of JSON files.
        Args:
            data_dir (str): Directory containing JSON files.
        Returns:
            List[Dict[str, Any]]: Each item is a dict with root, chapter, section, articles.
        """
        documents = []
        try:
            for root, dirs, files in os.walk(data_dir):
                logger.info(f"Processing directory: {root}")
                for file in files:
                    if file.endswith('.json'):
                        file_path = os.path.join(root, file)
                        logger.info(f"---Loading file: {file_path}")
                        data = load_data_from_json(file_path)
                        if data:
                            loaded_docs = self.load_document(data)
                            documents.extend(loaded_docs)

            logger.info(f"Total files processed: {len(files)}")
            logger.info(f"Total documents loaded: {len(documents)}")
            documents = self.postprocessing_documents(documents)
            logger.info("Documents loaded and processed successfully")
            return documents

        except Exception as e:
            logger.error(f"Error during document loading: {e}")
            return []


if __name__ == "__main__":
    # Example usage
    loader = DocumentLoader()
    docs = loader.runs("/Users/haonguyen/Documents/legal-retrieval-document-with-mlops/src/law_data/processed")
    with open("/Users/haonguyen/Documents/legal-retrieval-document-with-mlops/src/law_data/processed_documents.json", "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=4)
