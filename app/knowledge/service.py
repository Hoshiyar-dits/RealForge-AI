import logging
import os
import pytesseract
from fastapi import Depends, HTTPException, status
from pdf2image import convert_from_path
from pypdf import apply_configuration
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_core.documents import Document as Chunk
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.knowledge.repository import KnowledgeRepository
from app.database.config import chunk_size, chunk_overlap, ocr_dpi, pdf_parsing_limit

text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

logger = logging.getLogger(__name__)

class KnowledgeService():
    def __init__(self, repository: KnowledgeRepository = Depends()):
        self.repository = repository

    def load(self, file_path: str, on_page=None):
        extension = os.path.splitext(file_path)[1].lower()
        if extension == ".pdf":
            return self.load_pdf(file_path, on_page)
        if extension == ".docx":
            return Docx2txtLoader(file_path).load()
        return TextLoader(file_path, autodetect_encoding=True).load()

    def load_pdf(self, file_path: str, on_page=None):
        with apply_configuration(stream_parsing_work_maximum_count=pdf_parsing_limit):
            pages = PyPDFLoader(file_path).load()
        for number, page in enumerate(pages, start=1):
            if not page.page_content.strip():
                # no text on this page (a scan, or text drawn as shapes): draw the page as an image and OCR it
                page.page_content = self.read_page_image(file_path, number)
            # tell the caller how far we are, e.g. on_page(7, 38)
            if on_page:
                on_page(number, len(pages))
        return pages

    def read_page_image(self, file_path: str, page_number: int) -> str:
        image = convert_from_path(file_path, dpi=ocr_dpi, first_page=page_number, last_page=page_number)[0]
        return pytesseract.image_to_string(image)

    def ingest_document(self, document, product, on_page=None):
        chunks = text_splitter.split_documents(self.load(document.file_path, on_page))

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
            raise ValueError(f"No extractable text in {document.file_name}")
        self.repository.delete_by_document(document.id)
        self.repository.add(prepared, ids)

    def remove_document(self, document_id: int):
        try:
            self.repository.delete_by_document(document_id)
        except Exception:
            logger.exception("Removing vectors failed for document %s", document_id)
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Knowledge base is unavailable, please try again")

    def remove_product(self, product_id: int):
        try:
            self.repository.delete_by_product(product_id)
        except Exception:
            logger.exception("Removing vectors failed for product %s", product_id)
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Knowledge base is unavailable, please try again")

    def search(self, query: str, k: int, doc_types: list = None, product_id: int = None):
        return self.repository.search(query, k, doc_types, product_id)
