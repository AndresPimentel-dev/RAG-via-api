from pathlib import Path

from src.domain.exceptions import InfrastructureException, NotFoundException
from src.domain.interfaces import LogProvider, StorageService
from src.infrastructure.config import settings


class LocalStorageAdapter(StorageService):
    def __init__(self, log_provider: LogProvider, base_path: str = settings.BASE_PATH):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.log_provider = log_provider

    def save_file(self, file_bytes: bytes, file_path: str) -> None:
        full_path = self.base_path / file_path
        try:
            full_path.parent.mkdir(parents=True, exist_ok=True)

            with open(full_path, "wb") as buffer:
                buffer.write(file_bytes)

        except Exception as e:
            self.log_provider.error_log(
                message=f"Storage failure writing to path {file_path}",
                context=f"Technical error: {e!s}",
            )
            raise InfrastructureException("Could not save file to disk.") from e

    def get_file(self, file_path: str) -> bytes:
        full_path = self.base_path / file_path
        try:
            if not full_path.exists():
                return None

            return full_path.read_bytes()

        except Exception as e:
            self.log_provider.error_log(
                message=f"Technical storage failure reading path {file_path}",
                context=f"Technical error: {e!s}",
            )
            raise InfrastructureException(
                "Could not read file from storage volume."
            ) from e

    def delete_file(self, file_path: str) -> None:
        full_path = self.base_path / file_path
        try:
            if not full_path.exists():
                raise NotFoundException(f"File not found: {file_path}")

            full_path.unlink()

        except Exception as e:
            self.log_provider.error_log(
                message=f"Technical storage failure deleting path {file_path}",
                context=f"Technical error: {e!s}",
            )
            raise InfrastructureException(
                "Could not delete file from storage volume."
            ) from e
