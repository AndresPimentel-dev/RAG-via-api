from celery import Celery
from prometheus_client import Counter, Histogram

from src.domain.enums import DocumentStatus
from src.domain.exceptions import InfrastructureException
from src.infrastructure.config import settings
from src.infrastructure.database.conection import SessionLocal
from src.infrastructure.database.repositories import (
    PDFDatabaseRepositoryInfrastructure,
    VectorDatabaseRepositoryInfrastructure,
)
from src.infrastructure.logging.logging import LogProviderInfrastructure
from src.infrastructure.metrics.metrics import (
    InstrumentedRequestModelRepository,
    InstrumentedVectorDatabaseRepository,
    IntrumentedPDFRepository,
)
from src.infrastructure.model.model import LLMServiceInfrastructure
from src.infrastructure.pdfprocessor.pdf_processor_service import (
    PDFProcessorServiceInfrastruture,
)
from src.infrastructure.storage.local_storage import LocalStorageAdapter
from src.use_cases.vector_use_case import ProcessDocumentUseCase

celery_app = Celery(
    "RAG_worker", broker=f"{settings.REDIS_URL}/0", backend=f"{settings.REDIS_URL}/1"
)

CELERY_TASK_LATENCY = Histogram(
    "celery_task_latency_seconds",
    "Time taken to execute Celery tasks",
    ["task_name"],
)
CELERY_TASK_OPERATIONS = Counter(
    "celery_task_total", "Total Celery task executions", ["task_name", "status"]
)
CELERY_TASK_ERRORS = Counter(
    "celery_task_errors_total",
    "Total errors in Celery tasks",
    ["task_name", "error_type"],
)


@celery_app.task(name="PDF processor")
def process_pdf(document_id: int, user_id: int):
    with CELERY_TASK_LATENCY.labels(task_name="PDF processor").time():
        CELERY_TASK_OPERATIONS.labels(task_name="PDF processor", status="started").inc()

        db = SessionLocal()
        logger = LogProviderInfrastructure()

        try:
            use_case = ProcessDocumentUseCase(
                vector_db_repository=InstrumentedVectorDatabaseRepository(
                    original=VectorDatabaseRepositoryInfrastructure(db, logger)
                ),
                log_provider=logger,
                llm_service=InstrumentedRequestModelRepository(
                    original=LLMServiceInfrastructure(
                        api_key=settings.API_KEY, log_provider=logger
                    )
                ),
                pdf_processor_service=PDFProcessorServiceInfrastruture(
                    log_provider=logger
                ),
                pdf_database_repository=IntrumentedPDFRepository(
                    original=PDFDatabaseRepositoryInfrastructure(
                        db=db, log_provider=logger
                    )
                ),
                storage_service=LocalStorageAdapter(log_provider=logger),
            )

            logger.info_log(
                message="Converting new document into embeddings",
                context=f"document_id: {document_id}",
            )
            use_case.execute(document_id=document_id, user_id=user_id)

            CELERY_TASK_OPERATIONS.labels(
                task_name="PDF processor", status="success"
            ).inc()

        except Exception as e:
            CELERY_TASK_ERRORS.labels(
                task_name="PDF processor", error_type=type(e).__name__
            ).inc()
            CELERY_TASK_OPERATIONS.labels(
                task_name="PDF processor", status="failure"
            ).inc()
            logger.error_log(
                message="Error trying to convert into embeddings", context=str(e)
            )
            PDFDatabaseRepositoryInfrastructure(
                db=db, log_provider=logger
            ).update_document_status(
                document_id=document_id, user_id=user_id, status=DocumentStatus.FAILED
            )
            db.commit()
            raise InfrastructureException(
                "Error trying to convert into embeddings"
            ) from e
        finally:
            db.close()
