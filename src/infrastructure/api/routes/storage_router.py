from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from src.domain.entities import UserEntity
from src.infrastructure.api.dependencies.auth_dependencies import get_current_user
from src.infrastructure.api.dependencies.storage_dependencies import (
    get_storage_use_case,
)
from src.infrastructure.api.schemas import DocumentSchemaResponse
from src.use_cases.storage_use_case import StorageUseCase

router = APIRouter()

##########################
# storage endpoints
##########


@router.post(
    "/storage",
    status_code=status.HTTP_201_CREATED,
    response_model=DocumentSchemaResponse,
)
async def store_embeddings(
    file: UploadFile = File(..., description="PDF to process"),
    user: UserEntity = Depends(get_current_user),
    storage_case: StorageUseCase = Depends(get_storage_use_case),
) -> DocumentSchemaResponse:
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File has to be a valid PDF",
        )

    file_bytes = await file.read()

    return storage_case.store_file(
        file_bytes=file_bytes, filename=file.filename, user_id=user.id
    )


@router.get("/get", status_code=200, response_model=list[DocumentSchemaResponse])
def get_documents(
    user: UserEntity = Depends(get_current_user),
    storage_case: StorageUseCase = Depends(get_storage_use_case),
) -> list[DocumentSchemaResponse]:
    return storage_case.get_documents_data_by_user_id(user_id=user.id)


@router.delete("/delete/{document_id}", status_code=200)
def delete_document(
    document_id: int,
    user: UserEntity = Depends(get_current_user),
    storage_case: StorageUseCase = Depends(get_storage_use_case),
) -> None:
    return storage_case.delete_file(user_id=user.id, document_id=document_id)
