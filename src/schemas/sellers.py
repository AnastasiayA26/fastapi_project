from pydantic import BaseModel, Field, field_validator
from pydantic_core import PydanticCustomError

__all__ = ["IncomingSeller", "ReturnedSeller", "ReturnedAllsellers"]


# Базовый класс Seller, содержащий поля, которые есть во всех классах-наследниках.
class BaseSeller(BaseModel):
    first_name: str
    last_name: str
    e_mail: str


# Класс для валидации входящих данных. Не содержит id так как его присваивает БД.
#Нам нужен пароль только на входе, при этом пароль не будет отображаться в return
class IncomingSeller(BaseSeller):
    password: str


# Класс, валидирующий исходящие данные. Он уже содержит id
class ReturnedSeller(BaseSeller):
    id: int


# Класс для возврата массива объектов "Книга"
class ReturnedAllsellers(BaseModel):
    seller: list[ReturnedSeller]
