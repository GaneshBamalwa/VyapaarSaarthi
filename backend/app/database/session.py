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
    from app.models import order, agent_trace, hitl_queue  # noqa: F401
    Base.metadata.create_all(bind=engine)
