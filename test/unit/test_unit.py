from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from src.domain.entities import DocumentEntity, UserEntity
from src.domain.enums import DocumentStatus
from src.domain.exceptions import (
    ConflictException,
    NotFoundException,
    UnauthorizedException,
)
from src.use_cases.authentication_cases import UserUseCases
from src.use_cases.query_use_case import QueryUseCase
from src.use_cases.storage_use_case import StorageUseCase
from src.use_cases.vector_use_case import ProcessDocumentUseCase

########################################################
# Query Use Cases Tests
########################################################


def test_get_answer_success_without_document_id():
    mock_log_provider = MagicMock()
    mock_llm_service = MagicMock()
    mock_vector_repo = MagicMock()

    mock_llm_service.generate_embeddings.return_value = [[0.1, 0.2, 0.3]]
    mock_vector_repo.search_similar.return_value = "Relevant text from documents"
    mock_llm_service.get_answer.return_value = "This is the AI answer."

    use_case = QueryUseCase(
        log_provider=mock_log_provider,
        llm_service=mock_llm_service,
        vector_repository=mock_vector_repo,
    )

    result = use_case.get_answer(plain_query="What is AI?", user_id=1)

    assert result == "This is the AI answer."

    mock_llm_service.generate_embeddings.assert_called_once_with("What is AI?")

    mock_vector_repo.search_similar.assert_called_once_with(1, [0.1, 0.2, 0.3])

    mock_llm_service.get_answer.assert_called_once()

    mock_log_provider.info_log.assert_called_once()


def test_get_answer_success_with_document_id():
    mock_log_provider = MagicMock()
    mock_llm_service = MagicMock()
    mock_vector_repo = MagicMock()

    mock_llm_service.generate_embeddings.return_value = [[0.4, 0.5]]
    mock_vector_repo.search_similar.return_value = "Specific document context"
    mock_llm_service.get_answer.return_value = "Answer from specific doc."

    use_case = QueryUseCase(
        log_provider=mock_log_provider,
        llm_service=mock_llm_service,
        vector_repository=mock_vector_repo,
    )

    result = use_case.get_answer(
        plain_query="Summarize this", user_id=2, document_id=10
    )

    assert result == "Answer from specific doc."

    mock_vector_repo.search_similar.assert_called_once_with(2, [0.4, 0.5], 10)


def test_get_answer_raises_not_found_exception():
    mock_log_provider = MagicMock()
    mock_llm_service = MagicMock()
    mock_vector_repo = MagicMock()

    mock_llm_service.generate_embeddings.return_value = [[0.1]]
    mock_vector_repo.search_similar.return_value = None

    use_case = QueryUseCase(
        log_provider=mock_log_provider,
        llm_service=mock_llm_service,
        vector_repository=mock_vector_repo,
    )

    with pytest.raises(NotFoundException) as exc_info:
        use_case.get_answer(plain_query="Missing info", user_id=1, document_id=99)

    assert str(exc_info.value.message) == "Context not found"

    mock_llm_service.get_answer.assert_not_called()


########################################################
# Storage Use Cases Tests
########################################################


def test_store_file():
    log_provider = MagicMock()
    storage_service = MagicMock()
    pdf_database_repository = MagicMock()
    vector_database_repository=MagicMock()
    celery_service = MagicMock()

    entity = DocumentEntity(
        id=1,
        filename="fakename",
        file_path="fake/path",
        user_id=1,
        status=DocumentStatus.PENDING,
        created_at=datetime.now(UTC),
    )

    fake_pdf_bytes = b"%PDF-1.4 fake pdf content for testing..."

    pdf_database_repository.create_document.return_value = entity

    use_case = StorageUseCase(
        log_provider=log_provider,
        storage_service=storage_service,
        pdf_database_repository=pdf_database_repository,
        vector_database_repository=vector_database_repository,
        celery_service=celery_service,
    )

    response = use_case.store_file(
        file_bytes=fake_pdf_bytes, filename="fakename", user_id=1
    )

    assert response.filename == "fakename"
    assert response.file_path == "fake/path"
    assert response.user_id == 1

    storage_service.save_file.assert_called_once()
    pdf_database_repository.create_document.assert_called_once()
    celery_service.trigger_converting_process_pdf_task.assert_called_once_with(
        user_id=1, pdf=entity
    )


def test_get_document_bytes():
    log_provider = MagicMock()
    storage_service = MagicMock()
    pdf_database_repository = MagicMock()
    vector_database_repository=MagicMock()
    celery_service = MagicMock()

    entity = DocumentEntity(
        id=1,
        filename="fakename",
        file_path="fake/path",
        user_id=1,
        status=DocumentStatus.PENDING,
        created_at=datetime.now(UTC),
    )

    pdf_database_repository.get_document.return_value = entity
    storage_service.get_file.return_value = b"%PDF-1.4 fake pdf content for testing..."

    use_case = StorageUseCase(
        log_provider=log_provider,
        storage_service=storage_service,
        pdf_database_repository=pdf_database_repository,
        vector_database_repository=vector_database_repository,
        celery_service=celery_service,
    )

    response = use_case.get_document_bytes(file_id=1, user_id=1)

    assert isinstance(response, bytes)
    assert response == b"%PDF-1.4 fake pdf content for testing..."
    pdf_database_repository.get_document.assert_called_once_with(
        document_id=1, user_id=1
    )
    storage_service.get_file.assert_called_once_with(file_path=entity.file_path)


def test_get_document_bytes_not_found_entity():
    log_provider = MagicMock()
    storage_service = MagicMock()
    pdf_database_repository = MagicMock()
    vector_database_repository=MagicMock()
    celery_service = MagicMock()

    use_case = StorageUseCase(
        log_provider=log_provider,
        storage_service=storage_service,
        pdf_database_repository=pdf_database_repository,
        vector_database_repository=vector_database_repository,
        celery_service=celery_service,
    )

    pdf_database_repository.get_document.return_value = None

    with pytest.raises(NotFoundException) as exc_info:
        use_case.get_document_bytes(file_id=1, user_id=1)

    assert str(exc_info.value.message) == "Document not found in database"
    storage_service.get_file.assert_not_called()


def test_get_document_bytes_not_found_file():
    log_provider = MagicMock()
    storage_service = MagicMock()
    pdf_database_repository = MagicMock()
    vector_database_repository=MagicMock()
    celery_service = MagicMock()

    entity = DocumentEntity(
        id=1,
        filename="fakename",
        file_path="fake/path",
        user_id=1,
        status=DocumentStatus.PENDING,
        created_at=datetime.now(UTC),
    )

    pdf_database_repository.get_document.return_value = entity
    storage_service.get_file.return_value = None

    use_case = StorageUseCase(
        log_provider=log_provider,
        storage_service=storage_service,
        pdf_database_repository=pdf_database_repository,
        vector_database_repository=vector_database_repository,
        celery_service=celery_service,
    )

    with pytest.raises(NotFoundException) as exc_info:
        use_case.get_document_bytes(file_id=1, user_id=1)
    assert str(exc_info.value.message) == "File not found in storage"
    pdf_database_repository.get_document.assert_called_once_with(
        document_id=1, user_id=1
    )


def test_getget_documents_data_by_user_id():
    log_provider = MagicMock()
    storage_service = MagicMock()
    pdf_database_repository = MagicMock()
    vector_database_repository = MagicMock()
    celery_service = MagicMock()

    entity = DocumentEntity(
        id=1,
        filename="fakename",
        file_path="fake/path",
        user_id=1,
        status=DocumentStatus.PENDING,
        created_at=datetime.now(UTC),
    )

    pdf_database_repository.get_all_documents.return_value = [entity, entity]

    use_case = StorageUseCase(
        log_provider=log_provider,
        storage_service=storage_service,
        pdf_database_repository=pdf_database_repository,
        vector_database_repository=vector_database_repository,
        celery_service=celery_service,
    )

    response = use_case.get_documents_data_by_user_id(user_id=1)

    assert isinstance(response, list)
    assert response[1].id == 1
    assert response[1].file_path == "fake/path"
    assert len(response) == 2


def test_delete_file():
    log_provider = MagicMock()
    storage_service = MagicMock()
    pdf_database_repository = MagicMock()
    vector_database_repository = MagicMock()
    celery_service = MagicMock()

    entity = DocumentEntity(
        id=1,
        filename="fakename",
        file_path="fake/path",
        user_id=1,
        status=DocumentStatus.PENDING,
        created_at=datetime.now(UTC),
    )

    use_case = StorageUseCase(
        log_provider=log_provider,
        storage_service=storage_service,
        pdf_database_repository=pdf_database_repository,
        vector_database_repository=vector_database_repository,
        celery_service=celery_service,
    )

    pdf_database_repository.get_document.return_value = entity

    response = use_case.delete_file(user_id=1, document_id=1)

    assert response == None
    pdf_database_repository.get_document.assert_called_once_with(
        document_id=1, user_id=1
    )
    storage_service.delete_file.assert_called_once_with(file_path="fake/path")
    pdf_database_repository.delete_document.assert_called_once_with(
        document_id=1, user_id=1
    )


def test_delte_file_document_not_found():
    log_provider = MagicMock()
    storage_service = MagicMock()
    pdf_database_repository = MagicMock()
    vector_database_repository = MagicMock()
    celery_service = MagicMock()
    use_case = StorageUseCase(
        log_provider=log_provider,
        storage_service=storage_service,
        pdf_database_repository=pdf_database_repository,
        vector_database_repository=vector_database_repository,
        celery_service=celery_service,
    )

    pdf_database_repository.get_document.return_value = None

    with pytest.raises(NotFoundException) as exc_info:
        use_case.delete_file(user_id=1, document_id=1)

    assert str(exc_info.value.message) == "document not found"
    storage_service.delete_file.assert_not_called()
    pdf_database_repository.delete_document.assert_not_called()


########################################################
# Authentication Use Cases Tests
########################################################


def test_create_user():
    password_service = MagicMock()
    user_database_repository = MagicMock()
    token_service = MagicMock()
    log_provider = MagicMock()

    use_case = UserUseCases(
        password_service=password_service,
        user_database_repository=user_database_repository,
        token_service=token_service,
        log_provider=log_provider,
    )

    entity = UserEntity(
        id=1,
        username="fakeexpreso",
        email="fakeemail",
        hashed_password="adsfSDFG56454sdgASd",
        created_at=datetime.now(UTC),
    )

    user_database_repository.get_user_by_email.return_value = None
    user_database_repository.get_user_by_username.return_value = None
    password_service.hash_password.return_value = "adsfSDFG56454sdgASd"
    user_database_repository.create_user.return_value = entity
    token_service.create_token.return_value = "askugdjasfd4584asdhg4464adsg"

    response = use_case.create_user(
        username="fakeexpreso", email="fakeemail", plain_password="plainfake"
    )

    assert response == "askugdjasfd4584asdhg4464adsg"
    user_database_repository.get_user_by_email.assert_called_once_with(
        email="fakeemail"
    )
    user_database_repository.get_user_by_username.assert_called_once_with(
        username="fakeexpreso"
    )
    token_service.create_token.assert_called_once_with({"sub": "fakeexpreso"})


def test_create_user_with_existing_email():
    password_service = MagicMock()
    user_database_repository = MagicMock()
    token_service = MagicMock()
    log_provider = MagicMock()

    use_case = UserUseCases(
        password_service=password_service,
        user_database_repository=user_database_repository,
        token_service=token_service,
        log_provider=log_provider,
    )

    entity = UserEntity(
        id=1,
        username="fakeexpreso",
        email="fakeemail",
        hashed_password="adsfSDFG56454sdgASd",
        created_at=datetime.now(UTC),
    )

    user_database_repository.get_user_by_email.return_value = entity

    with pytest.raises(ConflictException) as exc_info:
        use_case.create_user(
            username="fakeexpreso", email="fakeemail", plain_password="plainfake"
        )
    assert exc_info.value.message == "email or username already exists"
    user_database_repository.get_user_by_email.assert_called_once_with(
        email="fakeemail"
    )
    user_database_repository.get_user_by_username.assert_not_called()
    token_service.create_token.assert_not_called()


def test_create_user_with_existing_username():
    password_service = MagicMock()
    user_database_repository = MagicMock()
    token_service = MagicMock()
    log_provider = MagicMock()

    use_case = UserUseCases(
        password_service=password_service,
        user_database_repository=user_database_repository,
        token_service=token_service,
        log_provider=log_provider,
    )

    entity = UserEntity(
        id=1,
        username="fakeexpreso",
        email="fakeemail",
        hashed_password="adsfSDFG56454sdgASd",
        created_at=datetime.now(UTC),
    )

    user_database_repository.get_user_by_email.return_value = None
    user_database_repository.get_user_by_username.return_value = entity

    with pytest.raises(ConflictException) as exc_info:
        use_case.create_user(
            username="fakeexpreso", email="fakeemail", plain_password="plainfake"
        )
    assert exc_info.value.message == "email or username already exists"
    user_database_repository.get_user_by_email.assert_called_once_with(
        email="fakeemail"
    )
    user_database_repository.get_user_by_username.assert_called_once_with(
        username="fakeexpreso"
    )
    token_service.create_token.assert_not_called()


def test_login():
    password_service = MagicMock()
    user_database_repository = MagicMock()
    token_service = MagicMock()
    log_provider = MagicMock()

    use_case = UserUseCases(
        password_service=password_service,
        user_database_repository=user_database_repository,
        token_service=token_service,
        log_provider=log_provider,
    )

    entity = UserEntity(
        id=1,
        username="fakeexpreso",
        email="fakeemail",
        hashed_password="adsfSDFG56454sdgASd",
        created_at=datetime.now(UTC),
    )

    user_database_repository.get_user_by_username.return_value = entity
    password_service.verify_password.return_value = True
    token_service.create_token.return_value = "askugdjasfd4584asdhg4464adsg"

    response = use_case.login(username="fakeexpreso", plain_password="plainfake")

    assert response == "askugdjasfd4584asdhg4464adsg"
    user_database_repository.get_user_by_username.assert_called_once_with(
        username="fakeexpreso"
    )
    password_service.verify_password.assert_called_once_with(
        plain_password="plainfake", hashed_password="adsfSDFG56454sdgASd"
    )
    token_service.create_token.assert_called_once_with({"sub": "fakeexpreso"})


def test_login_nonexisting_username():
    password_service = MagicMock()
    user_database_repository = MagicMock()
    token_service = MagicMock()
    log_provider = MagicMock()

    use_case = UserUseCases(
        password_service=password_service,
        user_database_repository=user_database_repository,
        token_service=token_service,
        log_provider=log_provider,
    )

    user_database_repository.get_user_by_username.return_value = None

    with pytest.raises(UnauthorizedException) as exc_info:
        use_case.login(username="fakeexpreso", plain_password="plainfake")

    assert str(exc_info.value.message) == "not existing user or incorrect password"
    token_service.create_token.assert_not_called()


def test_login_incorrect_password():
    password_service = MagicMock()
    user_database_repository = MagicMock()
    token_service = MagicMock()
    log_provider = MagicMock()

    use_case = UserUseCases(
        password_service=password_service,
        user_database_repository=user_database_repository,
        token_service=token_service,
        log_provider=log_provider,
    )

    entity = UserEntity(
        id=1,
        username="fakeexpreso",
        email="fakeemail",
        hashed_password="adsfSDFG56454sdgASd",
        created_at=datetime.now(UTC),
    )

    user_database_repository.get_user_by_username.return_value = entity
    password_service.verify_password.return_value = False

    with pytest.raises(UnauthorizedException) as exc_info:
        use_case.login(username="fakeexpreso", plain_password="plainfake")

    assert str(exc_info.value.message) == "not existing user or incorrect password"
    user_database_repository.get_user_by_username.assert_called_once_with(
        username="fakeexpreso"
    )
    password_service.verify_password.assert_called_once_with(
        plain_password="plainfake", hashed_password="adsfSDFG56454sdgASd"
    )
    token_service.create_token.assert_not_called()


########################################################
# Vector Use Cases Tests
########################################################


def test_execute_vecto_case():
    vector_db_repository = MagicMock()
    log_provider = MagicMock()
    llm_service = MagicMock()
    pdf_processor_service = MagicMock()
    pdf_database_repository = MagicMock()
    storage_service = MagicMock()

    use_case = ProcessDocumentUseCase(
        vector_db_repository=vector_db_repository,
        log_provider=log_provider,
        llm_service=llm_service,
        pdf_processor_service=pdf_processor_service,
        pdf_database_repository=pdf_database_repository,
        storage_service=storage_service,
    )

    entity = DocumentEntity(
        id=1,
        filename="fakename",
        file_path="fake/path",
        user_id=1,
        status=DocumentStatus.PENDING,
        created_at=datetime.now(UTC),
    )

    pdf_database_repository.get_document.return_value = entity
    storage_service.get_file.return_value = b"asayfa74f879414"
    pdf_processor_service.extract_text.return_value = "faketextasdasd"
    pdf_processor_service.split_into_chunks.return_value = ["asd", "pjs", "asf", "klj"]
    llm_service.generate_embeddings.return_value = [[0.2, 0.5, 0.5], [0.2, 0.5, 0.5]]

    response = use_case.execute(document_id=1, user_id=1)

    assert response is None
    pdf_database_repository.get_document.assert_called_once_with(
        document_id=1, user_id=1
    )
    storage_service.get_file.assert_called_once_with(file_path="fake/path")
    pdf_processor_service.extract_text.assert_called_once_with(b"asayfa74f879414")
    pdf_processor_service.split_into_chunks.assert_called_once_with(
        text="faketextasdasd"
    )


def test_execute_vecto_case_nonexisting_document():
    vector_db_repository = MagicMock()
    log_provider = MagicMock()
    llm_service = MagicMock()
    pdf_processor_service = MagicMock()
    pdf_database_repository = MagicMock()
    storage_service = MagicMock()

    use_case = ProcessDocumentUseCase(
        vector_db_repository=vector_db_repository,
        log_provider=log_provider,
        llm_service=llm_service,
        pdf_processor_service=pdf_processor_service,
        pdf_database_repository=pdf_database_repository,
        storage_service=storage_service,
    )

    pdf_database_repository.get_document.return_value = None

    with pytest.raises(NotFoundException) as exc_inf:
        use_case.execute(document_id=1, user_id=1)

    assert str(exc_inf.value.message) == "Document not Found"


def test_execute_vecto_case_nonexisting_file():
    vector_db_repository = MagicMock()
    log_provider = MagicMock()
    llm_service = MagicMock()
    pdf_processor_service = MagicMock()
    pdf_database_repository = MagicMock()
    storage_service = MagicMock()

    use_case = ProcessDocumentUseCase(
        vector_db_repository=vector_db_repository,
        log_provider=log_provider,
        llm_service=llm_service,
        pdf_processor_service=pdf_processor_service,
        pdf_database_repository=pdf_database_repository,
        storage_service=storage_service,
    )

    entity = DocumentEntity(
        id=1,
        filename="fakename",
        file_path="fake/path",
        user_id=1,
        status=DocumentStatus.PENDING,
        created_at=datetime.now(UTC),
    )

    pdf_database_repository.get_document.return_value = entity
    storage_service.get_file.return_value = None
    with pytest.raises(NotFoundException) as exc_info:
        use_case.execute(document_id=1, user_id=1)

    assert str(exc_info.value.message) == "File not Found"
