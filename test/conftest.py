import os
import random

from alembic.config import Config

from alembic import command

os.environ["REDIS_URL"] = "memory://"

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.domain.enums import DocumentStatus
from src.infrastructure.api.main import app
from src.infrastructure.config import settings
from src.infrastructure.database.conection import Base, get_db
from src.infrastructure.database.models import DocumentsTable, UsersTable, VectorsTable
from src.infrastructure.security.securityandtokens import (
    PasswordServiceRepositoryInfrastructure,
    TokenServiceRepositoryInfrastructure,
)

DB_URL = settings.DATABASE_URL

if not any(term in DB_URL for term in ("test", "prueba")):
    raise RuntimeError(
        f"❌ PELIGRO: Intentaste correr las pruebas contra una base de datos que NO es de pruebas.\n"
        f"URL actual: {DB_URL}\n"
        f"La URL debe contener la palabra 'test'."
    )

engine = create_engine(url=DB_URL)
SessionTesting = sessionmaker(autoflush=False, autocommit=False, bind=engine)


@pytest.fixture
def mock_log_provider():
    lp = MagicMock()
    return lp


@pytest.fixture(autouse=True)
def create_tables():
    alembic_cfg = Config("alembic.ini")
    engine = create_engine(url=DB_URL)

    with engine.connect() as connection:
        if engine.dialect.name == "postgresql":
            connection.execute(
                text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
            )
            connection.commit()
        else:
            Base.metadata.drop_all(bind=connection)
            connection.commit()
    engine.dispose()

    if engine.dialect.name == "postgresql":
        command.upgrade(alembic_cfg, "head")
    else:
        Base.metadata.create_all(bind=create_engine(url=DB_URL))

    yield


@pytest.fixture
def get_db_test():
    db = SessionTesting()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def cliente():
    def get_db_test():
        db = SessionTesting()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = get_db_test
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def normal_user(get_db_test):
    hashed = PasswordServiceRepositoryInfrastructure().hash_password(
        "hashed_password_mock"
    )
    user = UsersTable(
        username="usernametest",
        email="user@test.com",
        hashed_password=hashed,
    )
    get_db_test.add(user)
    get_db_test.commit()
    get_db_test.refresh(user)
    return user


@pytest.fixture
def token_headers(normal_user):
    token = TokenServiceRepositoryInfrastructure(
        log_provider=MagicMock(),
        SECRET_KEY=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
        expire_token_time=settings.EXPIRE_TOKEN_TIME,
    ).create_token({"sub": normal_user.username})

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def setup_test_data(get_db_test, normal_user):

    db = get_db_test

    document = DocumentsTable(
        filename="fakefilenaasdfme.pdf",
        file_path="fake/fisdfle/path",
        status=DocumentStatus.PENDING,
        user_id=normal_user.id,
    )
    db.add(document)

    document_2 = DocumentsTable(
        filename="fakefilenasdme.pdf",
        file_path="fasdake/fiasdfle/path",
        status=DocumentStatus.PENDING,
        user_id=normal_user.id,
    )
    db.add(document_2)

    db.commit()
    return {
        "user_id": normal_user.id,
        "document_id": document.id,
        "document_id_2": document_2.id,
    }


@pytest.fixture
def normal_document(normal_user, get_db_test):
    documetn = DocumentsTable(
        filename="fakefilename.pdf",
        file_path="fake/file/path",
        status=DocumentStatus.PENDING,
        user_id=normal_user.id,
    )

    get_db_test.add(documetn)
    get_db_test.commit()
    get_db_test.refresh(documetn)
    return documetn


@pytest.fixture
def normal_vectors(normal_document, get_db_test):
    vector = VectorsTable(
        chunk_text="asfjbjavsfafaf",
        embedding=[random.uniform(-1.0, 1.0) for _ in range(3072)],
        owner_id=normal_document.user_id,
        document_id=normal_document.id,
    )

    get_db_test.add(vector)
    get_db_test.commit()
    get_db_test.refresh(vector)
    return vector
