import jwt
from sanic.exceptions import SanicException
from sanic import Blueprint, text

from db import get_user_by_username
from utils import check_hashed_pass

login = Blueprint("login", url_prefix="/login")


@login.post("/")
async def do_login(request):
    if request.json:
        username = request.json.get("username")
        password = request.json.get("password")
        if username and password:
            user = await auth(request, username, password)
            if user:
                token = jwt.encode({"user_id": user.id}, request.app.config.SECRET)
                return text(token)
        raise SanicException("Username and password required.", status_code=500)
    raise SanicException("Empty json.", status_code=500)


async def auth(request, username, password):
    user = await get_user_by_username(request, username)
    if user:
        if check_hashed_pass(password, user.password):
            if user.activated:
                return user
            raise SanicException("User not activated.", status_code=500)
    raise SanicException("Wrong username or password.", status_code=500)
