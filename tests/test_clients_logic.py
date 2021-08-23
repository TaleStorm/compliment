import asyncio
import os
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

import aioredis
from pyrogram.errors.exceptions.bad_request_400 import UsernameNotOccupied

from client_config.client_logic import (birthday_check, contact_exist_check, night_mode,
                           set_messages)
from database.redis_db.key_schema import KeySchema
from database.sql_db.data_manager import DataManager
from tests import constants as const


class ClientsLogicTest(IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data_manager = DataManager(
            f'sqlite+aiosqlite:///{const.TESTS_PATH}/{const.TEST_DB_NAME}'
        )
        asyncio.run(cls.data_manager.create_user(
            const.USER_CHAT_ID,
            const.USER_PHONE_NUMBER
        ))
        asyncio.run(cls.data_manager.create_contact(
            const.CONTACT_USERNAME,
            const.CONTACT_BIRTHDAY,
            const.USER_CHAT_ID
        ))
        cls.contact = asyncio.run(cls.data_manager.get_contact(
            const.CONTACT_USERNAME
        ))
        pool = asyncio.run(aioredis.create_pool(
            "redis://localhost",
            encoding='utf-8'
        ))
        cls.redis = aioredis.Redis(pool_or_conn=pool)
        cls.messages_table = KeySchema().contact_messages(
            user_chat_id=const.USER_CHAT_ID,
            contact_username=const.CONTACT_USERNAME
        )

    @classmethod
    def tearDownClass(cls) -> None:
        path_db = os.path.join(const.TESTS_PATH, const.TEST_DB_NAME)
        os.remove(path_db)

    async def test_set_messages(self):
        first_query = await self.redis.hgetall(self.messages_table)
        self.assertFalse(first_query)
        await set_messages(
            self.messages_table,
            self.redis,
            time_now=const.FAKE_TIME
        )
        messages = await self.redis.hgetall(self.messages_table)
        for message in messages:
            await self.redis.hdel(self.messages_table, message)
        self.assertTrue(len(messages) == 4)

    async def test_birthday_check_birthday_wrong_date(self):
        self.assertFalse(await birthday_check(self.contact, const.WRONG_DATE))

    async def test_birthday_check_birthday_date(self):
        self.assertTrue(await birthday_check(
            self.contact,
            const.CONTACT_BIRTHDAY_DT,
            self.data_manager
        )
                        )

    async def test_birthday_check_birthday_date_again(self):
        contact_after_congrats = await self.data_manager.get_contact(
            const.CONTACT_USERNAME
        )
        self.assertFalse(await birthday_check(
            contact_after_congrats,
            const.CONTACT_BIRTHDAY_DT,
            self.data_manager
        )
                         )

    @patch('asyncio.sleep')
    async def test_night_mode(self, mock_sleep):
        messages = await self.redis.hgetall(self.messages_table)
        self.assertFalse(messages)
        await set_messages(
            self.messages_table,
            self.redis,
            time_now=const.FAKE_TIME
        )
        messages = await self.redis.hgetall(self.messages_table)
        self.assertTrue(messages)
        await night_mode(messages, self.redis, self.messages_table)
        messages = await self.redis.hgetall(self.messages_table)
        self.assertFalse(messages)
        mock_sleep.assert_called()

    async def test_01_contact_exist_check(self):
        # contact exist
        mock_client = AsyncMock()
        mock_info = AsyncMock(
            first_name=const.CONTACT_FIRSTNAME,
            last_name=const.CONTACT_LASTNAME
        )
        mock_client.get_users = AsyncMock(return_value=mock_info)
        contact_username = self.contact.contact_username
        await self.redis.sadd(KeySchema().check_contact(), contact_username)
        contact_username = self.contact.contact_username
        await contact_exist_check(mock_client, self.redis)
        full_name = await self.redis.hget(
            KeySchema().check_contact_status(),
            contact_username
        )
        self.assertTrue(
            full_name == f'{const.CONTACT_FIRSTNAME} {const.CONTACT_LASTNAME}'
        )
        await self.redis.hdel(
            KeySchema().check_contact_status(),
            contact_username
        )

        # contact not exist
        mock_client = AsyncMock()
        mock_client.get_users = AsyncMock(side_effect=UsernameNotOccupied)
        await self.redis.sadd(KeySchema().check_contact(), contact_username)
        await contact_exist_check(mock_client, self.redis)
        exist_status = await self.redis.hget(
            KeySchema().check_contact_status(),
            contact_username
        )
        self.assertTrue(exist_status == 'False')
        await self.redis.hdel(
            KeySchema().check_contact_status(),
            contact_username)
