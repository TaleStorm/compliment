import asyncio
import datetime
import logging
import os
import time
from datetime import datetime as dt
from datetime import timedelta
from random import randint

import aiogram
from aiogram.utils.exceptions import TelegramAPIError
from dotenv import load_dotenv

import constants
from database import (get_birthday_status, get_day_parts, get_message,
                      get_user, set_congratulate_status, set_last_message,
                      update_message_time)

load_dotenv()

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
DB_USERNAME = os.environ.get('DB_USERNAME')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
if TELEGRAM_TOKEN is None or CHAT_ID is None:
    raise SystemExit('Не удалось получить токены')
if DB_USERNAME is None or DB_PASSWORD is None:
    raise SystemExit('Не удалость полчить данные '
                     'для доступа к БД')


async def set_message(chat_id):
    """Is used to set message and random time for sending to user."""
    hour_now = dt.now().time().hour
    day_parts = get_day_parts()
    last_message = get_user(chat_id)['last_message']
    if last_message is not None:
        last_message = last_message.hour

    for part in day_parts:
        hour_start = part['hour_start']
        hour_end = part['hour_end']
        if (hour_now in range(hour_start, hour_end) and
                last_message not in range(hour_start, hour_end)):
            random_hour = randint(
                hour_now,
                hour_end
            )
            random_minute = randint(
                0,
                60
            )
            message_time = datetime.time(
                hour=random_hour,
                minute=random_minute
            )
            message_text = random_message(part['id'])
            update_message_time(
                chat_id=chat_id,
                message_time=message_time,
                message_text=message_text
            )


def random_message(day_part_id):
    messages = get_message(day_part_id)
    if type(messages) is dict:
        return messages['message']
    random_index = randint(0, len(messages))
    return messages[random_index]['message']


async def send_with_typing(bot_client, chat_id, message, typing_time=5):
    """Send message with 'typing...' in set duration."""
    await bot_client.send_chat_action(
        chat_id=chat_id,
        action='typing'
    )
    time.sleep(typing_time)
    await bot_client.send_message(
        chat_id=chat_id,
        text=message
    )


def parse_birthday(birthday):
    """Is used to set current year in birthday for match with current date."""
    day = birthday.day
    month = birthday.month
    year = dt.now().year
    return dt(
        year=year,
        month=month,
        day=day)


async def happy_birthday(bot_client, user_id, chat_id):
    """Is used to send HB congratulations."""
    status = get_birthday_status(user_id)
    if status['congratulate']:
        return None
    await send_with_typing(
        bot_client=bot_client,
        chat_id=chat_id,
        message=constants.BIRTHDAY
    )
    return set_congratulate_status(
        user_id=user_id,
        boolean=True
    )


async def main():
    bot = aiogram.Bot(token=TELEGRAM_TOKEN)
    try:
        await bot.get_me()
    except TelegramAPIError:
        logging.exception('Проблема с созданием бота')
        raise SystemExit('Не удалось создать бота')

    while True:
        try:
            user_info = get_user(CHAT_ID)
            message_time = user_info['message_time']
            date_today = dt.now()
            birthday = parse_birthday(user_info['birthday'])

            if date_today.date() == birthday:
                await happy_birthday(
                    bot_client=bot,
                    chat_id=CHAT_ID,
                    user_id=user_info['id']
                )
            elif date_today.date() == (birthday + timedelta(days=1)):
                set_congratulate_status(
                    user_id=user_info['id'],
                    boolean=False
                )

            if message_time is None:
                await set_message(CHAT_ID)
            elif (message_time.strftime('%H:%M')
                  == date_today.time().strftime('%H:%M')
                    or message_time < date_today.time()):
                message = user_info['message_text']
                await send_with_typing(
                    bot_client=bot,
                    chat_id=CHAT_ID,
                    message=message
                )
                set_last_message(
                    chat_id=CHAT_ID
                )

            time.sleep(constants.REQUEST_RATE)

        except Exception as e:
            logging.exception(e)
            time.sleep(constants.ERROR_REQUEST_RATE)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename='homework.log',
        filemode='w',
        format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
    )
    logging.debug('Бот запущен')
    asyncio.run(main())
