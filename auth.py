from functools import wraps

import jwt
from sanic import text
from sqlalchemy import select

from models import User


def check_token(request):
    if not request.token:
        return False
    try:
        jwt.decode(request.token, request.app.config.SECRET, algorithms=["HS256"])
    except jwt.exceptions.InvalidTokenError:
        return False
    else:
        return True


async def get_info_from_token(request):
    if not request.token:
        return False
    try:
        return jwt.decode(
            request.token, request.app.config.SECRET, algorithms=["HS256"]
        )
    except jwt.exceptions.InvalidTokenError:
        return False


def protected(wrapped):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            is_authenticated = check_token(request)

            if is_authenticated:
                token_info = await get_info_from_token(request)
                session = request.ctx.session
                async with session.begin():
                    stmt = select(User).where(User.id == token_info["user_id"])
                    result = await session.execute(stmt)
                    await session.close()
                user = result.scalar()
                if user.activated:
                    response = await f(request, *args, **kwargs)
                    return response

            return text("You are unauthorized.", 401)

        return decorated_function

    return decorator(wrapped)
