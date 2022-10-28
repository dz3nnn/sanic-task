from sanic import json
from sanic.exceptions import SanicException

from auth import protected
from utils import validate_signature, prepare_signature, success_json
from models import User

from db import *


def setup_routes(app):

    """

    Users

    """

    @app.get("/activate/<activate_link:str>")
    async def activate_user_endpoint(request, activate_link):
        user = await get_user_by_link(request, activate_link)
        if user:
            activate = await activate_user(request, user)
            return success_json()
        raise SanicException("Wrong link.", status_code=500)

    @app.get("/users/me")
    @protected
    async def get_current_user_endpoint(request):
        user = await get_current_user(request)
        return json(user.to_dict())

    @app.get("/users")
    @protected
    async def get_users_endpoint(request):
        if await is_super_user(request):
            users = await get_users(request)
            return json([user.to_dict() for user in users])
        else:
            return json({}, status=404)

    @app.post("/users/activate")
    @protected
    async def admin_activate_user_endpoint(request):
        if await is_super_user(request):
            if request.json and request.json.get("user_id"):
                await admin_activate_user(request, request.json.get("user_id"), True)
                return success_json()
            raise SanicException("user_id required.", status_code=500)
        else:
            return json({}, status=404)

    @app.post("/users/deactivate")
    @protected
    async def admin_deactivate_user_endpoint(request):
        if await is_super_user(request):
            if request.json and request.json.get("user_id"):
                await admin_activate_user(request, request.json.get("user_id"), False)
                return success_json()
            raise SanicException("user_id required.", status_code=500)
        else:
            return json({}, status=404)

    @app.post("/users")
    async def create_user_endpoint(request):
        if request.json:
            username = request.json.get("username")
            password = request.json.get("password")

            check_usr = await get_user_by_username(request, username)

            if not check_usr:
                usr = User(login=username, password=password)
                user = await create_user(request, usr)
                return json(
                    {"activate_link": f"{request.host}/activate/{user.activate_link}"}
                )
            raise SanicException("User already registered.", status_code=500)

        raise SanicException("Empty json.", status_code=500)

    @app.get("/users/<id:int>")
    @protected
    async def get_user_endpoint(request, id):
        user = await get_user_by_id(request, id)
        if not user:
            return json({}, status=404)
        return json(user.to_dict())

    """
    
    Accounts
    
    """

    @app.get("/accounts/me")
    @protected
    async def get_current_user_accounts_endpoint(request):
        user = await get_current_user(request)
        accounts = await get_accounts_by_user(request, user)
        return json([acc.to_dict() for acc in accounts])

    """
    
    Transactions
    
    """

    @app.get("/transactions/me")
    @protected
    async def get_current_user_transactions_endpoint(request):
        user = await get_current_user(request)
        transactions = await get_transactions_by_user(request, user)
        return json([trx.to_dict() for trx in transactions])

    """

    Products
    
    """

    @app.get("/products")
    @protected
    async def get_products_endpoint(request):
        prods = await get_products(request)
        if not prods:
            return json({})
        return json([prod.to_dict() for prod in prods])

    @app.post("/products")
    @protected
    async def add_product_endpoint(request):
        if is_super_user(request):
            if request.json and all(
                k in request.json for k in ("title", "description", "price")
            ):
                await add_product(
                    request,
                    Product(
                        title=request.json.get("title"),
                        description=request.json.get("description"),
                        price=request.json.get("price"),
                    ),
                )
                return success_json()
            else:
                return SanicException(
                    "title,description,price required.", status_code=500
                )
        else:
            return json({}, status=404)

    @app.delete("/products/<id:int>")
    @protected
    async def delete_product_endpoint(request, id):
        if await is_super_user(request):
            await delete_product(request, id)
            return success_json()
        else:
            return json({}, status=404)

    @app.patch("/products/<id:int>")
    @protected
    async def update_product_endpoint(request, id):
        if await is_super_user(request):
            product = await get_product_by_id(request, id)
            if product:
                if request.json and all(
                    k in request.json for k in ("title", "description", "price")
                ):
                    await update_product(
                        request,
                        id,
                        request.json,
                    )
                    upd_prod = await get_product_by_id(request, id)
                    return json(upd_prod.to_dict())
                else:
                    return SanicException(
                        "title,description,price required.", status_code=500
                    )
            else:
                return json({}, status=404)
        else:
            return json({}, status=404)

    @app.get("/products/<id:int>")
    @protected
    async def get_product_endpoint(request, id):
        prod = await get_product_by_id(request, id)
        if not prod:
            return json({}, status=404)
        return json(prod.to_dict())

    @app.post("/products/buy/<id:int>")
    @protected
    async def buy_product_endpoint(request, id):
        if request.json:
            account_id = request.json.get("account_id")
            product = await get_product_by_id(request, id)
            if account_id and product:
                account = await get_account_by_id(request, account_id)
                user = await get_current_user(request)
                if (
                    account
                    and account.user_id == user.id
                    and product.price <= account.balance
                ):
                    new_balance = account.balance - product.price
                    await update_account(request, id, new_balance)
                    return json({"success": "true"})
                else:
                    raise SanicException("Wrong account.", status_code=500)
            else:
                raise SanicException(
                    "Account id and product id required.", status_code=500
                )
        raise SanicException("Empty json.", status_code=500)

    """

    Payments
    
    """

    @app.post("/payment/webhook")
    async def payment_webhook_endpoint(request):
        if request.json and validate_signature(app.config.SECRET, request.json):
            result = await make_payment_webhook(request, request.json)
            return json({"success": result})
        raise SanicException("Wrong json.", status_code=500)

    if app.config.DEBUG:

        @app.post("/payment/webhook1")
        async def payment_webhook_create_endpoint(request):
            return json(
                {"signature": prepare_signature(app.config.SECRET, request.json)}
            )
