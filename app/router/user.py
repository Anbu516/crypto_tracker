from fastapi import status,HTTPException,APIRouter,Depends
from ..database import session_object,Users
from ..models import User_register,UserResponse
from .. import utility
from ..oauth2 import get_current_user
from sqlalchemy import select
import logging

router=APIRouter(
    prefix="/api/v1/user",
    tags=["Users"]
)

@router.post("/register",status_code=status.HTTP_201_CREATED,response_model=UserResponse)
async def create_user(new_user:User_register,session:session_object):
    statement = select(Users).where(Users.email == new_user.email)
    result=await session.execute(statement)
    existing_user=result.scalars().first()

    if existing_user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,detail="Email is already registered")
    
    try:
        hashed_password=utility.hash_password(new_user.password)
        new_user.password=hashed_password
        the_user = Users(**new_user.model_dump())
        session.add(the_user)
        await session.commit()
        await session.refresh(the_user)
    except Exception as e:
        await session.rollback()
        print(f"REAL ERROR: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the account"
        )
    return the_user

@router.get("/{id}",response_model=UserResponse)
async def get_user(id: int, session: session_object, current_user: Users = Depends(get_current_user)):
    
    the_user = await session.get(Users, id)
    
    if not the_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {id} not found"
        )
    
    return the_user