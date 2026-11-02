from typing import List
from fastapi import Depends, HTTPException, UploadFile, status
from app.products.repository import ProductRepository
from app.products.dto.CreateDocument import CreateDocument
from app.knowledge.service import KnowledgeService
from app.auth.dto.MessageResponse import MessageResponse
import logging
import os
import uuid

upload_dir = os.getenv("UPLOAD_DIR", "uploads")
max_upload_mb = int(os.getenv("MAX_UPLOAD_MB", "20"))
allowed_extensions = {".pdf", ".txt", ".md", ".docx"}

logger = logging.getLogger(__name__)

class ProductService():
    def __init__(
        self,
        repository: ProductRepository = Depends(),
        knowledge_service: KnowledgeService = Depends(),
    ):
        self.repository = repository
        self.knowledge_service = knowledge_service

    def create_product(self, data, files: List[UploadFile], current_user):
        if self.repository.get_by_model_number(data.model_number):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Model number already exists")
        self.check_files(files)

        product = self.repository.create(data)
        self.add_documents(product, files, data.doc_type, current_user)
        return product

    def list_products(self, search: str = None, model_number: str = None):
        return self.repository.list(search, model_number)

    def get_product(self, product_id: int):
        product = self.repository.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return product

    def update_product(self, product_id: int, data, files: List[UploadFile], current_user):
        product = self.get_product(product_id)
        if data.model_number and data.model_number != product.model_number:
            if self.repository.get_by_model_number(data.model_number):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Model number already exists")
        self.check_files(files)

        product = self.repository.update(product, data)

        # new files replace all the old documents of the product
        if files:
            for document in self.repository.list_documents(product.id):
                self.repository.delete_document(document)
                self.knowledge_service.remove_document(document.id)
            self.add_documents(product, files, data.doc_type, current_user)
        return product

    def delete_product(self, product_id: int) -> MessageResponse:
        product = self.get_product(product_id)
        self.repository.delete(product)
        self.knowledge_service.remove_product(product.id)
        return MessageResponse(message="Product deleted")

    def check_files(self, files: List[UploadFile]):
        # check every file (type and size) before saving anything
        for file in files:
            self.read_upload(file)
            file.file.seek(0)

    def add_documents(self, product, files: List[UploadFile], doc_type: str, current_user):
        # save each file as a product document and add it to the vector store
        for file in files:
            title = os.path.splitext(file.filename or "")[0] or "Product document"
            data = CreateDocument(title=title[:255], doc_type=doc_type)
            extension, content = self.read_upload(file)
            file_path = self.store_file(extension, content)
            try:
                document = self.repository.create_document(product.id, data, file.filename, file_path, file.content_type, len(content), current_user.id)
            except Exception:
                os.remove(file_path)
                raise
            self.ingest(document, product)

    def read_upload(self, file: UploadFile):
        extension = os.path.splitext(file.filename or "")[1].lower()
        if extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {', '.join(sorted(allowed_extensions))} files are allowed",
            )

        max_bytes = max_upload_mb * 1024 * 1024
        content = file.file.read(max_bytes + 1)
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=f"File is larger than {max_upload_mb} MB",
            )
        return extension, content

    def store_file(self, extension: str, content: bytes) -> str:
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, f"{uuid.uuid4().hex}{extension}")
        with open(file_path, "wb") as f:
            f.write(content)
        return file_path

    def ingest(self, document, product):
        # a failed ingest is recorded on the document; upload the files again via product update to retry
        try:
            self.knowledge_service.ingest_document(document, product)
        except Exception:
            logger.exception("Ingest failed for document %s", document.id)
            return self.repository.set_ingest_status(document, "failed")
        return self.repository.set_ingest_status(document, "ingested")
