from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from sqlalchemy.pool import StaticPool
from typing import Generator
from app.core.config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    pass


def _create_engine():
    if "sqlite" in settings.DATABASE_URL:
        return create_engine(
            settings.DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=settings.DATABASE_ECHO,
        )
    return create_engine(settings.DATABASE_URL, echo=settings.DATABASE_ECHO)


engine = _create_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    # Safe migration: add customer_phone column to orders if not present.
    # SQLite does not support IF NOT EXISTS on ALTER TABLE so we use try/except.
    with engine.connect() as conn:
        try:
            conn.execute(__import__('sqlalchemy').text("ALTER TABLE orders ADD COLUMN customer_phone VARCHAR(20)"))
            conn.commit()
        except Exception:
            pass  # column already exists — ignore
        try:
            conn.execute(__import__('sqlalchemy').text("ALTER TABLE orders ADD COLUMN payment_status VARCHAR(50) DEFAULT 'PENDING'"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(__import__('sqlalchemy').text("ALTER TABLE orders ADD COLUMN telegram_chat_id VARCHAR(50)"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(__import__('sqlalchemy').text("ALTER TABLE buyers ADD COLUMN telegram_chat_id VARCHAR(50)"))
            conn.commit()
        except Exception:
            pass
