import os
import asyncio
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch
from sql_db.data_manager import DataManager

from bot import cmd_start, process_phone

from tests import constants as const


class BotTest(IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data_manager = DataManager(
            f'sqlite+aiosqlite:///{const.TESTS_PATH}/{const.TEST_DB_NAME}'
        )

    @classmethod
    def tearDownClass(cls) -> None:
        path_db = os.path.join(const.TESTS_PATH, const.TEST_DB_NAME)
        os.remove(path_db)

    @patch('bot.Form', new_callable=AsyncMock)
    async def test_01_cmd_start(self, mock_form):
        message_mock = AsyncMock('/start')
        message_mock.chat = AsyncMock(id=const.USER_CHAT_ID)
        message_mock.reply = AsyncMock()
        await cmd_start(message_mock)
        message_mock.reply.assert_called_with('Введите номер телефона')

    @patch('bot.Form', new_callable=AsyncMock)
    async def test_02_process_phone(self, mock_form):
        message_mock = AsyncMock(text=const.USER_PHONE_NUMBER)
        message_mock.chat = AsyncMock(id=const.USER_CHAT_ID)
        state_mock = MagicMock()

        await process_phone(message_mock, state_mock, data_manager=self.data_manager)
        message_mock.reply.assert_called_with('Теперь введите код подтверждения.')

    @patch('bot.Form', new_callable=AsyncMock)
    async def test_03_process_phone_already_exist(self, mock_form):
        message_mock = AsyncMock(text=const.USER_PHONE_NUMBER)
        message_mock.chat = AsyncMock(id=const.USER_CHAT_ID)
        state_mock = MagicMock()

        await process_phone(message_mock, state_mock, data_manager=self.data_manager)
        message_mock.reply.assert_called_with('Вы уже зарегистрировались')






