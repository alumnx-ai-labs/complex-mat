from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)

# expire_on_commit=False: get_db() commits before the response is returned, but
# request-scoped objects (e.g. a just-created Task) are still read afterwards by
# FastAPI BackgroundTasks callbacks, which run once the session below has already
# been closed. With the default expire_on_commit=True, that later attribute
# access tries to lazily reload from the closed session and raises
# DetachedInstanceError; disabling it lets already-loaded attributes keep
# serving their cached values after commit.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
