from datetime import UTC, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.enums import DocumentStatus
from src.infrastructure.database.conection import Base


class UsersTable(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(
        String(30), unique=True, index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    # Relationships with cascade delete
    vectors: Mapped[list["VectorsTable"]] = relationship(
        "VectorsTable", back_populates="owner", cascade="all, delete-orphan"
    )
    documents: Mapped[list["DocumentsTable"]] = relationship(
        "DocumentsTable", back_populates="owner", cascade="all, delete-orphan"
    )


class DocumentsTable(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        SqlEnum(DocumentStatus), nullable=False, default=DocumentStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    owner: Mapped["UsersTable"] = relationship("UsersTable", back_populates="documents")

    vectors: Mapped[list["VectorsTable"]] = relationship(
        "VectorsTable", back_populates="document", cascade="all, delete-orphan"
    )


class VectorsTable(Base):
    __tablename__ = "vectors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chunk_text: Mapped[str] = mapped_column(Text(), nullable=False)
    embedding: Mapped[Vector] = mapped_column(Vector(3072), nullable=False)

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    owner: Mapped["UsersTable"] = relationship("UsersTable", back_populates="vectors")

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    document: Mapped["DocumentsTable"] = relationship(
        "DocumentsTable", back_populates="vectors"
    )
