import os
import asyncio
from unittest.mock import patch, AsyncMock
import pyrogram
from sql_db.data_manager import DataManager
from tests import constants as const
from unittest import IsolatedAsyncioTestCase
from client_manager import ClientManager

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

    @classmethod
    def tearDownClass(cls) -> None:
        path_db = os.path.join(const.TESTS_PATH, const.TEST_DB_NAME)
        os.remove(path_db)

    @patch('pyrogram.client.Client')
    @patch.object(pyrogram.client.Client, 'start', new_callable=AsyncMock)
    @patch.object(pyrogram.client.Client, 'stop', new_callable=AsyncMock)
    async def test_client_activate(self, mock_stop, mock_start, mock_client):
        client_manager = ClientManager('1234', '1234', self.data_manager)
        mock_client.start.return_value = None
        await client_manager.activate_client(self.user)
