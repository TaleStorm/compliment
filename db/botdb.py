from example import User, ContactsUser
from data_manager import DataManager
#from main import KeySchema

from loguru import logger
from dotenv import load_dotenv
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher
import aioredis

from random import randint
from datetime import datetime as dt
import os
import asyncio

# class RedisMiddleware(LifetimeControllerMiddleware):
#     def __init__(self):
#         super().__init__()

#     async def pre_process(self, obj, data, *args):
#         pool = await aioredis.create_pool(
#             "redis://localhost",
#             encoding='utf-8'
#         )
#         data['redis'] = aioredis.Redis(pool_or_conn=pool)

# class KeySchema:
#     """
#     Возвращает название таблиц для Redis.
#     """

#     def user_messages_key(self, chat_id):
#         """Хэш-таблица с сообщениями."""
#         return f'user:list:{chat_id}'

#     def users_set(self):
#         """Список юзеров, использующих бота."""
#         return 'users:set'

#     def user_info(self, chat_id):
#         """Хэш-информация о юзере."""
#         return f'user:info:{chat_id}'


pool = aioredis.create_pool("redis://localhost", encoding='utf-8')
redis = aioredis.Redis(pool_or_conn=pool)
print('data', type(redis))

us = redis.smembers(KeySchema().users_set())
print(us)

def db_add_user(message, state):
    """
    Заполнение таблицы users
    """

    with state.proxy() as data:

        user = User(data['name'], data['birthday'], message.chat.id)
        data_manager.add(user)


data_manager = DataManager('sqlite:///db/sqlite3.db')
data_manager._create_table(User)
data_manager._create_table(ContactsUser)

# us = data_manager.get_by_id(User, 23)
# print(us)
# #data_manager.del_obj(us)

# data_manager.update_state(User, 21, 'birthday', '12-31-23')
# data_manager.update_state(User, 21, 'chat_id', 4555969)
# data_manager.get_by_all(User)
