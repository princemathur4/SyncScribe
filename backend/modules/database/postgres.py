from sqlalchemy import create_engine, Column, Integer, DateTime
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.sql import func
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# Dependency: gives a DB session to each request, closes it after
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
