from datetime import datetime, timezone

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status

from app.core.database import Base
from app.auth.security import get_password_hash, verify_password


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def verify_password(self, plain_password: str) -> bool:
        is_valid, _ = verify_password(plain_password, self.password_hash)
        return is_valid

    def set_password(self, plain_password: str) -> None:
        self.password_hash = get_password_hash(plain_password)

    @classmethod
    async def get_by_email(cls, db: AsyncSession, email: str) -> "User | None":
        """Get user by email"""
        result = await db.execute(select(cls).where(cls.email == email))
        return result.scalar_one_or_none()

    @classmethod
    async def create(cls, db: AsyncSession, email: str, password: str) -> "User":
        """Create a new user in the database"""
        existing_user = await cls.get_by_email(db, email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        user = cls(email=email)
        user.set_password(password)
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @classmethod
    async def authenticate(cls, db: AsyncSession, email: str, password: str) -> "User | None":
        """Authenticate user by email and password"""
        user = await cls.get_by_email(db, email)
        if not user or not user.verify_password(password):
            return None
        return user
