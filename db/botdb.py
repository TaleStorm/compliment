import aioredis
import os
import asyncio

from example import User, ContactsUser
from data_manager import DataManager
from main import KeySchema


pool = aioredis.create_pool("redis://localhost", encoding='utf-8')
redis = aioredis.Redis(pool_or_conn=pool)
print('data', type(redis))

us = redis.smembers(KeySchema().users_set())

def db_add_user(message, state):
    """
    Заполнение таблицы users
    """
    with state.proxy() as data:
        user = User(data['name'], data['birthday'], message.chat.id)
        dm.add(user)


dm = DataManager('sqlite:///db/sqlite3.db')
dm._create_table(User)
dm._create_table(ContactsUser)
