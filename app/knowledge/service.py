from fastapi import Depends
from app.knowledge.repository import KnowledgeRepository

class KnowledgeService():
    def __init__(self, repository: KnowledgeRepository = Depends()):
        self.repository = repository

    def ingest_document(self, document, product, on_page=None):
        # TODO: read the file, split it into chunks and add them to the vector store
        # on_page(pages_done, pages_total) can be called to show progress in the front-end
        # until this is written, uploaded documents are marked "failed"
        raise NotImplementedError("Document ingestion is not written yet")

    def remove_document(self, document_id: int):
        # TODO: called when a product's files are replaced
        pass

    def remove_product(self, product_id: int):
        # TODO: called when a product is deleted
        pass

    def search(self, query: str, k: int, doc_types: list = None, product_id: int = None):
        # TODO: called by the assistant to find relevant chunks
        return []
