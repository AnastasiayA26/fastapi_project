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
from src.schemas import IncomingSeller, ReturnedSeller, ReturnedAllsellers, ReturnedSellerWithBooks, ReturnedBook
from icecream import ic
from sqlalchemy.ext.asyncio import AsyncSession
from src.configurations import get_async_session
from sqlalchemy.orm import selectinload
from fastapi.responses import JSONResponse

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
    return {"seller": sellers}


@sellers_router.get("/{seller_id}", response_model=ReturnedSellerWithBooks)
async def get_seller(seller_id: int, session: DBSession):
    result = await session.execute(
        select(Seller).options(selectinload(Seller.seller_books)).filter(Seller.id == seller_id)
    )
    seller = result.scalar_one_or_none()

    if not seller:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return ReturnedSellerWithBooks(
        id=seller.id,
        first_name=seller.first_name,
        last_name=seller.last_name,
        e_mail=seller.e_mail,
        books=[
            ReturnedBook(
                id=book.id,
                title=book.title,
                author=book.author,
                year=book.year,
                pages=book.pages,
                seller_id=book.seller_id
            )
            for book in seller.seller_books
        ]
    )


@sellers_router.delete("/{seller_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_seller(seller_id: int, session: DBSession):
    deleted_seller = await session.get(Seller, seller_id)
    ic(deleted_seller)  # Красивая и информативная замена для print. Полезна при отладке.
    if deleted_seller:
        books_to_delete = await session.execute(select(Book).filter(Book.seller_id == seller_id))
        books = books_to_delete.scalars().all()
        ic(books) 
        
        if books:
            await session.execute(delete(Book).where(Book.seller_id == seller_id))
        
        await session.delete(deleted_seller)
        await session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


# @sellers_router.delete("/{seller_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_seller(seller_id: int, session: AsyncSession):
#     deleted_seller = await session.get(Seller, seller_id)
#     ic(deleted_seller)  # Красивая и информативная замена для print. Полезна при отладке.
    
#     if deleted_seller:
#         # Удаляем книги, связанные с продавцом
#         await session.execute(delete(Book).where(Book.seller_id == seller_id))
#         # Удаляем самого продавца
#         await session.delete(deleted_seller)
#         # Сохраняем изменения
#         return Response(status_code=status.HTTP_204_NO_CONTENT)
#     else:
#         return Response(status_code=status.HTTP_404_NOT_FOUND)
    
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

