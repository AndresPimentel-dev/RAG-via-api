from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserEntity(BaseModel):
    id: int | None = None
    username: str
    email: str
    hashed_password: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentEntity(BaseModel):
    id: int | None = None
    filename: str
    file_path: str
    user_id: int
    status: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
