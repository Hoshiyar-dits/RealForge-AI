from typing import List
from fastapi import BackgroundTasks, Depends, HTTPException, UploadFile, status
from app.database.database import localSession
from app.products.repository import ProductRepository
from app.products.dto.CreateDocument import CreateDocument
from app.knowledge.service import KnowledgeService
from app.knowledge.repository import KnowledgeRepository
from app.roles.repository import RoleRepository
from app.auth.dto.MessageResponse import MessageResponse
from app.products.dto.SearchResultResponse import SearchResultResponse
import logging
import os
import uuid

upload_dir = os.getenv("UPLOAD_DIR", "uploads")
max_upload_mb = int(os.getenv("MAX_UPLOAD_MB", "20"))
allowed_extensions = {".pdf", ".txt", ".md", ".docx"}
# repair guides are for technicians only; users without this permission never get their chunks
repair_guide_permission = "assistant.technician"
all_doc_types = ["manual", "repair_guide", "specification", "other"]

logger = logging.getLogger(__name__)

class ProductService():
    def __init__(
        self,
        repository: ProductRepository = Depends(),
        knowledge_service: KnowledgeService = Depends(),
        role_repository: RoleRepository = Depends(),
    ):
        self.repository = repository
        self.knowledge_service = knowledge_service
        self.role_repository = role_repository

    def create_product(self, data, files: List[UploadFile], current_user, background_tasks: BackgroundTasks):
        if self.repository.get_by_model_number(data.model_number):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Model number already exists")
        self.check_files(files)

        product = self.repository.create(data)
        self.add_documents(product, files, data.doc_type, current_user, background_tasks)
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

        # new files replace all the old documents of the product
        if files:
            for document in self.repository.list_documents(product.id):
                self.repository.delete_document(document)
                self.knowledge_service.remove_document(document.id)
            self.add_documents(product, files, data.doc_type, current_user, background_tasks)
        return product

    def delete_product(self, product_id: int) -> MessageResponse:
        product = self.get_product(product_id)
        self.repository.delete(product)
        self.knowledge_service.remove_product(product.id)
        return MessageResponse(message="Product deleted")

    def list_documents(self, product_id: int):
        product = self.get_product(product_id)
        return self.repository.list_documents(product.id)

    def get_document(self, product_id: int, document_id: int):
        document = self.repository.get_document_by_id(document_id)
        if not document or document.product_id != product_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return document

    def reingest_document(self, product_id: int, document_id: int, background_tasks: BackgroundTasks):
        document = self.get_document(product_id, document_id)
        if document.ingest_status in ("pending", "processing"):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Document is already being ingested")
        document = self.repository.reset_ingest(document)
        background_tasks.add_task(ingest_in_background, document.id)
        return document

    def delete_document(self, product_id: int, document_id: int) -> MessageResponse:
        document = self.get_document(product_id, document_id)
        self.repository.delete_document(document)
        self.knowledge_service.remove_document(document.id)
        return MessageResponse(message="Document deleted")

    def search_product(self, product_id: int, data, current_user):
        product = self.get_product(product_id)
        doc_types = all_doc_types
        if repair_guide_permission not in self.role_repository.get_user_permission_names(current_user.id):
            doc_types = [doc_type for doc_type in all_doc_types if doc_type != "repair_guide"]

        results = self.knowledge_service.search_with_scores(data.query, data.k, doc_types, product.id)
        return [
            SearchResultResponse(
                document_id=chunk.metadata["document_id"],
                title=chunk.metadata["title"],
                doc_type=chunk.metadata["doc_type"],
                page=chunk.metadata.get("page"),
                content=chunk.page_content,
                score=round(score, 4),
            )
            for chunk, score in results
        ]

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
                os.remove(file_path)
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
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, f"{uuid.uuid4().hex}{extension}")
        with open(file_path, "wb") as f:
            f.write(content)
        return file_path

    def ingest(self, document_id: int):
        document = self.repository.get_document_by_id(document_id)
        product = self.repository.get_by_id(document.product_id) if document else None
        if not product:
            return

        self.repository.set_ingest_status(document, "processing")

        def on_page(pages_done: int, pages_total: int):
            self.repository.set_progress(document, pages_done, pages_total)
            # stop early when the document was replaced or deleted while it was being read
            if not self.repository.get_document_by_id(document.id):
                raise ValueError("Document was replaced or deleted")

        # a failed ingest is recorded on the document; retry via POST /product/{id}/documents/{document_id}/ingest
        try:
            self.knowledge_service.ingest_document(document, product, on_page)
        except Exception:
            logger.exception("Ingest failed for document %s", document.id)
            self.repository.set_ingest_status(document, "failed")
            return
        # deleted after its last page was read: drop the vectors that were just added
        if not self.repository.get_document_by_id(document.id):
            self.knowledge_service.remove_document(document.id)
            return
        self.repository.set_ingest_status(document, "completed")

def ingest_in_background(document_id: int):
    # runs after the response is sent, when the request's DB session is already closed, so it opens its own
    db = localSession()
    try:
        ProductService(ProductRepository(db), KnowledgeService(KnowledgeRepository()), RoleRepository(db)).ingest(document_id)
    finally:
        db.close()
