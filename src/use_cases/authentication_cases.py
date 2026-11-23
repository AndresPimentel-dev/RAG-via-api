from src.domain.exceptions import ConflictException, UnauthorizedException
from src.domain.interfaces import (
    LogProvider,
    PasswordService,
    TokenService,
    UserDatabaseRepository,
)


class UserUseCases:
    def __init__(
        self,
        password_service: PasswordService,
        user_database_repository: UserDatabaseRepository,
        token_service: TokenService,
        log_provider: LogProvider,
    ):
        self.password_service = password_service
        self.user_database_repository = user_database_repository
        self.token_service = token_service
        self.log_provider = log_provider

    def create_user(self, username: str, email: str, plain_password: str) -> str:
        if self.user_database_repository.get_user_by_email(
            email=email
        ) or self.user_database_repository.get_user_by_username(username=username):
            raise ConflictException("email or username already exists")
        hashed_password = self.password_service.hash_password(
            plain_password=plain_password
        )
        self.user_database_repository.create_user(
            username=username, email=email, hashed_password=hashed_password
        )
        data = {"sub": username}
        token = self.token_service.create_token(data)
        self.log_provider.info_log(
            message=f"new user created{{username: {username}, email: {email}}}"
        )

        return token

    def login(self, username, plain_password) -> str:
        user = self.user_database_repository.get_user_by_username(username=username)
        if not user or not self.password_service.verify_password(
            plain_password=plain_password, hashed_password=user.hashed_password
        ):
            raise UnauthorizedException("not existing user or incorrect password")
        data = {"sub": username}
        token = self.token_service.create_token(data)
        self.log_provider.info_log(message=f"user logged in{{username: {username}}}")

        return token
