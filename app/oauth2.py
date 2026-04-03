import jwt
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from . import database, models
from .config import settings
from datetime import datetime,timezone,timedelta

user_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", scheme_name="userAuth")

SECERET_KEY = settings.secret_key
ALGORITHM = settings.algorithm

def create_access_token(data:dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc)+timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp":expire})
    return jwt.encode(to_encode,SECERET_KEY,algorithm=ALGORITHM)

async def get_current_user(session:database.session_object,token: str = Depends(user_scheme)):
    try:
        payload=jwt.decode(token,SECERET_KEY,algorithms=ALGORITHM)
        user_id, role = payload.get("sub"), payload.get("role")
        if not user_id or role != "user":
            raise HTTPException(status_code=403, detail="user role required")
        user = await session.get(database.Users, int(user_id))
        if not user:
            raise HTTPException(status_code=401)
        return user
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401,detail="Invalid Token")
    