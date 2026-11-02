from app.database.database import get_db
from app.products.models.products import Product
from app.products.models.documents import Document
from fastapi import Depends
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
class ProductRepository():
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def create(self, data):
        try:
            product = Product(
                name=data.name,
                model_number=data.model_number,
                brand=data.brand,
                category=data.category,
                description=data.description,
            )
            self.db.add(product)
            self.db.commit()
            self.db.refresh(product)
            return product
        except Exception:
            self.db.rollback()
            raise

    def get_by_id(self, product_id: int):
        return self.db.query(Product).filter(Product.id == product_id, Product.deleted_at.is_(None)).first()

    def get_by_model_number(self, model_number: str):
        return self.db.query(Product).filter(Product.model_number == model_number, Product.deleted_at.is_(None)).first()

    def list(self, search: str = None, model_number: str = None):
        query = self.db.query(Product).filter(Product.deleted_at.is_(None))
        if model_number:
            query = query.filter(Product.model_number == model_number)
        if search:
            pattern = f"%{search}%"
            query = query.filter(or_(
                Product.name.ilike(pattern),
                Product.model_number.ilike(pattern),
                Product.brand.ilike(pattern),
            ))
        return query.order_by(Product.id.desc()).all()

    def update(self, product: Product, data):
        try:
            # doc_type belongs to the uploaded files, not the product
            for field, value in data.model_dump(exclude_none=True, exclude={"doc_type"}).items():
                setattr(product, field, value)
            self.db.commit()
            self.db.refresh(product)
            return product
        except Exception:
            self.db.rollback()
            raise

    def delete(self, product: Product):
        try:
            # documents belong to the product, so soft-delete them with it
            self.db.query(Document).filter(Document.product_id == product.id, Document.deleted_at.is_(None)).update({Document.deleted_at: func.now()})
            product.deleted_at = func.now()
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def create_document(self, product_id: int, data, file_name: str, file_path: str, content_type: str, file_size: int, uploaded_by: int):
        try:
            document = Document(
                product_id=product_id,
                title=data.title,
                doc_type=data.doc_type,
                file_name=file_name,
                file_path=file_path,
                content_type=content_type,
                file_size=file_size,
                uploaded_by=uploaded_by,
            )
            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)
            return document
        except Exception:
            self.db.rollback()
            raise

    def get_document_by_id(self, document_id: int):
        return self.db.query(Document).filter(Document.id == document_id, Document.deleted_at.is_(None)).first()

    def list_documents(self, product_id: int):
        return self.db.query(Document).filter(Document.product_id == product_id, Document.deleted_at.is_(None)).order_by(Document.id.desc()).all()

    def set_progress(self, document: Document, pages_done: int, pages_total: int):
        try:
            document.pages_done = pages_done
            document.pages_total = pages_total
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def set_ingest_status(self, document: Document, ingest_status: str):
        try:
            document.ingest_status = ingest_status
            document.ingested_at = func.now() if ingest_status == "ingested" else None
            self.db.commit()
            self.db.refresh(document)
            return document
        except Exception:
            self.db.rollback()
            raise

    def delete_document(self, document: Document):
        try:
            document.deleted_at = func.now()
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
