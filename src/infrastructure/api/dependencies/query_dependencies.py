from fastapi import Depends
from sqlalchemy.orm import Session

from src.infrastructure.config import settings
from src.infrastructure.database.conection import get_db
from src.infrastructure.database.repositories import (
    VectorDatabaseRepositoryInfrastructure,
)
from src.infrastructure.logging.logging import LogProviderInfrastructure
from src.infrastructure.metrics.metrics import (
    InstrumentedRequestModelRepository,
    InstrumentedVectorDatabaseRepository,
)
from src.infrastructure.model.model import LLMServiceInfrastructure
from src.use_cases.query_use_case import QueryUseCase


def get_query_use_case(db: Session = Depends(get_db)) -> QueryUseCase:
    use_case = QueryUseCase(
        log_provider=LogProviderInfrastructure(),
        llm_service=InstrumentedRequestModelRepository(
            LLMServiceInfrastructure(
                api_key=settings.API_KEY, log_provider=LogProviderInfrastructure()
            )
        ),
        vector_repository=InstrumentedVectorDatabaseRepository(
            VectorDatabaseRepositoryInfrastructure(
                db=db, lp=LogProviderInfrastructure()
            )
        ),
    )
    return use_case
