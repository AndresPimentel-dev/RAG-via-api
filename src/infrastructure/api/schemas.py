from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=30)
    email: EmailStr = Field(max_length=100)
    password: str

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "username": "jane_doe",
                    "email": "jane.doe@example.com",
                    "password": "a-strong-password",
                }
            ]
        }
    )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "access_token": "<jwt>",
                    "token_type": "bearer",
                }
            ]
        }
    )


class DocumentSchemaResponse(BaseModel):
    id: int
    filename: str
    file_path: str
    status: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "filename": "employee-handbook.pdf",
                    "file_path": "users/42/8c3d6af2_employee-handbook.pdf",
                    "status": "processed",
                    "created_at": "2025-01-15T10:30:00Z",
                }
            ]
        },
    )


class Request(BaseModel):
    file_id: int | None = None
    request: str

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "request": "What is the company's vacation policy?",
                    "file_id": 1,
                }
            ]
        }
    )


class AnswerResponseModel(BaseModel):
    answer: str

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "answer": "The handbook states that employees receive 15 days of paid vacation per year."
                }
            ]
        }
    )
