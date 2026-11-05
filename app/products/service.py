from typing import List
from fastapi import BackgroundTasks, Depends, HTTPException, UploadFile, status
from app.database.database import localSession
from app.products.repository import ProductRepository
from app.products.dto.CreateDocument import CreateDocument
from app.knowledge.service import KnowledgeService
from app.knowledge.repository import KnowledgeRepository
from app.auth.dto.MessageResponse import MessageResponse
from app.database.config import upload_dir, max_upload_mb
import logging
import os
import uuid

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

    def create_product(self, data, files: List[UploadFile], current_user, background_tasks: BackgroundTasks):
        if self.repository.get_by_model_number(data.model_number):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Model number already exists")
        self.check_files(files)

        product = self.repository.create(data)
        try:
            self.add_documents(product, files, data.doc_type, current_user, background_tasks)
        except Exception:
            # don't leave a half-created product behind that blocks a retry with "Model number already exists"
            self.repository.delete(product)
            raise
        return product

    def list_products(self, search: str = None, model_number: str = None):
        return self.repository.list(search, model_number)

    def get_product(self, product_id: int):
        product = self.repository.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return product

    def get_product_with_documents(self, product_id: int):
        product = self.get_product(product_id)
        product.documents = self.repository.list_documents(product.id)
        return product

    def update_product(self, product_id: int, data, files: List[UploadFile], current_user, background_tasks: BackgroundTasks):
        product = self.get_product(product_id)
        if data.model_number and data.model_number != product.model_number:
            if self.repository.get_by_model_number(data.model_number):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Model number already exists")
        self.check_files(files)

        product = self.repository.update(product, data)

        # new files replace all the old documents of the product;
        # the old ones are removed only after the new ones are saved, so a failed upload loses nothing
        if files:
            old_documents = self.repository.list_documents(product.id)
            self.add_documents(product, files, data.doc_type, current_user, background_tasks)
            for document in old_documents:
                self.knowledge_service.remove_document(document.id)
                self.repository.delete_document(document)
        return product

    def delete_product(self, product_id: int) -> MessageResponse:
        product = self.get_product(product_id)
        # vectors first: if the knowledge base is down nothing changes, and a deleted product never shows up in answers
        self.knowledge_service.remove_product(product.id)
        self.repository.delete(product)
        return MessageResponse(message="Product deleted")

    def check_files(self, files: List[UploadFile]):
        # check every file (type and size) before saving anything
        for file in files:
            self.read_upload(file)
            file.file.seek(0)

    def add_documents(self, product, files: List[UploadFile], doc_type: str, current_user, background_tasks: BackgroundTasks):
        # save each file as a "pending" document; reading it into the vector store runs after the response is sent
        for file in files:
            title = os.path.splitext(file.filename or "")[0] or "Product document"
            data = CreateDocument(title=title[:255], doc_type=doc_type)
            extension, content = self.read_upload(file)
            file_path = self.store_file(extension, content)
            try:
                document = self.repository.create_document(product.id, data, file.filename, file_path, file.content_type, len(content), current_user.id)
            except Exception:
                remove_file(file_path)
                raise
            background_tasks.add_task(ingest_in_background, document.id)

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
        file_path = os.path.join(upload_dir, f"{uuid.uuid4().hex}{extension}")
        try:
            os.makedirs(upload_dir, exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(content)
        except OSError:
            logger.exception("Saving upload to %s failed", file_path)
            remove_file(file_path)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not save the uploaded file")
        return file_path

    def ingest(self, document_id: int):
        document = self.repository.get_document_by_id(document_id)
        product = self.repository.get_by_id(document.product_id) if document else None
        if not product:
            return

        def on_page(pages_done: int, pages_total: int):
            self.repository.set_progress(document, pages_done, pages_total)
            # stop early when the document was replaced or deleted while it was being read
            if not self.repository.get_document_by_id(document.id):
                raise ValueError("Document was replaced or deleted")

        # a failed ingest is recorded on the document; upload the files again via product update to retry
        try:
            self.knowledge_service.ingest_document(document, product, on_page)
        except Exception:
            logger.exception("Ingest failed for document %s", document.id)
            self.repository.set_ingest_status(document, "failed")
            return
        self.repository.set_ingest_status(document, "ingested")

def remove_file(file_path: str):
    # cleanup must not hide the error that triggered it
    try:
        os.remove(file_path)
    except OSError:
        pass

def ingest_in_background(document_id: int):
    # runs after the response is sent, so it opens its own session; "with" closes it even on errors
    with localSession() as db:
        # Depends() doesn't work outside a request, so build the service by hand
        knowledge_service = KnowledgeService(repository=KnowledgeRepository())
        service = ProductService(repository=ProductRepository(db), knowledge_service=knowledge_service)
        try:
            service.ingest(document_id)
        except Exception:
            logger.exception("Background ingest failed for document %s", document_id)
