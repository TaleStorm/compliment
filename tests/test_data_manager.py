import os
from unittest import IsolatedAsyncioTestCase

from sqlalchemy.future import select

from database.sql_db.data_manager import DataManager
from database.sql_db.tables import User, UserContacts
from tests import constants as const


class DataManagerTest(IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data_manager = DataManager(
            f'sqlite+aiosqlite:///{const.TESTS_PATH}/{const.TEST_DB_NAME}'
        )

    @classmethod
    def tearDownClass(cls) -> None:
        path_db = os.path.join(const.TESTS_PATH, const.TEST_DB_NAME)
        os.remove(path_db)

    async def test_01_create_user(self):
        async with self.data_manager.async_session() as session:
            async with session.begin():
                result = await session.execute(select(User))
                users = result.scalars().all()
                self.assertFalse(users)
                await self.data_manager.create_user(
                    const.USER_CHAT_ID,
                    const.USER_PHONE_NUMBER
                )
                result = await session.execute(select(User))
                users = result.scalars().all()
                self.assertTrue(len(users) == 1)

    async def test_02_get_user(self):
        user = await self.data_manager.get_user(const.USER_CHAT_ID)
        self.assertTrue(user)

    async def test_03_get_wait_activation_users(self):
        wait_activation = await self.data_manager.get_wait_activation_users()
        self.assertTrue(wait_activation)

    async def test_04_set_client_activated_status_true(self):
        user_status = (await self.data_manager.get_user(
            const.USER_CHAT_ID
        )).is_activated
        self.assertFalse(user_status)
        await self.data_manager.set_client_activated_status(
            const.USER_CHAT_ID,
            True
        )
        user_status = (await self.data_manager.get_user(
            const.USER_CHAT_ID
        )).is_activated
        self.assertTrue(user_status)

    async def test_05_get_active_users(self):
        active_users = await self.data_manager.get_active_users()
        self.assertTrue(len(active_users) == 1)

    async def test_06_create_contact(self):
        async with self.data_manager.async_session() as session:
            async with session.begin():
                result = await session.execute(select(UserContacts))
                contacts = result.scalars().all()
                self.assertFalse(contacts)
                await self.data_manager.create_contact(
                    const.CONTACT_USERNAME,
                    const.CONTACT_USERNAME,
                    const.USER_CHAT_ID
                )
                result = await session.execute(select(UserContacts))
                contacts = result.scalars().all()
                self.assertTrue(len(contacts) == 1)

    async def test_07_get_contact(self):
        contact = await self.data_manager.get_contact(const.CONTACT_USERNAME)
        self.assertTrue(contact)

    async def test_08_get_client_contacts(self):
        client_contacts = await self.data_manager.get_client_contacts(
            const.USER_CHAT_ID
        )
        self.assertTrue(len(client_contacts) == 1)

    async def test_09_set_contact_congrats_status(self):
        contact = await self.data_manager.get_contact(const.CONTACT_USERNAME)
        contact_congrats_status = contact.birthday_congrats
        self.assertFalse(contact_congrats_status)
        await self.data_manager.set_contact_congrats_status(
            const.CONTACT_USERNAME,
            True
        )
        contact = await self.data_manager.get_contact(const.CONTACT_USERNAME)
        contact_congrats_status = contact.birthday_congrats
        self.assertTrue(contact_congrats_status)
        await self.data_manager.set_contact_congrats_status(
            const.CONTACT_USERNAME,
            False
        )
        contact = await self.data_manager.get_contact(const.CONTACT_USERNAME)
        contact_congrats_status = contact.birthday_congrats
        self.assertFalse(contact_congrats_status)

    async def test_10_delete_contact(self):
        contacts = await self.data_manager.get_client_contacts(
            const.USER_CHAT_ID
        )
        self.assertTrue(len(contacts) == 1)
        await self.data_manager.delete_contact(
            const.CONTACT_USERNAME,
            const.USER_CHAT_ID
        )
        contacts = await self.data_manager.get_client_contacts(
            const.USER_CHAT_ID
        )
        self.assertFalse(contacts)

    async def test_11_set_user_active_status(self):
        user = await self.data_manager.get_user(const.USER_CHAT_ID)
        user_status = user.is_active
        self.assertTrue(user_status)
        await self.data_manager.set_user_active_status(
            const.USER_CHAT_ID,
            False
        )
        user = await self.data_manager.get_user(const.USER_CHAT_ID)
        user_status = user.is_active
        self.assertFalse(user_status)
