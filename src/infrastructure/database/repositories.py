from sqlalchemy import Select
from sqlalchemy.orm import Session

from src.domain.entities import DocumentEntity, UserEntity
from src.domain.enums import DocumentStatus
from src.domain.exceptions import InfrastructureException
from src.domain.interfaces import (
    LogProvider,
    PDFDatabaseRepository,
    UserDatabaseRepository,
    VectorDatabaseRepository,
)
from src.infrastructure.database.models import (
    DocumentsTable,
    UsersTable,
    VectorsTable,
)


class UserDatabaseRepositoryInfrastructure(UserDatabaseRepository):
    def __init__(self, db: Session, log_provider: LogProvider):
        self.db = db
        self.log_provider = log_provider

    def create_user(
        self, username: str, email: str, hashed_password: str
    ) -> UserEntity:
        try:
            new_user = UsersTable(
                username=username,
                email=email,
                hashed_password=hashed_password,
            )
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)

            return UserEntity.model_validate(new_user)

        except Exception as e:
            self.db.rollback()
            self.log_provider.error_log(
                message="error inserting new user into db", context=str(e)
            )
            raise InfrastructureException("error inserting new user into db") from e

    def get_user_by_username(self, username: str) -> UserEntity | None:
        try:
            statement = Select(UsersTable).where(UsersTable.username == username)
            user = self.db.scalars(statement).first()

            if not user:
                return None

            return UserEntity.model_validate(user)
        except Exception as e:
            self.log_provider.error_log(message="error querying db", context=str(e))
            raise InfrastructureException("error fetching user data") from e

    def get_user_by_email(self, email: str) -> UserEntity | None:
        try:
            statement = Select(UsersTable).where(UsersTable.email == email)
            user = self.db.scalars(statement).first()

            if not user:
                return None

            return UserEntity.model_validate(user)
        except Exception as e:
            self.log_provider.error_log(message="error querying db", context=str(e))
            raise InfrastructureException("error fetching user data") from e


class VectorDatabaseRepositoryInfrastructure(VectorDatabaseRepository):
    def __init__(self, db: Session, lp: LogProvider):
        self.db = db
        self.log_provider = lp

    def insert_embeddings(
        self,
        document_id: int,
        user_id: int,
        chunks: list[str],
        embeddings: list[list[float]],
    ):
        try:
            to_add = []
            for chunk, embedding in zip(chunks, embeddings):
                new_vector = VectorsTable(
                    chunk_text=chunk,
                    embedding=embedding,
                    owner_id=user_id,
                    document_id=document_id,
                )
                to_add.append(new_vector)
            self.db.add_all(to_add)
            self.db.commit()
            return
        except Exception as e:
            self.db.rollback()
            self.log_provider.error_log(
                message="error inserting embeddings",
                context=f"user_id:{user_id}, error: {e!s}",
            )
            raise InfrastructureException("error inserting new vectors") from e

    def search_similar(
        self,
        user_id: int,
        query_embeddings: list[float],
        document_id: int | None = None,
        top_k: int = 5,
    ):
        try:
            if document_id is not None:
                statement = (
                    Select(VectorsTable.chunk_text)
                    .where(
                        VectorsTable.owner_id == user_id,
                        VectorsTable.document_id == document_id,
                    )
                    .order_by(VectorsTable.embedding.cosine_distance(query_embeddings))
                    .limit(top_k)
                )
                context = self.db.scalars(statement).all()
                return context
            statement = (
                Select(VectorsTable.chunk_text)
                .where(VectorsTable.owner_id == user_id)
                .order_by(VectorsTable.embedding.cosine_distance(query_embeddings))
                .limit(top_k)
            )
            context = self.db.scalars(statement).all()
            return context
        except Exception as e:
            self.log_provider.error_log(
                message="error searching similar vectors", context=str(e)
            )
            raise InfrastructureException("error fetching context") from e

    def delete_context(self, document_id: int, user_id: int):
        try:
            (
                self.db.query(VectorsTable)
                .filter(
                    VectorsTable.document_id == document_id,
                    VectorsTable.owner_id == user_id,
                )
                .delete(synchronize_session=False)
            )
            self.db.commit()
            return
        except Exception as e:
            self.db.rollback()
            self.log_provider.error_log(
                message="error deleting embeddings", context=str(e)
            )
            raise InfrastructureException("error deleting context") from e


class PDFDatabaseRepositoryInfrastructure(PDFDatabaseRepository):
    def __init__(self, db: Session, log_provider: LogProvider):
        self.db = db
        self.log_provider = log_provider

    def create_document(
        self,
        filename: str,
        file_path: str,
        user_id: int,
        status: DocumentStatus,
    ) -> DocumentEntity:
        try:
            new = DocumentsTable(
                filename=filename,
                file_path=file_path,
                status=status,
                user_id=user_id,
            )

            self.db.add(new)
            self.db.commit()
            self.db.refresh(new)

            return DocumentEntity.model_validate(new)
        except Exception as e:
            self.db.rollback()
            self.log_provider.error_log(
                message="error trying to create a new document in the db",
                context=str(e),
            )
            raise InfrastructureException("error creating document") from e

    def get_document(self, document_id: int, user_id: int) -> DocumentEntity | None:
        try:
            stmt = Select(DocumentsTable).where(
                DocumentsTable.id == document_id, DocumentsTable.user_id == user_id
            )
            document = self.db.scalars(statement=stmt).first()

            if not document:
                return None

            return DocumentEntity.model_validate(document)
        except Exception as e:
            self.log_provider.error_log(
                message="error trying to fecth document data",
                context=str(e),
            )
            raise InfrastructureException("error fetching document data") from e

    def get_all_documents(self, user_id: int) -> list[DocumentEntity]:
        try:
            stmt = Select(DocumentsTable).where(DocumentsTable.user_id == user_id)
            documents = self.db.scalars(statement=stmt).all()
            return [DocumentEntity.model_validate(document) for document in documents]
        except Exception as e:
            self.log_provider.error_log(
                message="error fetching documents data", context=str(e)
            )
            raise InfrastructureException("error fetching documents data") from e

    def update_document_status(
        self, document_id: int, user_id: int, status: DocumentStatus
    ) -> DocumentEntity:
        try:
            stmt = Select(DocumentsTable).where(
                DocumentsTable.id == document_id, DocumentsTable.user_id == user_id
            )
            document = self.db.scalars(statement=stmt).first()

            if not document:
                raise InfrastructureException("Document not found")

            document.status = status

            self.db.commit()
            self.db.refresh(document)
            return DocumentEntity.model_validate(document)
        except Exception as e:
            self.db.rollback()
            self.log_provider.error_log(
                message="error updating documents data", context=str(e)
            )
            raise InfrastructureException("error updating documents data") from e

    def delete_document(self, document_id: int, user_id: int) -> None:
        try:
            stmt = Select(DocumentsTable).where(
                DocumentsTable.id == document_id, DocumentsTable.user_id == user_id
            )
            document = self.db.scalars(statement=stmt).first()

            if document:
                self.db.delete(document)
                self.db.commit()
            return
        except Exception as e:
            self.db.rollback()
            self.log_provider.error_log(
                message="error deleting documents data", context=str(e)
            )
            raise InfrastructureException("error deleting documents data") from e
