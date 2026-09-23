import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

load_dotenv()

class KnowledgeBaseService:
    def __init__(self):
        self.endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.key = os.getenv("AZURE_SEARCH_KEY")
        self.index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "language-learning-kb")

        if self.endpoint and self.key:
            self.client = SearchClient(
                endpoint=self.endpoint,
                index_name=self.index_name,
                credential=AzureKeyCredential(self.key)
            )
        else:
            self.client = None

    def retrieve_context(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Queries Azure AI Search for relevant curriculum and grammar context."""
        if not self.client:
            # Safe offline fallback
            return [{"content": f"Grammar & vocab reference for '{query}' (offline fallback).", "source": "local_cache"}]

        try:
            results = self.client.search(search_text=query, top=top_k)
            docs = []
            for doc in results:
                docs.append({
                    "content": doc.get("content") or doc.get("text") or str(doc),
                    "title": doc.get("title", "Curriculum Doc")
                })
            return docs
        except Exception as e:
            return [{"content": f"Default language rule: {e}", "source": "error_fallback"}]
