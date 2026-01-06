from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


# Database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./ufc.db"

# Engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()