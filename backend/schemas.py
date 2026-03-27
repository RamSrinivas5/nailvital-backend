from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[str] = None
    password: Optional[str] = None

class DeleteAccountRequest(BaseModel):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class Finding(BaseModel):
    result_class: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    recommendation: Optional[str] = None
    confidence: float

class ScanResponse(BaseModel):
    id: int
    image_path: str
    finger: Optional[str] = None
    result_class: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    recommendation: Optional[str] = None
    confidence: float
    findings: List[Finding] = []
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
