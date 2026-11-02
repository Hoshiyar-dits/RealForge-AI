from sqlalchemy import Column, Integer, String, Enum, TIMESTAMP, ForeignKey, func
from app.database.database import Base

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    doc_type = Column(Enum("manual","repair_guide","specification","other"), nullable=False, default="other")
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    content_type = Column(String(100))
    file_size = Column(Integer)
    ingest_status = Column(Enum("pending","ingested","failed"), nullable=False, default="pending")
    ingested_at = Column(TIMESTAMP)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP)
