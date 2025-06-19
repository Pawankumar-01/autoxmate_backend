from sqlmodel import SQLModel, create_engine, Session

from models import WhatsAppConfig
sqlite_url = "sqlite:///./database.db"
engine = create_engine(sqlite_url, echo=True)


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


def init_db():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        # Ensure one config row exists
        config = session.get(WhatsAppConfig, 1)
        if not config:
            session.add(WhatsAppConfig(
                accessToken='',
                phoneNumberId='',
                businessAccountId='',
                isConfigured=False
            ))
            session.commit()
