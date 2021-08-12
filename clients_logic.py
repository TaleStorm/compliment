import asyncio
import os
from datetime import datetime as dt
from random import randint

from dotenv import load_dotenv
from sqlalchemy import update

import constants
from client_manager import ClientManager
from sql_db.data_manager import DataManager
from sql_db.tables import Base, UserContacts

load_dotenv()

manager = DataManager('sqlite:///test.db', base=Base)
session = manager.session

API_ID = os.environ.get('API_ID')
API_HASH = os.environ.get('API_HASH')

client_manager = ClientManager(
    api_id=API_ID,
    api_hash=API_HASH
)


async def main():
    await client_manager.on_startup()
    redis = client_manager.redis
    while True:
        await client_manager.clients_activate()
        for user_chat_id, client in client_manager.clients.items():
            client_contacts = session.query(UserContacts).filter(
                UserContacts.user_chat_id == user_chat_id
            ).all()
            await client.start()
            for contact in client_contacts:
                contact_id = contact.contact_id
                table = f'hash:messages:{user_chat_id}:{contact_id}'
                date_today = dt.now()
                time_now = date_today.time()
                messages = await redis.hget(table)
                print(messages)
                if await birthday_check(contact, date_today):
                    await client.send_message(
                        f'{contact_id}',
                        constants.BIRTHDAY
                    )

                if time_now < constants.MORNING['hour_start']:
                    await night_mode(messages, redis, table)
                    continue

                if not messages:
                    await set_messages(table, redis)

                time_now_str = time_now.strftime('%H:%M')
                message_now = await redis.hget(table, time_now_str)
                if message_now:
                    await client.send_message(f'{contact_id}', message_now)
                    await redis.hdel(table, time_now_str)
            await client.stop()
            await asyncio.sleep(1)


async def set_messages(table, redis):
    """
    Создает список сообщений на день с временем отправки.
    """
    for day_part in constants.DAY_PARTS:
        hour_start = day_part['hour_start']
        hour_end = day_part['hour_end']
        if hour_end < dt.now().time():
            continue
        random_hour = randint(
            hour_start.hour,
            hour_end.hour - 1
        )
        random_minute = randint(
            0,
            60
        )
        if random_minute < 10:
            random_minute = '0' + str(random_minute)
        message_time = f'{random_hour}:{random_minute}'
        message = day_part['message']
        await redis.hset(table, message_time, message)


async def birthday_check(contact, date_today):
    """Проверяет наступление ДР пользователя и отправляет поздравление."""
    contact_id = contact.contact_id
    contact_birthday_date = contact.birthday[0:5]
    congratulations = contact.birthday_congrats
    date_today_str = date_today.strftime('%d-%m')
    if (date_today_str == contact_birthday_date and
            not congratulations):
        session.execute(
            update(UserContacts).
            where(
                UserContacts.contact_id == contact_id
            ).values(birthday_congrats=True)
        )
        session.commit()
        return True
    elif congratulations:
        session.execute(
            update(UserContacts).
            where(UserContacts.contact_id == contact_id).
            values(birthday_congrats=False)
        )
        session.commit()
    return False


async def night_mode(messages, redis, table):
    if messages:
        for message in messages.keys():
            await redis.hdel(table, message)
    await asyncio.sleep(1200)


if __name__ == '__main__':
    asyncio.run(main())
