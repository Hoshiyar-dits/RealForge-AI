import os
from fastapi import Depends
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_core.documents import Document as Chunk
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.knowledge.repository import KnowledgeRepository

chunk_size = int(os.getenv("RAG_CHUNK_SIZE", "1000"))
chunk_overlap = int(os.getenv("RAG_CHUNK_OVERLAP", "150"))

text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

class KnowledgeService():
    def __init__(self, repository: KnowledgeRepository = Depends()):
        self.repository = repository

    def load(self, file_path: str):
        extension = os.path.splitext(file_path)[1].lower()
        if extension == ".pdf":
            return PyPDFLoader(file_path).load()
        if extension == ".docx":
            return Docx2txtLoader(file_path).load()
        return TextLoader(file_path, autodetect_encoding=True).load()

    def ingest_document(self, document, product):
        chunks = text_splitter.split_documents(self.load(document.file_path))

        prepared = []
        ids = []
        for chunk in chunks:
            if not chunk.page_content.strip():
                continue
            # the product label goes into the text so questions naming the product match its chunks
            text = f"Product: {product.name} (model {product.model_number})\n{chunk.page_content}"
            metadata = {"document_id": document.id, "doc_type": document.doc_type, "title": document.title, "product_id": product.id}
            # only pdf chunks have a page (Chroma metadata cannot hold None)
            if "page" in chunk.metadata:
                metadata["page"] = int(chunk.metadata["page"]) + 1
            prepared.append(Chunk(page_content=text, metadata=metadata))
            ids.append(f"{document.id}-{len(ids)}")

        if not prepared:
            raise ValueError(f"No extractable text in {document.file_name} (scanned PDFs need OCR first)")
        self.repository.delete_by_document(document.id)
        self.repository.add(prepared, ids)

    def remove_document(self, document_id: int):
        self.repository.delete_by_document(document_id)

    def remove_product(self, product_id: int):
        self.repository.delete_by_product(product_id)

    def search(self, query: str, k: int, doc_types: list = None, product_id: int = None):
        return self.repository.search(query, k, doc_types, product_id)
