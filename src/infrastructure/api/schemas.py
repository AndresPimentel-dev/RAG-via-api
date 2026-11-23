from datetime import datetime

from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class DocumentSchemaResponse(BaseModel):
    id: int
    filename: str
    file_path: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class Request(BaseModel):
    file_id: int | None = None
    request: str


class AnswerResponseModel(BaseModel):
    answer: str
