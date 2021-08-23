import asyncio
import os
from unittest import IsolatedAsyncioTestCase
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import aioredis

from bot_config.bot_messages import (add_contact, cmd_contacts, cmd_start,
                                     confirm_contact, process_conf_code,
                                     process_contact, process_phone)
from database.sql_db.data_manager import DataManager
from tests import constants as const


class BotTest(IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data_manager = DataManager(
            f'sqlite+aiosqlite:///{const.TESTS_PATH}/{const.TEST_DB_NAME}'
        )
        pool = asyncio.run(aioredis.create_pool(
            "redis://localhost",
            encoding='utf-8'
        ))
        cls.redis = aioredis.Redis(pool_or_conn=pool)

    @classmethod
    def tearDownClass(cls) -> None:
        path_db = os.path.join(const.TESTS_PATH, const.TEST_DB_NAME)
        os.remove(path_db)

    @patch('bot_config.bot_messages.Form', new_callable=AsyncMock)
    async def test_01_cmd_start(self, mock_form):
        message_mock = AsyncMock('/start')
        message_mock.chat = AsyncMock(id=const.USER_CHAT_ID)
        message_mock.reply = AsyncMock()
        await cmd_start(message_mock)
        message_mock.reply.assert_called_with('Введите номер телефона')

    @patch('bot_config.bot_messages.Form', new_callable=AsyncMock)
    async def test_02_process_phone(self, mock_form):
        message_mock = AsyncMock(text=const.USER_PHONE_NUMBER)
        message_mock.chat = AsyncMock(id=const.USER_CHAT_ID)
        state_mock = MagicMock()
        redis = AsyncMock()

        await process_phone(
            message_mock,
            state_mock,
            data_manager=self.data_manager,
            redis=redis)

        message_mock.reply.assert_called_with(
            'Теперь введите код подтверждения.'
        )

    @patch('bot_config.bot_messages.Form', new_callable=AsyncMock)
    @patch('asyncio.sleep')
    async def test_03_process_conf_code(self, mock_form, mock_sleep):
        message_mock = AsyncMock(text=const.USER_CONF_CODE)
        message_mock.chat = AsyncMock(id=const.USER_CHAT_ID)
        redis = AsyncMock()
        redis.smembers.return_value = [const.USER_CHAT_ID, ]
        await process_conf_code(message_mock, redis, self.data_manager)
        message_mock.reply.assert_called_with('Код неверный.\n'
                                              'Введите код еще раз')

        await self.data_manager.set_client_activated_status(
            const.USER_CHAT_ID,
            True
        )
        await process_conf_code(message_mock, redis, self.data_manager)
        message_mock.reply.assert_called_with('Вы успешно зарегистрировались')

    @patch('bot_config.bot_messages.FormAddContact', new_callable=AsyncMock)
    async def test_04_cmd_add_contact(self, mock_form):
        message_mock = AsyncMock()
        await add_contact(message_mock)
        message_mock.reply.assert_called_with(
            'Отправьте имя пользователя в формате '
            '"@username"'
        )

    @patch('bot_config.bot_messages.FormAddContact', new_callable=AsyncMock)
    async def test_05_process_contact(self, mock_form):
        message_mock = AsyncMock(text=const.CONTACT_USERNAME)
        state_mock = MagicMock()
        redis_mock = AsyncMock()
        await process_contact(message_mock, state_mock, redis_mock)
        message_mock.reply.assert_called_with('Введите имя пользователя в '
                                              'правильном формате')
        contact_fullname = (f'{const.CONTACT_FIRSTNAME} '
                            f'{const.CONTACT_LASTNAME}')
        redis_mock.hget.return_value = contact_fullname
        message_mock.text = f'@{const.CONTACT_USERNAME}'
        await process_contact(message_mock, state_mock, redis_mock)
        message_mock.reply.assert_called_with(
            'Вы действительно хотите добавить контакт '
            f'"{contact_fullname}"?',
            reply_markup=ANY
        )

    @patch('bot_config.bot_messages.FormAddContact', new_callable=AsyncMock)
    @patch('bot_config.bot_messages.Form', new_callable=AsyncMock)
    async def test_06_confirm_contact(self, mock_form, mock_form_2):
        message_mock = AsyncMock(text='Да')
        await confirm_contact(message_mock)
        message_mock.reply.assert_called_with(
            'Теперь введите день рождения данного '
            'контакта в формате ДД-ММ-ГГ',
            reply_markup=ANY
        )

        message_mock = AsyncMock(text='Нет')
        await confirm_contact(message_mock)
        message_mock.reply.assert_called_with('Добавление контакта отменено',
                                              reply_markup=ANY)

        message_mock = AsyncMock(text='Привет')
        await confirm_contact(message_mock)
        message_mock.reply.assert_called_with('Воспользуйтесь клавиатурой')

    async def test_07_cmd_contacts(self):
        message_mock = AsyncMock(text=const.USER_CONF_CODE)
        message_mock.chat = AsyncMock(id=const.USER_CHAT_ID)
        await cmd_contacts(message_mock, self.data_manager)
        message_mock.reply.assert_called_with(
            'Вы еще не добавили ни один контакт.\n'
            'Что бы добавить контакт введите /add'
        )
        await self.data_manager.create_contact(
            const.CONTACT_USERNAME,
            const.CONTACT_BIRTHDAY,
            const.USER_CHAT_ID
        )
        await cmd_contacts(message_mock, self.data_manager)
        message_mock.reply.assert_called_with('Список ваших контактов:\n1. '
                                              f'@{const.CONTACT_USERNAME}\n')
