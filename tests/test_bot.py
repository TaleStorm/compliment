import os
import asyncio
from unittest import IsolatedAsyncioTestCase
from sql_db.data_manager import DataManager

from tests import constants as const


class BotTest(IsolatedAsyncioTestCase):
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
        cls.message = {
            'chat': {
                'id': const.USER_CHAT_ID
            }
        }

    @classmethod
    def tearDownClass(cls) -> None:
        path_db = os.path.join(const.TESTS_PATH, const.TEST_DB_NAME)
        os.remove(path_db)

