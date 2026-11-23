from prometheus_client import Counter, Histogram

from src.domain.enums import DocumentStatus
from src.domain.interfaces import (
    LLMService,
    PDFDatabaseRepository,
    UserDatabaseRepository,
    VectorDatabaseRepository,
)

############################################################################################
ORM_OPERATIONS = Counter(
    "orm_operations_userrepo",
    "lector de aperturas a la base de datos",
    ["type", "table"],
)
ORM_LATENCY = Histogram(
    "orm_latency_userrepo", "tiempo de respuesta de la db con el orm", ["type", "table"]
)
ORM_ERRORS = Counter(
    "orm_errors_userrepo",
    "lector de errores orm",
    ["componente", "operation", "error_type"],
)


class InstrumentedUserDatabaseRepository(UserDatabaseRepository):
    def __init__(self, original: UserDatabaseRepository):
        self._decored = original

    def create_user(self, username: str, email: str, hashed_password: str):
        try:
            with ORM_LATENCY.labels(type="create user", table="users").time():
                ORM_OPERATIONS.labels(type="create user", table="users").inc()
                return self._decored.create_user(
                    username=username, email=email, hashed_password=hashed_password
                )
        except Exception as e:
            ORM_ERRORS.labels(
                componente="user repo db",
                operation="create user",
                error_type=type(e).__name__,
            ).inc()
            raise

    def get_user_by_username(self, username: str):
        try:
            with ORM_LATENCY.labels(type="get_by_username", table="users").time():
                ORM_OPERATIONS.labels(type="get_by_usernma", table="users").inc()
                return self._decored.get_user_by_username(username)
        except Exception as e:
            ORM_ERRORS.labels(
                componente="user repo db",
                operation="get by username",
                error_type=type(e).__name__,
            ).inc()
            raise

    def get_user_by_email(self, email: str):
        try:
            with ORM_LATENCY.labels(type="get_user_by_email", table="users").time():
                ORM_OPERATIONS.labels(type="get_user_by_email", table="users").inc()
                return self._decored.get_user_by_email(email=email)
        except Exception as e:
            ORM_ERRORS.labels(
                componente="get_user_by_email",
                operation="create username",
                error_type=type(e).__name__,
            ).inc()
            raise


class InstrumentedVectorDatabaseRepository(VectorDatabaseRepository):
    def __init__(self, original: VectorDatabaseRepository):
        self._decored = original

    def insert_embeddings(
        self,
        document_id: int,
        user_id: int,
        chunks: list[str],
        embeddings: list[list[float]],
    ):
        try:
            with ORM_LATENCY.labels(type="Insert Embeddings", table="vectors").time():
                ORM_OPERATIONS.labels(type="Insert Embeddings", table="vectors").inc()
                return self._decored.insert_embeddings(
                    document_id=document_id,
                    user_id=user_id,
                    chunks=chunks,
                    embeddings=embeddings,
                )
        except Exception as e:
            ORM_ERRORS.labels(
                componente="Insert Embeddings",
                operation="insert embedings",
                error_type=type(e).__name__,
            ).inc()
            raise

    def search_similar(
        self,
        user_id: int,
        query_embeddings: list[float],
        document_id: int | None = None,
        top_k: int = 5,
    ):
        try:
            with ORM_LATENCY.labels(type="Search Similar", table="vectors").time():
                ORM_OPERATIONS.labels(type="Search Similar", table="vectors").inc()
                return self._decored.search_similar(
                    user_id=user_id,
                    query_embeddings=query_embeddings,
                    document_id=document_id,
                    top_k=top_k,
                )
        except Exception as e:
            ORM_ERRORS.labels(
                componente="Search Similar",
                operation="Search similar",
                error_type=type(e).__name__,
            ).inc()
            raise

    def delete_context(self, document_id: int, user_id: int):
        try:
            with ORM_LATENCY.labels(type="Delete Vector", table="vectors").time():
                ORM_OPERATIONS.labels(type="Delete Vector", table="vectors").inc()
                return self._decored.delete_context(
                    document_id=document_id, user_id=user_id
                )
        except Exception as e:
            ORM_ERRORS.labels(
                componente="Delete Vector",
                operation="Delete Vector",
                error_type=type(e).__name__,
            ).inc()
            raise


class IntrumentedPDFRepository(PDFDatabaseRepository):
    def __init__(self, original: PDFDatabaseRepository):
        self._decored = original

    def create_document(
        self, filename: str, file_path: str, user_id: int, status: DocumentStatus
    ):
        try:
            with ORM_LATENCY.labels(type="create document", table="documents").time():
                ORM_OPERATIONS.labels(type="create document", table="document").inc()
                return self._decored.create_document(
                    filename=filename,
                    file_path=file_path,
                    user_id=user_id,
                    status=status,
                )
        except Exception as e:
            ORM_ERRORS.labels(
                componente="create document",
                operation="create document",
                error_type=type(e).__name__,
            ).inc()
            raise

    def get_document(self, document_id: int, user_id: int):
        try:
            with ORM_LATENCY.labels(type="get document", table="documents").time():
                ORM_OPERATIONS.labels(type="get document", table="document").inc()
                return self._decored.get_document(
                    document_id=document_id, user_id=user_id
                )
        except Exception as e:
            ORM_ERRORS.labels(
                componente="get document",
                operation="get document",
                error_type=type(e).__name__,
            ).inc()
            raise

    def get_all_documents(self, user_id: int):
        try:
            with ORM_LATENCY.labels(type="get documents", table="documents").time():
                ORM_OPERATIONS.labels(type="get documents", table="document").inc()
                return self._decored.get_all_documents(user_id=user_id)
        except Exception as e:
            ORM_ERRORS.labels(
                componente="get documents",
                operation="get document",
                error_type=type(e).__name__,
            ).inc()
            raise

    def update_document_status(
        self, document_id: int, user_id: int, status: DocumentStatus
    ):
        try:
            with ORM_LATENCY.labels(type="update documents", table="documents").time():
                ORM_OPERATIONS.labels(type="update documents", table="document").inc()
                return self._decored.update_document_status(
                    document_id=document_id, user_id=user_id, status=status
                )
        except Exception as e:
            ORM_ERRORS.labels(
                componente="update documents",
                operation="get document",
                error_type=type(e).__name__,
            ).inc()
            raise

    def delete_document(self, document_id: int, user_id: int):
        try:
            with ORM_LATENCY.labels(type="delete documents", table="documents").time():
                ORM_OPERATIONS.labels(type="delete documents", table="document").inc()
                return self._decored.delete_document(
                    document_id=document_id, user_id=user_id
                )
        except Exception as e:
            ORM_ERRORS.labels(
                componente="delete documents",
                operation="get document",
                error_type=type(e).__name__,
            ).inc()
            raise


##########################################################################################
MODEL_OPERATIONS = Counter(
    "model_operaions", "lector de uso de api modelo", ["type", "model"]
)
MODEL_LATENCY = Histogram(
    "model_latency", "tiempo de respuesta API modelo", ["type", "model"]
)
MODEL_ERRORS = Counter(
    "model_errors",
    "lector errores modelo",
    ["componete", "operation", "error_type"],
)

# New counter to track tokens used by Gemini models!
MODEL_TOKENS = Counter(
    "model_tokens_total",
    "Total tokens consumed by LLM models",
    ["model", "token_type"],
)


class InstrumentedRequestModelRepository(LLMService):
    def __init__(self, original: LLMService):
        self._decorated = original

    def generate_embeddings(self, plain_chunks: str | list[str]):
        try:
            with MODEL_LATENCY.labels(
                type="convert into embedings", model="text-embedding-004"
            ).time():
                MODEL_OPERATIONS.labels(
                    type="convert into embeddings", model="text-embedding-004"
                ).inc()

                response = self._decorated.generate_embeddings(
                    plain_chunks=plain_chunks
                )

                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    MODEL_TOKENS.labels(
                        model="text-embedding-001", token_type="total"
                    ).inc(response.usage_metadata.total_token_count)

                return [embedding.values for embedding in response.embeddings]

        except Exception as e:
            MODEL_ERRORS.labels(
                componete="convertor embeddings model",
                operation="converting into embeddings",
                error_type=type(e).__name__,
            ).inc()
            raise

    def get_answer(self, prompt: str):
        try:
            with MODEL_LATENCY.labels(
                type="consult model", model="gemini-3.5-flash-lite"
            ).time():
                MODEL_OPERATIONS.labels(
                    type="consultmodel", model="gemini-3.5-flash-lite"
                ).inc()

                response = self._decorated.get_answer(prompt=prompt)

                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    MODEL_TOKENS.labels(
                        model="gemini-2.5-flash", token_type="prompt"
                    ).inc(response.usage_metadata.prompt_token_count)
                    MODEL_TOKENS.labels(
                        model="gemini-2.5-flash", token_type="response"
                    ).inc(response.usage_metadata.candidates_token_count)
                    MODEL_TOKENS.labels(
                        model="gemini-2.5-flash", token_type="total"
                    ).inc(response.usage_metadata.total_token_count)

                return response.text

        except Exception as e:
            MODEL_ERRORS.labels(
                componete="consult model",
                operation="consult model",
                error_type=type(e).__name__,
            ).inc()
            raise


############################################################################################
