import asyncio
import os
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

import aioredis
import pyrogram
from pyrogram.errors.exceptions.not_acceptable_406 import PhoneNumberInvalid

from client_config.client_manager import ClientManager
from database.sql_db.data_manager import DataManager
from tests import constants as const


class ClientManagerTest(IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data_manager = DataManager(
            f'sqlite+aiosqlite:///{const.TESTS_PATH}/{const.TEST_DB_NAME}'
        )
        asyncio.run(cls.data_manager.create_user(
            const.USER_CHAT_ID,
            const.USER_PHONE_NUMBER
        ))
        cls.user = asyncio.run(cls.data_manager.get_user(const.USER_CHAT_ID))
        pool = asyncio.run(aioredis.create_pool(
            "redis://localhost",
            encoding='utf-8'
        ))
        cls.redis = aioredis.Redis(pool_or_conn=pool)

    @classmethod
    def tearDownClass(cls) -> None:
        path_db = os.path.join(const.TESTS_PATH, const.TEST_DB_NAME)
        os.remove(path_db)

    @patch('pyrogram.client.Client')
    @patch.object(pyrogram.client.Client, 'start', new_callable=AsyncMock)
    @patch.object(pyrogram.client.Client, 'stop', new_callable=AsyncMock)
    async def test_client_activate(self, mock_stop, mock_start, mock_client):

        client_manager = ClientManager('1234', '1234', self.data_manager)
        await client_manager.on_startup()
        self.assertFalse(client_manager.clients)
        await client_manager.activate_client(self.user)
        for client_id, client in client_manager.clients.items():
            self.assertTrue(client_id == const.USER_CHAT_ID)
            self.assertTrue(client.phone_number == const.USER_PHONE_NUMBER)

        mock_start.side_effect = PhoneNumberInvalid
        await client_manager.activate_client(self.user)
        status = await self.redis.hget(
            'hash:phone_validation',
            const.USER_CHAT_ID
        )
        self.assertTrue(status == 'False')
        await self.redis.hdel(
            'hash:phone_validation',
            const.USER_CHAT_ID
        )
