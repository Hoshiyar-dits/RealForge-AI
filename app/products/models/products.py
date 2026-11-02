from sqlalchemy import Column, Integer, String, Text, Enum, TIMESTAMP, func
from app.database.database import Base

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    brand = Column(String(255))
    model_number = Column(String(255), nullable=False, index=True)
    category = Column(String(255))
    description = Column(Text)
    status = Column(Enum("0","1"), nullable=False, default="1")
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP)
