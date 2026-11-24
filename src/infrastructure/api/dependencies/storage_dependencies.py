from fastapi import Depends
from sqlalchemy.orm import Session

from src.infrastructure.celery.celery_task_trigger import (
    CeleryTaskServiceInfrastructure,
)
from src.infrastructure.database.conection import get_db
from src.infrastructure.database.repositories import (
    PDFDatabaseRepositoryInfrastructure,
    VectorDatabaseRepositoryInfrastructure,
)
from src.infrastructure.logging.logging import LogProviderInfrastructure
from src.infrastructure.metrics.metrics import (
    InstrumentedVectorDatabaseRepository,
    IntrumentedPDFRepository,
)
from src.infrastructure.storage.local_storage import LocalStorageAdapter
from src.use_cases.storage_use_case import StorageUseCase


def get_storage_use_case(db: Session = Depends(get_db)) -> StorageUseCase:
    use_case = StorageUseCase(
        log_provider=LogProviderInfrastructure(),
        storage_service=LocalStorageAdapter(LogProviderInfrastructure()),
        pdf_database_repository=IntrumentedPDFRepository(
            PDFDatabaseRepositoryInfrastructure(db, LogProviderInfrastructure())
        ),
        vector_database_repository=InstrumentedVectorDatabaseRepository(
            VectorDatabaseRepositoryInfrastructure(db, LogProviderInfrastructure())
        ),
        celery_service=CeleryTaskServiceInfrastructure(),
    )

    return use_case
