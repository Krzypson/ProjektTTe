from fastapi import HTTPException, status, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, ExpiredSignatureError
from datetime import datetime, timedelta
from database import DB_main as dbm
from pwdlib import PasswordHash
from pydantic import EmailStr
from auth.config import settings
from dependecies.schemas import TokenData
from jwt.exceptions import InvalidTokenError

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

pwd_hash = PasswordHash.recommended()

def create_access_token(data: dict):
    token_data = data.copy()
    expire_time = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data.update({"exp": expire_time.timestamp()})
    return jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(request: Request, token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        token = request.cookies.get("access_token")
        if not token:
            raise credentials_exception
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        raise credentials_exception
    user = dbm.select_user_info(token_data.username)
    if user is None:
        raise credentials_exception
    return user

def authenticate_user(username: str, password: str):
    user = dbm.select_user_info(username)
    if not user:
        return False
        #raise HTTPException(status_code=401, detail="Incorrect username")
    if not pwd_hash.verify(password,user.password):
        return False
        #raise HTTPException(status_code=401, detail="Incorrect password")
    return True

def create_user(username: str, password: str, email: EmailStr = None):
    if dbm.select_user_info(username):
        return "username is already taken"
    else:
        return dbm.add_user(username, pwd_hash.hash(password), email)