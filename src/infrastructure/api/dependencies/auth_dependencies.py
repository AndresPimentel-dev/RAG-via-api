from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.domain.entities import UserEntity
from src.domain.exceptions import UnauthorizedException
from src.domain.interfaces import UserDatabaseRepository
from src.infrastructure.config import settings
from src.infrastructure.database.conection import get_db
from src.infrastructure.database.repositories import (
    UserDatabaseRepositoryInfrastructure,
)
from src.infrastructure.logging.logging import LogProviderInfrastructure
from src.infrastructure.metrics.metrics import InstrumentedUserDatabaseRepository
from src.infrastructure.security.securityandtokens import (
    PasswordServiceRepositoryInfrastructure,
    TokenServiceRepositoryInfrastructure,
)
from src.use_cases.authentication_cases import UserUseCases

oauth_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")


def get_user_reppository(db: Session = Depends(get_db)) -> UserDatabaseRepository:
    repo = InstrumentedUserDatabaseRepository(
        UserDatabaseRepositoryInfrastructure(
            db=db, log_provider=LogProviderInfrastructure()
        )
    )
    return repo


def get_current_user(
    token: str = Depends(oauth_scheme),
    user_repo: UserDatabaseRepositoryInfrastructure = Depends(get_user_reppository),
    token_service=TokenServiceRepositoryInfrastructure(
        log_provider=LogProviderInfrastructure(),
        SECRET_KEY=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
        expire_token_time=settings.EXPIRE_TOKEN_TIME,
    ),
) -> UserEntity:
    data = token_service.decode_token(token=token)

    if data is None:
        raise UnauthorizedException(message="unauthenticated")

    user = user_repo.get_user_by_username(username=data["sub"])

    if user is None:
        raise UnauthorizedException(message="unauthenticated")

    return user


def get_user_use_cases(db: Session = Depends(get_db)) -> UserUseCases:
    use_case = UserUseCases(
        password_service=PasswordServiceRepositoryInfrastructure(),
        user_database_repository=InstrumentedUserDatabaseRepository(
            UserDatabaseRepositoryInfrastructure(
                db=db, log_provider=LogProviderInfrastructure()
            )
        ),
        token_service=TokenServiceRepositoryInfrastructure(
            log_provider=LogProviderInfrastructure(),
            SECRET_KEY=settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
            expire_token_time=settings.EXPIRE_TOKEN_TIME,
        ),
        log_provider=LogProviderInfrastructure(),
    )

    return use_case
