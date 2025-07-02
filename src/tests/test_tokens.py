import pytest
from httpx import AsyncClient
from fastapi import HTTPException, status
from jose import jwt
from datetime import datetime, timedelta
from src.auth.auth import hash_password
from src.routers.v1.tokens import get_current_seller
from src.models.sellers import Seller

from src.routers.v1.tokens import (
    JWT_SECRET,
    ALGORITHM,
    ACESS_TOKEN_EXPIRE_TIME_MINS,
    check_password
)


@pytest.fixture
async def seller(db_session):
    seller = Seller(first_name="Anna", last_name="Ivanovna", e_mail="anna@gmail.com", password=hash_password("07876r"))
    db_session.add(seller)
    await db_session.flush()  
    return seller


@pytest.mark.asyncio
async def test_password_hashing():
    password = "07876r"
    hashed = hash_password(password)
    
    assert isinstance(hashed, str)
    assert hashed != password
    assert check_password(password, hashed)
    assert not check_password("wrong_password", hashed)

@pytest.mark.asyncio
async def test_get_current_seller_invalid_token(db_session):
    expired_token = jwt.encode(
        {"sub": "test@gmail.com", "exp": datetime.utcnow() - timedelta(minutes=5)},
        JWT_SECRET,
        algorithm=ALGORITHM
    )
    
    with pytest.raises(HTTPException) as exc:
        await get_current_seller(db_session=db_session, token=expired_token)
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
 
    invalid_token = jwt.encode(
        {"sub": "test@gmail.com"},
        "wrong_secret",
        algorithm=ALGORITHM
    )
    
    with pytest.raises(HTTPException) as exc:
        await get_current_seller(db_session=db_session, token=invalid_token)
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_current_seller_missing_subject(db_session):
    invalid_token = jwt.encode(
        {"exp": datetime.utcnow() + timedelta(minutes=5)},
        JWT_SECRET,
        algorithm=ALGORITHM
    )
    
    with pytest.raises(HTTPException) as exc:
        await get_current_seller(db_session=db_session, token=invalid_token)
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_token_with_invalid_signature(async_client: AsyncClient):
    invalid_token = jwt.encode(
        {"sub": "error@gmail.com", "exp": datetime.utcnow() + timedelta(minutes=30)},
        "wrong_secret_key",
        algorithm=ALGORITHM
    )
    
    response = await async_client.get(
        "/api/v1/seller/1",
        headers={"Authorization": f"Bearer {invalid_token}"}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED