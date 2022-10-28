from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

import os

load_dotenv()

settings = {
    "HOST": os.getenv("HOST"),
    "PORT": os.getenv("PORT"),
    "DEBUG": os.getenv("DEBUG"),
    "DB_URL": os.getenv("DB_URL"),
    "SECRET": os.getenv("SECRET_KEY"),
}

bind = create_async_engine(
    settings["DB_URL"], future=True, echo=True, poolclass=NullPool
)

async_session_factory = sessionmaker(bind, AsyncSession)
