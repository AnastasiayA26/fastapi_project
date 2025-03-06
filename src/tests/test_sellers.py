import pytest
from sqlalchemy import select
from src.models.sellers import Seller
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.books import Book
from fastapi import status
from fastapi.testclient import TestClient
from src.auth.auth import hash_password
from icecream import ic
from fastapi import HTTPException



# Тест на ручку создающую продавца
@pytest.mark.asyncio
async def test_create_seller(async_client):
    data = {
        "first_name": "anna",
        "last_name": "Ivanova",
        "e_mail": "ivanovaanna12@gmail.com",
        "password": "1234567",
    }
    response = await async_client.post("/api/v1/seller/", json=data)

    assert response.status_code == status.HTTP_201_CREATED

    result_data = response.json()

    resp_seller_id = result_data.pop("id", None)
    assert resp_seller_id, "Seller id not returned from endpoint"

    assert result_data == {
        "first_name": "anna",
        "last_name": "Ivanova",
        "e_mail": "ivanovaanna12@gmail.com",
    }


# Тест на ручку получения списка продавцов
@pytest.mark.asyncio
async def test_get_sellers(db_session, async_client):
    # Создаем продавца вручную, а не через ручку, чтобы нам не попасться на ошибку которая
    # может случиться в POST ручке
    seller = Seller(first_name="Artem", last_name="Popov", e_mail="popov@gmail.com", password="67895")
    seller_1 = Seller(first_name="Anastasia", last_name="ivanova", e_mail="ivanova@gmail.com", password="0975")
    db_session.add_all([seller, seller_1])
    await db_session.flush()

    response = await async_client.get("/api/v1/seller/")

    assert response.status_code == status.HTTP_200_OK

    assert (
        len(response.json()["seller"]) == 2
    )  # Опасный паттерн! Если в БД есть данные, то тест упадет

    # Проверяем интерфейс ответа, на который у нас есть контракт.
    assert response.json() == {
        "seller": [
            {
                "first_name": "Artem",
                "last_name": "Popov",
                "e_mail": "popov@gmail.com",
                "id": seller.id,
            },
            {
                "first_name": "Anastasia",
                "last_name": "ivanova",
                "e_mail": "ivanova@gmail.com",
                "id": seller_1.id,
            },
        ]
    }

# Тест на ручку получения одного продавца и всех книг, принадлежащих ему
@pytest.mark.asyncio
async def test_get_single_seller(db_session, async_client):
    # Создаем продавца и книги
    seller = Seller(first_name="Daniil", last_name="Popov", e_mail="popov@gmail.com", password="67895")
    db_session.add(seller)
    await db_session.flush()

    book = Book(author="Pushkin", title="Eugeny Onegin", year=2001, pages=104, seller_id=seller.id)
    book_2 = Book(author="Lermontov", title="Mziri", year=2015, pages=104, seller_id=seller.id)

    db_session.add_all([book, book_2])
    await db_session.commit()  # <-- ключевой момент

    response = await async_client.get(f"/api/v1/seller/{seller.id}")

    assert response.status_code == status.HTTP_200_OK

    assert response.json() == {
        "id": seller.id,
        "first_name": "Daniil",
        "last_name": "Popov",
        "e_mail": "popov@gmail.com",
        "books": [
            {
                "title": "Eugeny Onegin",
                "author": "Pushkin",
                "year": 2001,
                "id": book.id,
                "pages": 104,
                "seller_id": book.seller_id,
            },
            {
                "id": book_2.id,
                "title": "Mziri",
                "author": "Lermontov",
                "year": 2015,
                "id": book_2.id,
                "pages": 104,
                "seller_id": book_2.seller_id,
            }
        ]
    }
# ##
# # Тест на ручку получения одного продавца и всех книг, принадлежащих ему
# @pytest.mark.asyncio
# async def test_get_single_seller(db_session, async_client):
#     # Создаем продавца и книги
#     seller = Seller(first_name="Daniil", last_name="Popov", e_mail="popov@gmail.com", password=hash_password("67895"))
#     db_session.add(seller)
#     await db_session.flush()

#     data = {
#         "username": "popov@gmail.com", 
#         "password": "67895"
#     }
#     token_response = await async_client.post("/api/v1/token/", data=data)
#     token = token_response.json().get("access_token")
#     headers = {"Authorization": f"Bearer {token}"}

#     book = Book(author="Pushkin", title="Eugeny Onegin", year=2001, pages=104, seller_id=seller.id)
#     book_2 = Book(author="Lermontov", title="Mziri", year=2015, pages=104, seller_id=seller.id)

#     db_session.add_all([book, book_2])
#     await db_session.flush()

#     response = await async_client.get(f"/api/v1/seller/{seller.id}", headers = headers)

#     assert response.status_code == status.HTTP_200_OK

#     assert response.json() == {
#         "id": seller.id,
#         "first_name": "Daniil",
#         "last_name": "Popov",
#         "e_mail": "popov@gmail.com",
#         "books": [
#             {
#                 "title": "Eugeny Onegin",
#                 "author": "Pushkin",
#                 "year": 2001,
#                 "id": book.id,
#                 "pages": 104,
#                 "seller_id": book.seller_id,
#             },
#             {
#                 "id": book_2.id,
#                 "title": "Mziri",
#                 "author": "Lermontov",
#                 "year": 2015,
#                 "id": book_2.id,
#                 "pages": 104,
#                 "seller_id": book_2.seller_id,
#             }
#         ]
#     }


# Тест на ручку обновления продавца без изменения пароля
@pytest.mark.asyncio
async def test_update_seller(db_session, async_client):
    # Создаем продавца вручную, а не через ручку, чтобы нам не попасться на ошибку которая
    # может случиться в POST ручке
    seller = Seller(first_name="Daniil", last_name="Popov", e_mail="popov@gmail.com", password="67895")

    db_session.add(seller)
    await db_session.commit()

    response = await async_client.put(
        f"/api/v1/seller/{seller.id}",
        json={
            "first_name": "Ivan",
            "last_name": "Popov",
            "e_mail": "ivanpopov@gmail.com",
            "id": seller.id,
        },
    )

    assert response.status_code == status.HTTP_200_OK
    await db_session.flush()

    # Проверяем, что обновились все поля
    res = await db_session.get(Seller, seller.id)
    assert res.first_name == "Ivan"
    assert res.last_name == "Popov"
    assert res.e_mail == "ivanpopov@gmail.com"
    assert res.id == seller.id
    assert res.password == seller.password



@pytest.mark.asyncio
async def test_delete_seller_with_invalid_seller_id(db_session, async_client):
    seller = Seller(first_name="Anastasia", last_name="ivanova", e_mail="ivanova@gmail.com", password=hash_password("0975"))

    db_session.add(seller)
    await db_session.flush()

    data = {
        "username": "ivanova@gmail.com", 
        "password": "0975"
    }
    token_response = await async_client.post("/api/v1/token/", data=data)
    token = token_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    response = await async_client.delete(f"/api/v1/books/{seller.id + 1}", headers = headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_seller(db_session, async_client):
    seller = Seller(first_name="Anastasia", last_name="ivanova", e_mail="ivanova@gmail.com", password="0975")

    db_session.add(seller)
    await db_session.flush()
    book = Book(author="Pushkin", title="Eugeny Onegin", year=2001, pages=104, seller_id=seller.id)
    db_session.add(book)
    await db_session.flush()

    response = await async_client.delete(f"/api/v1/seller/{seller.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    deleted_seller = await db_session.get(Seller, seller.id)
    assert deleted_seller is None
    all_books = await db_session.execute(select(Book).filter(Book.seller_id == seller.id))
    books = all_books.scalars().all()
    assert len(books) == 0 

    all_sellers = await db_session.execute(select(Seller))
    sellers = all_sellers.scalars().all()
    assert len(sellers) == 0
