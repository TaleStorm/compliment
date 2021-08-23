import asyncio
import os
from datetime import datetime as dt
from random import randint

from dotenv import load_dotenv
from pyrogram.errors.exceptions.bad_request_400 import UsernameNotOccupied

from bot_config import constants
from client_config.client_manager import ClientManager
from database.redis_db.key_schema import KeySchema
from database.sql_db.data_manager import DataManager

load_dotenv()

manager = DataManager('sqlite+aiosqlite:///test.db')

API_ID = os.environ.get('API_ID')
API_HASH = os.environ.get('API_HASH')

client_manager = ClientManager(
    api_id=API_ID,
    api_hash=API_HASH,
    data_manager=manager
)


async def set_messages(table, redis, time_now=None):
    """
    Создает список сообщений на день с временем отправки.
    """
    if time_now is None:
        time_now = dt.now().time()
    for day_part in constants.DAY_PARTS:
        hour_start = day_part['hour_start']
        hour_end = day_part['hour_end']
        if hour_end < time_now:
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


async def birthday_check(contact, date_today, manager=manager):
    """Проверяет наступление ДР пользователя и отправляет поздравление."""
    contact_username = contact.contact_username
    contact_birthday_date = contact.birthday[0:5]
    congratulations = contact.birthday_congrats
    date_today_str = date_today.strftime('%d-%m')
    is_birthday = date_today_str == contact_birthday_date
    if (is_birthday and
            not congratulations):
        await manager.set_contact_congrats_status(
            contact_username=contact_username,
            status=True
        )
        return True
    elif congratulations and not is_birthday:
        await manager.set_contact_congrats_status(
            contact_username=contact_username,
            status=False
        )
    return False


async def contact_messages_check(client, contact, user_chat_id, redis):
    contact_username = contact.contact_username
    table = KeySchema().contact_messages(user_chat_id, contact_username)
    date_today = dt.now()
    time_now = date_today.time()
    messages = await redis.hgetall(table)
    print(messages)
    need_to_congratulate = await birthday_check(contact, date_today)
    if need_to_congratulate:
        await client.send_message(
            chat_id=contact_username,
            text=constants.BIRTHDAY
        )

    if time_now < constants.MORNING['hour_start']:
        await night_mode(messages, redis, table)
        return

    if not messages:
        await set_messages(table, redis)

    time_now_str = time_now.strftime('%H:%M')
    message_now = await redis.hget(table, time_now_str)
    if message_now:
        await client.send_message(f'{contact_username}', message_now)
        await redis.hdel(table, time_now_str)


async def night_mode(messages, redis, table):
    if messages:
        for message in messages.keys():
            await redis.hdel(table, message)
    return await asyncio.sleep(1200)


async def contact_exist_check(client, redis):
    contacts = await redis.smembers(KeySchema().check_contact())
    for contact in contacts:
        try:
            contact_info = await client.get_users(contact)

        except UsernameNotOccupied:
            await redis.hset(
                KeySchema().check_contact_status(),
                contact,
                'False'
            )
        else:
            first_name = contact_info.first_name
            last_name = contact_info.last_name
            username = contact_info.username
            if last_name is None:
                if first_name is None:
                    full_name = username
                else:
                    full_name = first_name
            else:
                full_name = first_name + ' ' + last_name
            await redis.hset(
                KeySchema().check_contact_status(),
                contact,
                full_name
            )

        finally:
            await redis.srem(KeySchema().check_contact(), contact)
