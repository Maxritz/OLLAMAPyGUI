# rag/knowledge_base.py
import chromadb
from typing import List, Dict
import requests
from bs4 import BeautifulSoup

class KnowledgeBase:
    def __init__(self, collection_name="ollama_knowledge_base"):
        self.client = chromadb.Client()
        self.collection = self.client.create_collection(name=collection_name)

    def add_document(self, content: str, metadata: Dict = None) -> bool:
        try:
            self.collection.add(
                documents=[content],
                metadatas=[metadata or {}],
                ids=[str(datetime.now().timestamp())]
            )
            return True
        except Exception as e:
            return False

    def add_url(self, url: str) -> bool:
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            content = soup.get_text()
            return self.add_document(content, {"source": url})
        except Exception as e:
            return False
