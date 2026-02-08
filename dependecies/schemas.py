from pydantic import BaseModel,EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class User(BaseModel):
    username: str
    email: str | None = None
    password: str

class loginForm(BaseModel):
    username: str
    password: str

class registerForm(BaseModel):
    username: str
    email: EmailStr
    password: str