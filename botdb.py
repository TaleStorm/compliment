
import aioredis
import asyncio

from db.example import User, ContactsUser
from db.data_manager import DataManager
from main import KeySchema


dm = DataManager('sqlite:///db/sqlite3.db')
dm._create_table(User)
dm._create_table(ContactsUser)

async def main_r():
    pool = await aioredis.create_pool('redis://localhost', encoding='utf-8')
    redis = aioredis.Redis(pool_or_conn=pool)

    ch_id_users = await redis.smembers(KeySchema().users_set())

    for ch_id in ch_id_users:

        user = await redis.hgetall(KeySchema().user_info(ch_id))

        mes = await redis.hgetall(KeySchema().user_messages_key(ch_id))

        if not ch_id in ch_id_users:
            dm.add(User(user['name'], ch_id))

    pool.close()
    await pool.wait_closed()

asyncio.run(main_r())
