from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.database.config import db_url

engine = create_engine(db_url)

localSession = sessionmaker(bind=engine)

Base = declarative_base()

def get_db():
    db = localSession()
    try:
        yield db
    finally:
        db.close()