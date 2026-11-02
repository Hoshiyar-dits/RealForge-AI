from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from app.database.config import ollama_base_url, embedding_model, chroma_dir, chroma_collection

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
        # Chroma needs "$and" only when there are two conditions
        if doc_types and product_id:
            where = {"$and": [{"doc_type": {"$in": doc_types}}, {"product_id": product_id}]}
        elif doc_types:
            where = {"doc_type": {"$in": doc_types}}
        elif product_id:
            where = {"product_id": product_id}
        else:
            where = None
        return vector_store.similarity_search(query, k=k, filter=where)
