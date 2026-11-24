import uuid

from src.domain.entities import DocumentEntity
from src.domain.enums import DocumentStatus
from src.domain.exceptions import NotFoundException
from src.domain.interfaces import (
    CeleryTaskService,
    LogProvider,
    PDFDatabaseRepository,
    StorageService,
    VectorDatabaseRepository,
)


class StorageUseCase:
    def __init__(
        self,
        log_provider: LogProvider,
        storage_service: StorageService,
        pdf_database_repository: PDFDatabaseRepository,
        vector_database_repository: VectorDatabaseRepository,
        celery_service: CeleryTaskService,
    ):
        self.storage_service = storage_service
        self.pdf_database_repository = pdf_database_repository
        self.vector_database_repository = vector_database_repository
        self.log_provider = log_provider
        self.celery_service = celery_service

    def store_file(
        self, file_bytes: bytes, filename: str, user_id: int
    ) -> DocumentEntity:
        unique_id = uuid.uuid4()
        safe_file_name = f"{unique_id}_{filename}"
        file_path = f"users/{user_id}/{safe_file_name}"

        self.storage_service.save_file(file_bytes=file_bytes, file_path=file_path)

        document_entity = self.pdf_database_repository.create_document(
            filename=filename,
            file_path=file_path,
            user_id=user_id,
            status=DocumentStatus.PENDING,
        )

        self.log_provider.info_log(
            message="file stored correctly", context=f"data: {user_id}, {file_path}"
        )
        self.celery_service.trigger_converting_process_pdf_task(
            user_id=user_id, pdf=document_entity
        )

        return document_entity

    def get_document_bytes(self, file_id: int, user_id: int) -> bytes:
        documententity = self.pdf_database_repository.get_document(
            document_id=file_id, user_id=user_id
        )
        if documententity is None:
            raise NotFoundException("Document not found in database")

        file = self.storage_service.get_file(file_path=documententity.file_path)
        if file is None:
            raise NotFoundException("File not found in storage")

        return file

    def get_documents_data_by_user_id(self, user_id: int) -> list[DocumentEntity]:
        documents = self.pdf_database_repository.get_all_documents(user_id=user_id)

        return documents

    def delete_file(self, user_id: int, document_id: int) -> None:
        document = self.pdf_database_repository.get_document(
            document_id=document_id, user_id=user_id
        )
        if document is None:
            raise NotFoundException(message="document not found")

        self.storage_service.delete_file(file_path=document.file_path)
        self.pdf_database_repository.delete_document(
            document_id=document.id, user_id=user_id
        )
        self.vector_database_repository.delete_context(
            document_id=document_id, user_id=user_id
        )
        self.log_provider.info_log(message="file deleted correctly")
