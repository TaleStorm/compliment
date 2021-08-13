from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
import asyncio
from sqlalchemy.future import select

from sql_db.tables import Base, UserContacts, User
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
        async with self.async_session() as session:
            async with session.begin():
                query = select(User).where(
                    User.is_active == True,
                    User.is_activated == True
                )
                result = await session.execute(query)
                return result.scalars().all()

    async def get_wait_activation_users(self):
        async with self.async_session() as session:
            async with session.begin():
                query = select(User).where(
                    User.is_activated == False
                )
                result = await session.execute(query)
                return result.scalars().all()

    async def get_user(self, user_chat_id):
        async with self.async_session() as session:
            async with session.begin():
                query = select(User).where(User.chat_id == user_chat_id)
                result = await session.execute(query)
                return result.scalars().all()

    async def get_client_contacts(self, user_chat_id):
        async with self.async_session() as session:
            async with session.begin():
                query = select(UserContacts).where(
                    UserContacts.user_chat_id == user_chat_id
                )
                result = await session.execute(query)
                return result.scalars().all()

    async def create_user(self, user_chat_id, user_phone_number):
        async with self.async_session() as session:
            async with session.begin():
                user = User(
                    chat_id=user_chat_id,
                    phone_number=user_phone_number
                )
                session.add(user)
                await session.commit()

    async def create_contact(self, contact_username, contact_birthday, user_chat_id):
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
        async with self.async_session() as session:
            async with session.begin():
                query = select(User).where(User.chat_id == user_chat_id)
                result = await session.execute(query)
                user = result.scalars().first()
                user.is_activated = status
                await session.commit()


    async def set_user_active_status(self, user_chat_id, status: bool):
        async with self.async_session() as session:
            async with session.begin():
                query = select(User).where(User.chat_id == str(user_chat_id))
                result = await session.execute(query)
                user = result.scalars().first()
                user.is_active = status
                await session.commit()

    async def set_contact_congrats_status(self, contact_username: str, status: bool):
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