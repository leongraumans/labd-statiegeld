from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from statiegeld.models import Base

DB_PATH = Path(__file__).parent.parent.parent / "statiegeld.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_conn, connection_record):
    """Tune SQLite for performance on Raspberry Pi (SD card I/O)."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=-8000")  # 8 MB page cache
    cursor.execute("PRAGMA busy_timeout=5000")  # 5 sec wait on lock
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.close()


SessionLocal = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
