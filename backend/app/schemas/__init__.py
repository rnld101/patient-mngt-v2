from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class PatientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    age: int = Field(..., gt=0, le=150)
    gender: str = Field(..., min_length=1, max_length=50)
    blood_group: str = Field(..., min_length=1, max_length=10)
    phone: str = Field(..., min_length=1, max_length=20)
    address: str = Field(..., min_length=1, max_length=500)


class PatientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    age: Optional[int] = Field(None, gt=0, le=150)
    gender: Optional[str] = Field(None, min_length=1, max_length=50)
    blood_group: Optional[str] = Field(None, min_length=1, max_length=10)
    phone: Optional[str] = Field(None, min_length=1, max_length=20)
    address: Optional[str] = Field(None, min_length=1, max_length=500)


class PatientResponse(BaseModel):
    id: int
    name: str
    age: int
    gender: str
    blood_group: str
    phone: str
    address: str
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PatientsListResponse(BaseModel):
    total: int
    patients: list[PatientResponse]


# ── Document schemas ──────────────────────────────────────────────────────────

ALLOWED_DOCUMENT_TYPES = {
    "Prescription",
    "Blood Report",
    "X-Ray",
    "MRI",
    "CT Scan",
    "Other",
}


class DocumentResponse(BaseModel):
    id: int
    patient_id: int
    user_id: int
    document_type: str
    file_name: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    total: int
    documents: list[DocumentResponse]


class DocumentUrlResponse(BaseModel):
    url: str
    expires_in_seconds: int
