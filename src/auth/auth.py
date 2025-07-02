import jwt
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Dict



ACESS_TOKEN_EXPIRE_TIME_MINS = 60 * 12 


JWT_SECRET = "my_secret_key_123123123"                                   
ALGORITHM = "HS256"


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated = "auto")

oath_bearer = OAuth2PasswordBearer(tokenUrl="api/v1/token")


def create_token(data: dict, expire_delta: timedelta):
    expires = expire_delta + datetime.utcnow() 
    to_encode = data.copy()
    to_encode.update({'exp': expires})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)


def hash_password(password: str):
    return bcrypt_context.hash(password)


def check_password(password: str, hashed_password: str):
    return bcrypt_context.verify(password, hashed_password)