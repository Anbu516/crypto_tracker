from fastapi import APIRouter,Depends,HTTPException,status,Request
from ..database import session_object,Users
from fastapi.security import OAuth2PasswordRequestForm
from ..utility import verify
from ..oauth2 import create_access_token
from ..models import Token
from sqlalchemy import select
import logging

router = APIRouter(prefix="/api/v1/auth",tags=['Authentication'])

@router.post("/login",response_model=Token)
async def login(request:Request,session:session_object,user_credentials:OAuth2PasswordRequestForm=Depends()):
    try:
        result = await session.execute(select(Users).where(Users.email==user_credentials.username))
        user = result.scalars().first()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="An error occured during login")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Invalid Credentials'
        )
    
    if not verify(user_credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Invalid Credentials'
        )
    
    access_token = create_access_token(data={"sub": str(user.id),"role":"user"})  
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }