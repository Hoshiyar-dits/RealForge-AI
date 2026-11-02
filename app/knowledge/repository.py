import os
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
embedding_model = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
chroma_dir = os.getenv("CHROMA_DIR", "chroma_db")
chroma_collection = os.getenv("CHROMA_COLLECTION", "product_knowledge")

# created once when the app starts and shared by every request
vector_store = Chroma(
    collection_name=chroma_collection,
    embedding_function=OllamaEmbeddings(model=embedding_model, base_url=ollama_base_url),
    persist_directory=chroma_dir,
    collection_metadata={"hnsw:space": "cosine"},
)

class KnowledgeRepository():
    def add(self, chunks, ids):
        vector_store.add_documents(chunks, ids=ids)

    def delete_by_document(self, document_id: int):
        vector_store.delete(where={"document_id": document_id})

    def delete_by_product(self, product_id: int):
        vector_store.delete(where={"product_id": product_id})

    def search(self, query: str, k: int, doc_types: list = None, product_id: int = None):
        return vector_store.similarity_search(query, k=k, filter=self.build_filter(doc_types, product_id))

    def search_with_scores(self, query: str, k: int, doc_types: list = None, product_id: int = None):
        # returns (chunk, score) pairs, score 0..1 where higher is closer
        return vector_store.similarity_search_with_relevance_scores(query, k=k, filter=self.build_filter(doc_types, product_id))

    def build_filter(self, doc_types: list = None, product_id: int = None):
        # Chroma needs "$and" only when there are two conditions
        if doc_types and product_id:
            return {"$and": [{"doc_type": {"$in": doc_types}}, {"product_id": product_id}]}
        if doc_types:
            return {"doc_type": {"$in": doc_types}}
        if product_id:
            return {"product_id": product_id}
        return None
