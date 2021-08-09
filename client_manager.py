import asyncio
import aioredis
from pyrogram import Client
from sqlalchemy import update
from sql_db.tables import User, Base
from sql_db.data_manager import DataManager

manager = DataManager('sqlite:///test.db', base=Base)
session = manager.session


class ClientManager:
    def __init__(self, api_id, api_hash):
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
        activated_clients = session.query(User).filter(
            User.is_activated == True,
            User.is_active == True
        ).all()
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
        wait_activation = session.query(User).filter(User.is_activated == False).all()
        for user in wait_activation:
            user_chat_id = user.chat_id
            phone_number = user.phone_number
            client = Client(
                f'{user_chat_id}',
                api_id=self.api_id,
                api_hash=self.api_hash,
                phone_number=phone_number,
                phone_code_handler=await self.get_confirmation_code(client_id=user_chat_id)
            )
            await client.start()
            await client.stop()
            session.execute(
                update(User).
                where(User.chat_id == user_chat_id).
                values(is_activated=True)
            )
            session.commit()
            await self.add_client(f'{user_chat_id}', client)

    async def get_confirmation_code(self, client_id):
        async def _stab():
            while True:
                code = await self.redis.hget(
                    'hash:id_conf_code',
                    client_id
                )
                if code:
                    break
                await asyncio.sleep(1)
            return code

        return _stab
