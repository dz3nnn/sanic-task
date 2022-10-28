from typing import List
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from sanic.exceptions import SanicException

from auth import get_info_from_token
from utils import fake_encode_password
from models import User, Product, Transaction, Account


import traceback
import logging

# Utils


async def is_super_user(request):
    curr_user = await get_current_user(request)
    return curr_user.superuser


# Users


async def get_users(request) -> List[User]:
    session = request.ctx.session
    async with session.begin():
        stmt = select(User).options(selectinload(User.accounts))
        result = await session.execute(stmt)
    return result.scalars().all()


async def get_user_by_request(request) -> User:
    token_info = get_info_from_token(request)
    if token_info:
        user_id = token_info["user_id"]
        session = request.ctx.session
        async with session.begin():
            stmt = (
                select(User)
                .where(User.id == user_id)
                .options(selectinload(User.accounts))
            )
            result = await session.execute(stmt)
        return result.scalar()


async def get_current_user(request):
    current_user = await get_info_from_token(request)
    if current_user and "user_id" in current_user:
        user = await get_user_by_id(request, current_user["user_id"])
        if user:
            return user
    raise SanicException("You are unauthorized.", status_code=401)


async def get_user_by_username(request, username) -> User:
    session = request.ctx.session
    async with session.begin():
        stmt = (
            select(User)
            .where(User.login == username)
            .options(selectinload(User.accounts))
        )
        result = await session.execute(stmt)
    return result.scalar()


async def get_user_by_id(request, pk) -> User:
    session = request.ctx.session
    async with session.begin():
        stmt = select(User).where(User.id == pk).options(selectinload(User.accounts))
        result = await session.execute(stmt)
        user = result.scalar()
    return user


async def get_user_by_link(request, link) -> User:
    session = request.ctx.session
    async with session.begin():
        stmt = (
            select(User)
            .where(User.activate_link == link)
            .options(selectinload(User.accounts))
        )
        result = await session.execute(stmt)
    return result.scalar()


async def create_user(request, user: User):
    session = request.ctx.session
    async with session.begin():
        user.password = fake_encode_password(user.password)
        if not user.accounts:
            acc = Account()
            user.accounts = [acc]
        session.add_all([user])
    return user


async def activate_user(request, user: User):
    session = request.ctx.session
    async with session.begin():
        user.activated = True
        session.commit()
    return user


async def admin_activate_user(request, user_id, activate: bool):
    session = request.ctx.session
    async with session.begin():
        stmt = update(User).where(User.id == user_id).values(activated=activate)
        await session.execute(stmt)


# Products


async def get_product_by_id(request, pk) -> Product:
    session = request.ctx.session
    async with session.begin():
        stmt = select(Product).where(Product.id == pk)
        result = await session.execute(stmt)
    return result.scalar()


async def get_products(request) -> List[Product]:
    session = request.ctx.session
    async with session.begin():
        stmt = select(Product)
        result = await session.execute(stmt)
    return result.scalars().all()


async def add_product(request, product: Product):
    session = request.ctx.session
    async with session.begin():
        session.add(product)


async def update_product(request, id, json_dict):
    session = request.ctx.session
    async with session.begin():
        stmt = (
            update(Product)
            .where(Product.id == id)
            .values(
                title=json_dict["title"],
                description=json_dict["description"],
                price=json_dict["price"],
            )
        )
        await session.execute(stmt)


async def delete_product(request, product_id):
    session = request.ctx.session
    async with session.begin():
        stmt = delete(Product).where(Product.id == product_id)
        await session.execute(stmt)


# Accounts


async def get_accounts_by_user(request, user: User) -> List[Account]:
    session = request.ctx.session
    async with session.begin():
        stmt = select(Account).where(Account.user_id == user.id)
        result = await session.execute(stmt)
    return result.scalars().all()


async def get_account_by_id(request, pk) -> Account:
    session = request.ctx.session
    async with session.begin():
        stmt = select(Account).where(Account.id == pk)
        result = await session.execute(stmt)
    return result.scalar()


async def update_account(request, id, amount):
    session = request.ctx.session
    async with session.begin():
        stmt = update(Account).where(Account.id == id).values(balance=amount)
        await session.execute(stmt)


# Transactions


async def get_transactions_by_user(request, user: User) -> List[Transaction]:
    session = request.ctx.session
    async with session.begin():

        accounts_smtp = select(Account).where(Account.user_id == user.id)
        result = await session.execute(accounts_smtp)
        accounts = result.scalars().all()

        stmt = select(Transaction).where(
            Transaction.bill_id.in_([acc.id for acc in accounts])
        )
        result = await session.execute(stmt)
    return result.scalars().all()


# Payments


async def make_payment_webhook(request, json_dict):
    """
    private_key: приватный ключ, задаётся в свойствах приложения,
    transaction_id: уникальный идентификатор транзакции,
    user_id: пользователь на чеё счёт произойдёт зачисление,
    bill_id: идентификатор счёта (если счёта c таким айди не существует, то но должен быть создан),
    amount: сумма транзакции
    """

    session = request.ctx.session
    async with session.begin():
        try:
            account_stmt = select(Account).where(Account.id == json_dict["bill_id"])
            result = await session.execute(account_stmt)
            account = result.scalar()
            if account:
                # and account in user.accounts?
                account.balance = account.balance + json_dict["amount"]
            else:
                user_stmt = select(User).where(User.id == json_dict["user_id"])
                result = await session.execute(user_stmt)
                user = result.scalar()
                account = Account(
                    id=json_dict["bill_id"], user=user, balance=json_dict["amount"]
                )
                session.add(account)
            # check transaction exists?
            transaction = Transaction(
                id=json_dict["transaction_id"],
                bill_id=json_dict["bill_id"],
                amount=json_dict["amount"],
            )
            session.add(transaction)
            await session.commit()
            return True
        except Exception as e:
            await session.rollback()
            logging.error(traceback.format_exc())
            return False
