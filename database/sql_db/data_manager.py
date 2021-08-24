import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from database.sql_db.tables import Base, User, UserContacts


class DataManager:
    def __init__(self, str_connection):
        self.engine = create_async_engine(str_connection)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._create_table())
        self.async_session = sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

    async def _create_table(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_active_users(self):
        """Возвращает список активных пользователей."""
        async with self.async_session() as session:
            async with session.begin():
                query = select(User).where(
                    User.is_active == True,
                    User.is_activated == True
                )
                result = await session.execute(query)
                return result.scalars().all()

    async def get_wait_activation_users(self):
        """Возвращает список аккаунтов, которые надо активировать."""
        async with self.async_session() as session:
            async with session.begin():
                query = select(User).where(
                    User.is_activated == False
                )
                result = await session.execute(query)
                return result.scalars().all()

    async def get_user(self, user_chat_id):
        """Возвращает объект юзера по chat_id."""
        async with self.async_session() as session:
            async with session.begin():
                query = select(User).where(User.chat_id == user_chat_id)
                result = await session.execute(query)
                return result.scalars().first()

    async def get_contact(self, contact_username):
        """Возвращает объект контакта по его username."""
        async with self.async_session() as session:
            async with session.begin():
                query = select(UserContacts).where(
                    UserContacts.contact_username == contact_username)
                result = await session.execute(query)
                return result.scalars().first()

    async def get_client_contacts(self, user_chat_id):
        """Возвращает список контактов клиента по его chat_id."""
        async with self.async_session() as session:
            async with session.begin():
                query = select(UserContacts).where(
                    UserContacts.user_chat_id == user_chat_id
                )
                result = await session.execute(query)
                return result.scalars().all()

    async def create_user(self, user_chat_id, user_phone_number):
        """Создает объект юзера в БД."""
        async with self.async_session() as session:
            async with session.begin():
                user = User(
                    chat_id=user_chat_id,
                    phone_number=user_phone_number
                )
                session.add(user)
                await session.commit()

    async def create_contact(self,
                             contact_username,
                             contact_birthday,
                             user_chat_id):
        """Создает объект контакта в БД."""
        contact = UserContacts(
            contact_username=contact_username,
            birthday=contact_birthday,
            user_chat_id=user_chat_id
        )
        async with self.async_session() as session:
            async with session.begin():
                session.add(contact)
                await session.commit()

    async def set_client_activated_status(self, user_chat_id, status: bool):
        """Изменяет статус активации клиента пользователя."""
        async with self.async_session() as session:
            async with session.begin():
                query = select(User).where(User.chat_id == user_chat_id)
                result = await session.execute(query)
                user = result.scalars().first()
                user.is_activated = status
                await session.commit()

    async def set_user_active_status(self, user_chat_id, status: bool):
        """Изменяет статус пользователя (активен/неактивен)."""
        async with self.async_session() as session:
            async with session.begin():
                query = select(User).where(User.chat_id == str(user_chat_id))
                result = await session.execute(query)
                user = result.scalars().first()
                user.is_active = status
                await session.commit()

    async def set_contact_congrats_status(self,
                                          contact_username: str,
                                          status: bool
                                          ):
        """Изменяет статус поздравления контакта."""
        async with self.async_session() as session:
            async with session.begin():
                query = select(UserContacts).where(
                    UserContacts.contact_username == contact_username
                )
                result = await session.execute(query)
                user_contact = result.scalars().first()
                user_contact.birthday_congrats = status
                await session.commit()
        return True

    async def update_user_phone_number(self, chat_id, phone_number):
        """Иземеняет номер телефона пользователя."""
        async with self.async_session() as session:
            async with session.begin():
                query = select(User).where(
                    User.chat_id == chat_id
                )
                result = await session.execute(query)
                user = result.scalars().first()
                user.phone_number = phone_number
                await session.commit()

    async def delete_contact(self, contact_username, user_chat_id):
        """Удаляет контакт."""
        async with self.async_session() as session:
            async with session.begin():
                query = select(UserContacts).where(
                    UserContacts.contact_username == contact_username,
                    UserContacts.user_chat_id == user_chat_id
                )
                result = await session.execute(query)
                contact = result.scalars().first()
                await session.delete(contact)
                await session.commit()

    async def delete_user(self, user_chat_id):
        """Удаляет пользователя."""
        async with self.async_session() as session:
            async with session.begin():
                query = select(User).where(
                    User.chat_id == user_chat_id
                )
                result = await session.execute(query)
                user = result.scalars().first()
                await session.delete(user)
                await session.commit()
