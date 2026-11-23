from fastapi import APIRouter, Depends

from src.domain.entities import UserEntity
from src.infrastructure.api.dependencies.auth_dependencies import get_current_user
from src.infrastructure.api.dependencies.query_dependencies import get_query_use_case
from src.infrastructure.api.schemas import AnswerResponseModel, Request
from src.use_cases.query_use_case import QueryUseCase

router = APIRouter()


@router.post("/query", status_code=200, response_model=AnswerResponseModel)
def get_answer_router(
    data: Request,
    query_use: QueryUseCase = Depends(get_query_use_case),
    user: UserEntity = Depends(get_current_user),
):
    answer = query_use.get_answer(
        plain_query=data.request, user_id=user.id, document_id=data.file_id
    )

    return {"answer": answer}
