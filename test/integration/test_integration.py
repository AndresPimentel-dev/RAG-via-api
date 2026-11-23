import pytest
from sqlalchemy import select

from src.domain.enums import DocumentStatus
from src.domain.exceptions import InfrastructureException
from src.infrastructure.database.models import VectorsTable
from src.infrastructure.database.repositories import (
    PDFDatabaseRepositoryInfrastructure,
    UserDatabaseRepositoryInfrastructure,
    VectorDatabaseRepositoryInfrastructure,
)
from src.infrastructure.logging.logging import LogProviderInfrastructure

###############################################################
# User Database Repository Infrastructure Integration Tests
###############################################################


def test_create_user(get_db_test):
    db = get_db_test
    logger = LogProviderInfrastructure()
    repo = UserDatabaseRepositoryInfrastructure(db=db, log_provider=logger)

    response = repo.create_user(
        username="FakeUsername", email="FakeEmail@gmail.com", hashed_password="fakehash"
    )

    assert response.email == "FakeEmail@gmail.com"
    assert response.username == "FakeUsername"


def test_get_user_by_username(normal_user, get_db_test):
    db = get_db_test
    logger = LogProviderInfrastructure()
    repo = UserDatabaseRepositoryInfrastructure(db=db, log_provider=logger)

    response = repo.get_user_by_username(username="usernametest")

    assert response is not None
    assert response.email == normal_user.email
    assert response.username == normal_user.username


def test_get_nonexisting_user_by_username(get_db_test):
    db = get_db_test
    logger = LogProviderInfrastructure()
    repo = UserDatabaseRepositoryInfrastructure(db=db, log_provider=logger)

    response = repo.get_user_by_username(username="nonexisnting")

    assert response is None


def test_get_user_by_email(get_db_test, normal_user):
    db = get_db_test
    logger = LogProviderInfrastructure()
    repo = UserDatabaseRepositoryInfrastructure(db=db, log_provider=logger)

    response = repo.get_user_by_email(email="user@test.com")

    assert response is not None
    assert response.username == normal_user.username
    assert response.email == normal_user.email


def test_get_nonexisting_user_by_email(get_db_test):
    db = get_db_test
    logger = LogProviderInfrastructure()
    repo = UserDatabaseRepositoryInfrastructure(db=db, log_provider=logger)

    response = repo.get_user_by_email(email="user@tessassdasdst.com")

    assert response is None


###############################################################
# Vector Database Repository Infrastructure Integration Tests
###############################################################


def test_insert_embeddings_success(get_db_test, mock_log_provider, setup_test_data):
    """Prueba la inserción exitosa de múltiples chunks y embeddings."""
    repo = VectorDatabaseRepositoryInfrastructure(db=get_db_test, lp=mock_log_provider)
    user_id = setup_test_data["user_id"]
    document_id = setup_test_data["document_id"]

    chunks = ["Este es el chunk 1", "Este es el chunk 2"]
    embeddings = [[0.1] * 3072, [0.2] * 3072]

    response = repo.insert_embeddings(
        document_id=document_id,
        user_id=user_id,
        chunks=chunks,
        embeddings=embeddings,
    )

    assert response is None
    mock_log_provider.error_log.assert_not_called()

    saved_vectors = get_db_test.scalars(
        select(VectorsTable).where(VectorsTable.document_id == document_id)
    ).all()
    assert len(saved_vectors) == 2
    assert saved_vectors[0].chunk_text == "Este es el chunk 1"
    assert saved_vectors[0].owner_id == user_id


def test_insert_embeddings_edge_case_empty_lists(
    get_db_test, mock_log_provider, setup_test_data
):
    """Edge case: Intentar insertar listas vacías de chunks y embeddings."""
    repo = VectorDatabaseRepositoryInfrastructure(db=get_db_test, lp=mock_log_provider)
    user_id = setup_test_data["user_id"]
    document_id = setup_test_data["document_id"]

    response = repo.insert_embeddings(
        document_id=document_id, user_id=user_id, chunks=[], embeddings=[]
    )

    assert response is None
    saved_vectors = get_db_test.scalars(
        select(VectorsTable).where(VectorsTable.document_id == document_id)
    ).all()
    assert len(saved_vectors) == 0


def test_insert_embeddings_infrastructure_exception(get_db_test, mock_log_provider):
    repo = VectorDatabaseRepositoryInfrastructure(db=get_db_test, lp=mock_log_provider)

    # IDs que no existen en la base de datos de prueba
    invalid_user_id = 9999
    invalid_doc_id = 9999
    chunks = ["Chunk de prueba"]
    embeddings = [[0.1] * 3072]

    with pytest.raises(InfrastructureException) as exc_info:
        repo.insert_embeddings(
            document_id=invalid_doc_id,
            user_id=invalid_user_id,
            chunks=chunks,
            embeddings=embeddings,
        )

    assert "error inserting new vectors" in str(exc_info.value)
    mock_log_provider.error_log.assert_called_once()
    _args, kwargs = mock_log_provider.error_log.call_args
    assert f"user_id:{invalid_user_id}" in kwargs.get("context", "")


def test_search_similar_without_document_id(
    get_db_test, mock_log_provider, setup_test_data
):
    repo = VectorDatabaseRepositoryInfrastructure(db=get_db_test, lp=mock_log_provider)
    user_id = setup_test_data["user_id"]
    doc_1 = setup_test_data["document_id"]
    doc_2 = setup_test_data["document_id_2"]

    repo.insert_embeddings(
        document_id=doc_1,
        user_id=user_id,
        chunks=["Python es genial"],
        embeddings=[[0.1] * 3072],
    )
    repo.insert_embeddings(
        document_id=doc_2,
        user_id=user_id,
        chunks=["Me gusta la base de datos"],
        embeddings=[[0.2] * 3072],
    )

    # Búsqueda general
    results = repo.search_similar(
        user_id=user_id, query_embeddings=[0.15] * 3072, top_k=5
    )

    assert isinstance(results, list)
    assert len(results) == 2
    assert "Python es genial" in results


def test_search_similar_with_document_id(
    get_db_test, mock_log_provider, setup_test_data
):
    repo = VectorDatabaseRepositoryInfrastructure(db=get_db_test, lp=mock_log_provider)
    user_id = setup_test_data["user_id"]
    doc_1 = setup_test_data["document_id"]
    doc_2 = setup_test_data["document_id_2"]

    repo.insert_embeddings(
        document_id=doc_1,
        user_id=user_id,
        chunks=["Chunk del documento 1"],
        embeddings=[[0.1] * 3072],
    )
    repo.insert_embeddings(
        document_id=doc_2,
        user_id=user_id,
        chunks=["Chunk del documento 2"],
        embeddings=[[0.9] * 3072],
    )

    results = repo.search_similar(
        user_id=user_id,
        query_embeddings=[0.1] * 3072,
        document_id=doc_1,
        top_k=5,
    )

    assert len(results) == 1
    assert results[0] == "Chunk del documento 1"


def test_search_similar_edge_case_no_matches(
    get_db_test, mock_log_provider, setup_test_data
):
    repo = VectorDatabaseRepositoryInfrastructure(db=get_db_test, lp=mock_log_provider)
    user_id = setup_test_data["user_id"]

    results = repo.search_similar(
        user_id=user_id, query_embeddings=[0.5] * 3072, top_k=5
    )

    assert results == []


def test_delete_context_success(get_db_test, mock_log_provider, setup_test_data):
    repo = VectorDatabaseRepositoryInfrastructure(db=get_db_test, lp=mock_log_provider)
    user_id = setup_test_data["user_id"]
    document_id = setup_test_data["document_id"]

    repo.insert_embeddings(
        document_id=document_id,
        user_id=user_id,
        chunks=["Para borrar"],
        embeddings=[[0.1] * 3072],
    )

    vectors_before = get_db_test.scalars(
        select(VectorsTable).where(VectorsTable.document_id == document_id)
    ).all()
    assert len(vectors_before) == 1

    response = repo.delete_context(document_id=document_id, user_id=user_id)
    assert response is None

    vectors_after = get_db_test.scalars(
        select(VectorsTable).where(VectorsTable.document_id == document_id)
    ).all()
    assert len(vectors_after) == 0


def test_delete_context_edge_case_non_existent(
    get_db_test, mock_log_provider, setup_test_data
):
    repo = VectorDatabaseRepositoryInfrastructure(db=get_db_test, lp=mock_log_provider)
    user_id = setup_test_data["user_id"]
    non_existent_doc_id = 8888

    response = repo.delete_context(document_id=non_existent_doc_id, user_id=user_id)
    assert response is None
    mock_log_provider.error_log.assert_not_called()


###############################################################
# Document Database Repository Infrastructure Integration Tests
###############################################################


def test_create_document_success(get_db_test, mock_log_provider, normal_user):
    repo = PDFDatabaseRepositoryInfrastructure(
        db=get_db_test, log_provider=mock_log_provider
    )
    user_id = normal_user.id

    filename = "manual_usuario.pdf"
    file_path = "/uploads/manual_usuario.pdf"
    status = DocumentStatus.PENDING

    doc_entity = repo.create_document(
        filename=filename, file_path=file_path, user_id=user_id, status=status
    )

    assert doc_entity is not None
    assert doc_entity.filename == filename
    assert doc_entity.file_path == file_path
    assert doc_entity.user_id == user_id
    assert doc_entity.id is not None
    mock_log_provider.error_log.assert_not_called()


def test_create_document_edge_case_duplicate_filepath(
    get_db_test, mock_log_provider, normal_user
):
    repo = PDFDatabaseRepositoryInfrastructure(
        db=get_db_test, log_provider=mock_log_provider
    )
    user_id = normal_user.id

    file_path = "/uploads/duplicado.pdf"

    repo.create_document(
        filename="doc1.pdf",
        file_path=file_path,
        user_id=user_id,
        status=DocumentStatus.PENDING,
    )

    with pytest.raises(InfrastructureException) as exc_info:
        repo.create_document(
            filename="doc2.pdf",
            file_path=file_path,
            user_id=user_id,
            status=DocumentStatus.PENDING,
        )

    assert "error creating document" in str(exc_info.value)
    mock_log_provider.error_log.assert_called_once()


def test_get_document_success(get_db_test, mock_log_provider, normal_user):
    repo = PDFDatabaseRepositoryInfrastructure(
        db=get_db_test, log_provider=mock_log_provider
    )
    user_id = normal_user.id

    created = repo.create_document(
        filename="reporte.pdf",
        file_path="/uploads/reporte.pdf",
        user_id=user_id,
        status=DocumentStatus.PROCESSED,
    )

    fetched = repo.get_document(document_id=created.id, user_id=user_id)

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.filename == "reporte.pdf"


def test_get_document_edge_case_not_found(get_db_test, mock_log_provider, normal_user):
    repo = PDFDatabaseRepositoryInfrastructure(
        db=get_db_test, log_provider=mock_log_provider
    )
    user_id = normal_user.id

    fetched = repo.get_document(document_id=9999, user_id=user_id)
    assert fetched is None
    mock_log_provider.error_log.assert_not_called()


def test_get_all_documents_success(get_db_test, mock_log_provider, normal_user):
    repo = PDFDatabaseRepositoryInfrastructure(
        db=get_db_test, log_provider=mock_log_provider
    )
    user_id = normal_user.id

    repo.create_document(
        filename="doc_A.pdf",
        file_path="/uploads/a.pdf",
        user_id=user_id,
        status=DocumentStatus.PENDING,
    )
    repo.create_document(
        filename="doc_B.pdf",
        file_path="/uploads/b.pdf",
        user_id=user_id,
        status=DocumentStatus.PROCESSED,
    )

    documents = repo.get_all_documents(user_id=user_id)

    assert isinstance(documents, list)
    assert len(documents) == 2
    filenames = [d.filename for d in documents]
    assert "doc_A.pdf" in filenames
    assert "doc_B.pdf" in filenames


def test_get_all_documents_edge_case_empty(get_db_test, mock_log_provider, normal_user):
    repo = PDFDatabaseRepositoryInfrastructure(
        db=get_db_test, log_provider=mock_log_provider
    )
    user_id = normal_user.id

    documents = repo.get_all_documents(user_id=user_id)
    assert documents == []
    assert isinstance(documents, list)


# ==========================================
# 3. PRUEBAS DE ACTUALIZACIÓN (update_document_status)
# ==========================================


def test_update_document_status_success(get_db_test, mock_log_provider, normal_user):
    repo = PDFDatabaseRepositoryInfrastructure(
        db=get_db_test, log_provider=mock_log_provider
    )
    user_id = normal_user.id

    created = repo.create_document(
        filename="proceso.pdf",
        file_path="/uploads/proceso.pdf",
        user_id=user_id,
        status=DocumentStatus.PENDING,
    )

    updated = repo.update_document_status(
        document_id=created.id, user_id=user_id, status=DocumentStatus.PROCESSED
    )

    assert updated.status == "processed"
    assert updated.id == created.id


def test_update_document_status_edge_case_not_found(
    get_db_test, mock_log_provider, normal_user
):
    repo = PDFDatabaseRepositoryInfrastructure(
        db=get_db_test, log_provider=mock_log_provider
    )
    user_id = normal_user.id

    with pytest.raises(InfrastructureException) as exc_info:
        repo.update_document_status(
            document_id=8888, user_id=user_id, status=DocumentStatus.PROCESSED
        )

    assert "error updating documents data" in str(exc_info.value)
    mock_log_provider.error_log.assert_called_once()


# ==========================================
# 4. PRUEBAS DE ELIMINACIÓN (delete_document)
# ==========================================


def test_delete_document_success(get_db_test, mock_log_provider, normal_user):
    repo = PDFDatabaseRepositoryInfrastructure(
        db=get_db_test, log_provider=mock_log_provider
    )
    user_id = normal_user.id

    created = repo.create_document(
        filename="borrar.pdf",
        file_path="/uploads/borrar.pdf",
        user_id=user_id,
        status=DocumentStatus.PENDING,
    )

    # Verificamos que existe antes de borrar
    assert repo.get_document(created.id, user_id) is not None

    # Ejecutamos borrado
    response = repo.delete_document(document_id=created.id, user_id=user_id)
    assert response is None

    # Verificamos que ya no existe
    assert repo.get_document(created.id, user_id) is None


def test_delete_document_edge_case_non_existent(
    get_db_test, mock_log_provider, normal_user
):
    repo = PDFDatabaseRepositoryInfrastructure(
        db=get_db_test, log_provider=mock_log_provider
    )
    user_id = normal_user.id

    response = repo.delete_document(document_id=7777, user_id=user_id)
    assert response is None
    mock_log_provider.error_log.assert_not_called()
