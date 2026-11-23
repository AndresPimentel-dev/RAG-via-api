from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from src.domain.exceptions import InfrastructureException
from src.domain.interfaces import LogProvider, PasswordService, TokenService


class PasswordServiceRepositoryInfrastructure(PasswordService):
    def __init__(self):
        self.password_hash_context = PasswordHash.recommended()

    def hash_password(self, plain_password: str):
        return self.password_hash_context.hash(plain_password)

    def verify_password(self, plain_password, hashed_password):
        return self.password_hash_context.verify(plain_password, hashed_password)


class TokenServiceRepositoryInfrastructure(TokenService):
    def __init__(
        self, log_provider: LogProvider, SECRET_KEY, algorithm, expire_token_time
    ):
        self.secret_key = SECRET_KEY
        self.algorithm = algorithm
        self.expire_time = expire_token_time
        self.log_provider = log_provider

    def create_token(self, data: dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()
        expire = datetime.now(UTC) + (
            expires_delta or timedelta(minutes=self.expire_time)
        )
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, self.algorithm)

    def decode_token(self, token: str):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username = payload.get("sub")
            if username is None:
                return None
            return {"sub": username}
        except Exception as e:
            self.log_provider.error_log(message="error decoding token", context=str(e))
            raise InfrastructureException("error decoding token") from e
