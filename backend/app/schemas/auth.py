import re
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


UserRole = Literal["admin", "technician", "employee"]



class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    must_change_password: bool
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    created_at: datetime

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if len(value) > 255 or "@" not in value or "." not in value.rsplit("@", 1)[-1]:
            raise ValueError("A valid email address is required")
        return value


class LoginResponse(BaseModel):
    user: UserRead


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    email: str
    full_name: str = Field(min_length=2, max_length=160)
    role: Literal["technician", "employee"]

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("Tên đăng nhập phải là chuỗi ký tự")
        clean = value.strip().lower()
        clean = re.sub(r"\s+", ".", clean)
        if len(clean) < 3:
            raise ValueError("Tên đăng nhập phải có ít nhất 3 ký tự (Username must be at least 3 characters)")
        if len(clean) > 80:
            raise ValueError("Tên đăng nhập tối đa 80 ký tự")
        if not re.fullmatch(r"^[a-z0-9._-]+$", clean):
            raise ValueError("Tên đăng nhập chỉ được dùng chữ cái, số, dấu chấm '.', gạch dưới '_' hoặc gạch ngang '-' (Letters, numbers, ., _, - only)")
        return clean

    @field_validator("full_name", mode="before")
    @classmethod
    def normalize_full_name(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("Họ và tên phải là chuỗi ký tự")
        clean = value.strip()
        if len(clean) < 2:
            raise ValueError("Họ và tên phải có ít nhất 2 ký tự (Full name must be at least 2 characters)")
        return clean

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("Email phải là chuỗi ký tự")
        clean = value.strip().lower()
        if len(clean) > 255 or "@" not in clean or "." not in clean.rsplit("@", 1)[-1]:
            raise ValueError("Địa chỉ email không hợp lệ (cần có định dạng name@domain.com)")
        return clean



class UserCreated(UserRead):
    temporary_password: str


class PasswordResetResponse(BaseModel):
    temporary_password: str
    user: UserRead


class UserActiveUpdate(BaseModel):
    is_active: bool

