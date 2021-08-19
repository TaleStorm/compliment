import asyncio

import aioredis
from pyrogram import Client

from sql_db.data_manager import DataManager

manager = DataManager('sqlite+aiosqlite:///test.db')


class ClientManager:
    def __init__(self, api_id, api_hash, manager=None):
        self.api_id = api_id
        self.api_hash = api_hash
        self.clients = {}
        self.redis = None

    async def add_client(self, client_id, client):
        self.clients[client_id] = client

    async def on_startup(self):
        pool = await aioredis.create_pool(
            "redis://localhost",
            encoding='utf-8'
        )
        self.redis = aioredis.Redis(pool_or_conn=pool)
        activated_clients = await manager.get_active_users()
        for user in activated_clients:
            user_chat_id = user.chat_id
            client = Client(
                f'{user_chat_id}',
                api_id=self.api_id,
                api_hash=self.api_hash
            )
            await self.add_client(
                client_id=user_chat_id,
                client=client
            )
        print(self.clients)

    async def clients_activate(self):
        wait_activation = await manager.get_wait_activation_users()
        tasks = []
        for user in wait_activation:
            tasks.append(asyncio.create_task(self.activate_client(user)))

        if tasks:
            await asyncio.wait(tasks)

    async def activate_client(self, user):
        user_chat_id = user.chat_id
        phone_number = user.phone_number
        client = Client(
            f'{user_chat_id}',
            api_id=self.api_id,
            api_hash=self.api_hash,
            phone_number=phone_number,
            phone_code_handler=await self.get_confirmation_code(
                client_id=user_chat_id
            )
        )
        await client.start()
        await client.stop()
        await manager.set_client_activated_status(user_chat_id, True)
        await self.add_client(f'{user_chat_id}', client)

    async def get_confirmation_code(self, client_id):
        async def _stab():
            while True:
                wrong_code = await self.redis.smembers('set:code_entered')
                if client_id in wrong_code:
                    await asyncio.sleep(0)
                    continue
                code = await self.redis.hget(
                    'hash:id_conf_code',
                    client_id
                )
                if code:
                    await self.redis.hdel('hash:id_conf_code', client_id)
                    await self.redis.sadd('set:code_entered', client_id)
                    break
                await asyncio.sleep(1)
            return code

        return _stab
