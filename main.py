from sanic import Sanic
from sanic_openapi import openapi3_blueprint

from routes import setup_routes
from middlewares import setup_middlewares
from login import login
from settings import settings, bind, async_session_factory
from models import Base, User, Account, Product

import asyncio

app = Sanic(__name__)
app.update_config(settings)

# app.blueprint(openapi3_blueprint)
app.blueprint(login)


def setup_database(engine):
    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

        session = async_session_factory()

        user = User(
            login="username",
            password="password",
            activated=True,
            superuser=True,
            accounts=[Account(balance=1000)],
        )

        product = Product(title="sometitle", description="somedesc", price=100)

        async with session.begin():
            session.add_all([user, product])

    asyncio.run(init_models())


def init():

    setup_routes(app)
    setup_middlewares(app, bind)

    setup_database(bind)

    app.run(
        debug=app.config.DEBUG,
        workers=2,
    )
