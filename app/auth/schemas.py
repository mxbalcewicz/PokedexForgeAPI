from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """Schema for creating a new user"""

    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class UserUpdate(BaseModel):
    """Schema for updating user information"""

    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)


class UserResponse(BaseModel):
    """Schema for user response (excludes sensitive data)"""

    id: int
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserInDB(UserResponse):
    """Schema for user in database (includes password hash)"""

    password_hash: str
 
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Schema for OAuth2 token response"""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token payload data"""

    sub: str  # subject - typically the user email or id
    exp: Optional[int] = None  # expiration time
