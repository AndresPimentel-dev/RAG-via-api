from abc import ABC, abstractmethod

from src.domain.entities import DocumentEntity, UserEntity
from src.domain.enums import DocumentStatus


class PasswordService(ABC):
    @abstractmethod
    def hash_password(self, plain_password: str) -> str:
        pass

    @abstractmethod
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        pass


class TokenService(ABC):
    @abstractmethod
    def create_token(self, data: dict) -> str:
        pass

    @abstractmethod
    def decode_token(self, token: str) -> dict | None:
        pass


class PDFDatabaseRepository(ABC):
    @abstractmethod
    def create_document(
        self, filename: str, file_path: str, user_id: int, status: DocumentStatus
    ) -> DocumentEntity:
        pass

    @abstractmethod
    def get_document(self, document_id: int, user_id: int) -> DocumentEntity | None:
        pass

    @abstractmethod
    def get_all_documents(self, user_id: int) -> list[DocumentEntity]:
        pass

    @abstractmethod
    def update_document_status(
        self, document_id: int, user_id: int, status: DocumentStatus
    ) -> DocumentEntity:
        pass

    @abstractmethod
    def delete_document(self, document_id: int, user_id: int) -> None:
        pass


class UserDatabaseRepository(ABC):
    @abstractmethod
    def create_user(
        self, username: str, email: str, hashed_password: str
    ) -> UserEntity:
        pass

    @abstractmethod
    def get_user_by_username(self, username: str) -> UserEntity | None:
        pass

    @abstractmethod
    def get_user_by_email(self, email: str) -> UserEntity | None:
        pass


class StorageService(ABC):
    @abstractmethod
    def save_file(self, file_bytes: bytes, file_path: str) -> bool:
        pass

    @abstractmethod
    def get_file(self, file_path: str) -> bytes:
        pass

    @abstractmethod
    def delete_file(self, file_path: str) -> None:
        pass


class PDFProcessorService(ABC):
    @abstractmethod
    def extract_text(self, file_bytes: bytes) -> str:
        pass

    @abstractmethod
    def split_into_chunks(self, text: str) -> list[str]:
        pass


class CeleryTaskService(ABC):
    @abstractmethod
    def trigger_converting_process_pdf_task(self, user_id: int, pdf: DocumentEntity):
        pass


class LogProvider(ABC):
    @abstractmethod
    def info_log(self, message: str, context: str | None = None):
        pass

    @abstractmethod
    def error_log(self, message: str, context: str | None = None):
        pass


class VectorDatabaseRepository(ABC):
    @abstractmethod
    def insert_embeddings(
        self,
        document_id: int,
        user_id: int,
        chunks: list[str],
        embeddings: list[list[float]],
    ):
        pass

    @abstractmethod
    def search_similar(
        self,
        user_id: int,
        query_embeddings: list[float],
        document_id: int | None = None,
        top_k: int = 5,
    ):
        pass

    @abstractmethod
    def delete_context(self, document_id: int, user_id: int):
        pass


class LLMService(ABC):
    @abstractmethod
    def generate_embeddings(self, plain_chunks: str | list[str]):
        pass

    @abstractmethod
    def get_answer(self, prompt: str):
        pass
