# Для импорта из корневого модуля
# import sys
# sys.path.append("..")
# from main import app

from typing import Annotated
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy import delete
from src.models.sellers import Seller
from src.models.books import Book
from src.schemas import IncomingSeller, ReturnedSeller, ReturnedAllsellers
from icecream import ic
from sqlalchemy.ext.asyncio import AsyncSession
from src.configurations import get_async_session
from sqlalchemy.orm import selectinload

sellers_router = APIRouter(tags=["seller"], prefix="/seller")

# CRUD - Create, Read, Update, Delete

DBSession = Annotated[AsyncSession, Depends(get_async_session)]


# Ручка для создания записи о продавца в БД. Возвращает запись.
# @sellers_router.post("/seller/", status_code=status.HTTP_201_CREATED)
@sellers_router.post(
    "/", response_model=ReturnedSeller, status_code=status.HTTP_201_CREATED
)  # Прописываем модель ответа
async def create_sellers(
    seller: IncomingSeller,
    session: DBSession,
):  # прописываем модель валидирующую входные данные
    # session = get_async_session() вместо этого мы используем иньекцию зависимостей DBSession

    # это - бизнес логика. Обрабатываем данные, сохраняем, преобразуем и т.д.
    new_seller = Seller(
        **{
            "first_name": seller.first_name,
            "last_name": seller.last_name,
            "e_mail": seller.e_mail,
            "password": seller.password,
        }
    )

    session.add(new_seller)
    await session.flush()

    return new_seller


# Ручка, возвращающая всех продавцов
@sellers_router.get("/", response_model=ReturnedAllsellers)
async def get_all_sellers(session: DBSession):
    # Хотим видеть формат
    # sellers: [{"id": 1, "title": "blabla", ...., "year": 2023},{...}]
    query = select(Seller)  # SELECT * FROM seller
    result = await session.execute(query)
    sellers = result.scalars().all()
    # returned_sellers = [
    #     ReturnedSeller(
    #         id=s.id,
    #         first_name=s.first_name,
    #         last_name=s.last_name,
    #         e_mail=s.e_mail,
    #     )
    #     for s in sellers
    # ]

    # return {"sellers": returned_sellers}
    return {"seller": sellers}


# # Ручка для получения продавца по ее ИД
# @sellers_router.get("/{seller_id}", response_model=ReturnedSeller)
# async def get_seller(seller_id: int, session: DBSession):
#     if seller := await session.get(Seller, seller_id):
#         query = select(Book).where(Book.seller_id == seller_id)
#         result = await session.execute(query)
#         books = result.scalars().all()
   
#         books_data = [{
#                     "title": book.title,
#                     "author": book.author,
#                     "year": book.year,
#                     "pages": book.pages,
#                     "id": book.id
#                 } for book in books]

#         return { 
#             "id": seller.id,
#             "first_name": seller.first_name,
#             "last_name": seller.last_name,
#             "e_mail": seller.e_mail,
#             "books": books_data
#         }

#     return Response(status_code=status.HTTP_404_NOT_FOUND)

@sellers_router.get("/{seller_id}", response_model=ReturnedSeller)
async def get_seller(seller_id: int, session: DBSession):
    result = await session.execute(
        select(Seller).options(selectinload(Seller.seller_books)).filter(Seller.id == seller_id) 
    )
    seller = result.scalar_one_or_none()  # Получаем одного продавца, либо None, если не найден
    if seller:
        return ReturnedSeller(
            id=seller.id,
            first_name=seller.first_name,
            last_name=seller.last_name,
            e_mail=seller.e_mail,
            books=seller.seller_books
        )
    return Response(status_code=status.HTTP_404_NOT_FOUND)

# Ручка для удаления продавца
@sellers_router.delete("/{seller_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_seller(seller_id: int, session: DBSession):
    deleted_seller = await session.get(Seller, seller_id)
    ic(deleted_seller)  # Красивая и информативная замена для print. Полезна при отладке.
    if deleted_seller:
        await session.execute(delete(Book).where(Book.seller_id == seller_id))
        await session.delete(delete_seller)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


# Ручка для обновления данных о продавце
@sellers_router.put("/{seller_id}", response_model=ReturnedSeller)
async def update_seller(seller_id: int, new_seller_data: ReturnedSeller, session: DBSession):
    # Оператор "морж", позволяющий одновременно и присвоить значение и проверить его. Заменяет то, что закомментировано выше.
    if updated_seller := await session.get(Seller, seller_id):
        updated_seller.first_name = new_seller_data.first_name
        updated_seller.last_name = new_seller_data.last_name
        updated_seller.e_mail = new_seller_data.e_mail

        await session.flush()

        return updated_seller

    return Response(status_code=status.HTTP_404_NOT_FOUND)