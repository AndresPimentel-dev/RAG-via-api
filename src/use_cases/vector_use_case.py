from src.domain.enums import DocumentStatus
from src.domain.exceptions import NotFoundException
from src.domain.interfaces import (
    LLMService,
    LogProvider,
    PDFDatabaseRepository,
    PDFProcessorService,
    StorageService,
    VectorDatabaseRepository,
)


class ProcessDocumentUseCase:
    def __init__(
        self,
        vector_db_repository: VectorDatabaseRepository,
        log_provider: LogProvider,
        llm_service: LLMService,
        pdf_processor_service: PDFProcessorService,
        pdf_database_repository: PDFDatabaseRepository,
        storage_service: StorageService,
    ):
        self.log_provider = log_provider
        self.vector_db_repository = vector_db_repository
        self.llm_service = llm_service
        self.pdf_processor_service = pdf_processor_service
        self.pdf_database_repository = pdf_database_repository
        self.storage_service = storage_service

    def execute(self, document_id: int, user_id: int) -> None:
        """The master method called by the Celery worker."""
        self.log_provider.info_log(
            message=f"Starting processing for file_id: {document_id}"
        )
        document = self.pdf_database_repository.get_document(
            document_id=document_id, user_id=user_id
        )
        if document is None:
            raise NotFoundException(message="Document not Found")
        file = self.storage_service.get_file(file_path=document.file_path)
        if file is None:
            raise NotFoundException(message="File not Found")
        text = self.pdf_processor_service.extract_text(file)
        chunks = self.pdf_processor_service.split_into_chunks(text=text)
        embeddings = self.llm_service.generate_embeddings(chunks)
        self.vector_db_repository.insert_embeddings(
            document_id, user_id, chunks, embeddings
        )
        self.pdf_database_repository.update_document_status(
            document_id=document_id, user_id=user_id, status=DocumentStatus.PROCESSED
        )
        self.log_provider.info_log(
            message=f"Successfully processed file_id: {document_id}"
        )
