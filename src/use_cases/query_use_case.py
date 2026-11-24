from src.domain.exceptions import NotFoundException
from src.domain.interfaces import (
    LLMService,
    LogProvider,
    VectorDatabaseRepository,
)


class QueryUseCase:
    def __init__(
        self,
        log_provider: LogProvider,
        llm_service: LLMService,
        vector_repository: VectorDatabaseRepository,
    ):
        self.vector_repo = vector_repository
        self.llm_service = llm_service
        self.log_provider = log_provider

    def get_answer(
        self, plain_query: str, user_id: int, document_id: int | None = None
    ) -> str:
        query_embeddings_list = self.llm_service.generate_embeddings(plain_query)

        single_query_vector = query_embeddings_list[0]

        if document_id is not None:
            context = self.vector_repo.search_similar(
                user_id, single_query_vector, document_id
            )
            if not context:
                raise NotFoundException("Context not found")
        else:
            context = self.vector_repo.search_similar(user_id, single_query_vector)
            if not context:
                raise NotFoundException("Context not found")

        prompt = (
            f"Eres un asistente de consulta experto. Responde a la pregunta del usuario "
            f"utilizando únicamente la información provista en el siguiente contexto. "
            f"Si la respuesta no se encuentra en el contexto, di amablemente que no posees esa información. "
            f"No inventes nada.\n\n"
            f"CONTEXTO: {context}\n\n"
            f"PREGUNTA DEL USUARIO: {plain_query}\n\n"
            f"RESPUESTA:"
        )

        answer = self.llm_service.get_answer(prompt=prompt)

        self.log_provider.info_log(
            message=f"Query executed successfully for user_id: {user_id}"
        )

        return answer
