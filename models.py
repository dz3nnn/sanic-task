"""

Пользователь – репрезентация пользователей в приложении. Должны быть обычные и админ пользователи (админ назначается руками в базе или создаётся на старте приложения)
Товар – Состоит из заголовка, описания и цены
Счёт – Имеет идентификатор счёта и баланс. Привязан к пользователю. У пользователя может быть несколько счетов
Транзакция – история зачисления на счёт, хранит сумму зачисления и идентификатор счёта


"""
from sqlalchemy import (
    INTEGER,
    Column,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Boolean,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

from utils import generate_uuid


Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True
    id = Column(INTEGER(), primary_key=True)


class User(BaseModel):
    __tablename__ = "user"

    login = Column(String())
    password = Column(String())
    activated = Column(Boolean(), default=False)
    superuser = Column(Boolean(), default=False)

    activate_link = Column(String, default=generate_uuid)

    accounts = relationship("Account")

    def to_dict(self):
        return {
            "id": self.id,
            "login": self.login,
            "password": self.password,
            "activated": self.activated,
            "superuser": self.superuser,
            "accounts": [{"balance": acc.balance} for acc in self.accounts],
        }

    def get_all_amount(self):
        result = 0
        for acc in self.accounts:
            result = result + acc.balance
        return result


class Product(BaseModel):
    __tablename__ = "product"

    title = Column(String())
    description = Column(Text())
    price = Column(Float())  # Decimal?

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "price": self.price,
        }


class Account(BaseModel):
    __tablename__ = "account"

    user_id = Column(ForeignKey("user.id"))
    user = relationship("User", back_populates="accounts")
    balance = Column(Float(), default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "balance": self.balance,
        }


class Transaction(BaseModel):
    __tablename__ = "transaction"

    bill_id = Column(Integer())
    amount = Column(Float())

    def to_dict(self):
        return {
            "id": self.id,
            "bill_id": self.bill_id,
            "amount": self.amount,
        }
