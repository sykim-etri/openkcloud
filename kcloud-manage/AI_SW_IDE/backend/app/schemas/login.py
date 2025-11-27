from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    email: str
    name: str
    role: str
    department: Optional[str] = None


class UserCreate(UserBase):
    password: str

class LoginResponse(BaseModel):
    success: bool
    user: UserBase      
    access_token: str
    refresh_token: Optional[str] = None

    class Config:
        from_attributes = True
        
class LoginRequest(BaseModel):
    email: str
    password: str
    
        
class RefreshTokenRequest(BaseModel):
    refresh_token: str
