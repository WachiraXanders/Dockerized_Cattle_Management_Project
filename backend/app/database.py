import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# DATABASE_URL, if set, takes full precedence — this is how you point the
# app at Postgres (or any other SQLAlchemy-supported database) in
# production/Docker. Without it, falls back to a local SQLite file.
SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    DB_PATH = os.environ.get("DAIRYPRO_DB_PATH", os.path.join(os.path.dirname(__file__), "..", "dairypro.db"))
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
