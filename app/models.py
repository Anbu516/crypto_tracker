from pydantic import BaseModel, EmailStr
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: str | None = None
    role: str | None = None

class User_register(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    model_config = {"from_attributes": True}

class PortfolioCreate(BaseModel):
    coin_id: str
    symbol: str
    quantity: float

class PortfolioResponse(PortfolioCreate):
    id: int
    user_id: int

    model_config = {"from_attributes": True}