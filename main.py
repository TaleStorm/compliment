import asyncio
import os
from datetime import datetime as dt
from random import randint

import aioredis
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.utils import executor
from dotenv import load_dotenv
from loguru import logger

import constants

logger.add('logs.json', format='{time} {level} {message}',
           level='INFO', rotation='50 KB', compression='zip', serialize=True)

load_dotenv()

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
if TELEGRAM_TOKEN is None:
    logger.exception('Не удалось получить токены')
    raise SystemExit()


try:
    bot = Bot(token=TELEGRAM_TOKEN)
    logger.info('Бот создан')
except Exception as e:
    logger.exception('Ошибка при создании бота: ', e)
    raise SystemExit()
storage = MemoryStorage()
try:
    dp = Dispatcher(bot=bot, storage=storage)
    logger.info('Диспетчер создан')
except Exception as e:
    logger.exception('Ошибка при создании диспетчера: ', e)
    raise SystemExit()


class Form(StatesGroup):
    name = State()
    birthday = State()
    yes_or_not = State()


@dp.message_handler(commands='start')
async def cmd_start(message, state):
    """
    Точка начала диалога.
    """
    if await state.get_state() is not None:
        await cancel_handler(message, state)

    await Form.name.set()

    await message.reply('Привет! Как тебя зовут?')


@dp.message_handler(state='*', commands='continue')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cmd_continue(message, state):
    async with state.proxy() as data:
        if data['answer'] is not None:
            await message.reply('Кажется ты уже активировал бота')
            return


@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message, state):
    """
    Обработчик команды "/cancel". Удаляет все данные по state.
    """
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    async with state.proxy() as data:
        data['answer'] = None
    await message.reply("Пока!\n"
                        "Если захочешь сново получать сообщения - введи /start")


@dp.message_handler(state=Form.name)
async def process_name(message, state):
    """
    Установка имени пользователя.
    """
    async with state.proxy() as data:
        data['name'] = message.text

    await Form.next()
    await message.reply('Введи дату своего рождения в формате "ДД-ММ-ГГ"')


@dp.message_handler(state=Form.birthday)
async def process_birthday(message, state):
    """
    Установка дня рождения.
    """
    try:
        birthday = dt.strptime(message.text, '%d-%m-%y')
    except ValueError:
        await bot.send_message(message.chat.id, 'Введите дату в правильном формате')
        return
    else:
        async with state.proxy() as data:
            data['birthday'] = birthday
            data['congratulations'] = False
    await Form.next()
    await message.reply('Введи любое сообщение что бы начать!')


@dp.message_handler(state=Form.yes_or_not)
async def message_loop(message, state):
    """
    Основной цикл бота.
    """
    await message.reply('С этого момента ты будешь получать сообщения!')

    redis_connection = await aioredis.create_connection("redis://localhost")
    redis = await aioredis.Redis(pool_or_conn=redis_connection)
    await redis.sadd('users:set', message.chat.id)

    async with state.proxy() as data:
        birthday = data['birthday']
        data['answer'] = True

    current_state = await state.get_state()

    while current_state is not None:
        async with state.proxy() as data:
            if data.get('answer') is None:
                await redis.srem('users:set', message.chat.id)
                break
        chat_id = message.chat.id
        current_state = await state.get_state()
        date_today = dt.now()
        time_now = date_today.time()
        table = f'user:list:{chat_id}'
        messages = await redis.hgetall(table, encoding='utf-8')
        async with state.proxy() as data:
            congratulations = data['congratulations']
            date_today_str = date_today.strftime('%d-%m')
            birthday_str = birthday.strftime('%d-%m')
            if date_today_str == birthday_str:
                await happy_birthday(state, congratulations, chat_id)
            elif congratulations:
                data['congratulations'] = False
        if time_now < constants.MORNING['hour_start']:
            if messages:
                for message in messages.keys():
                    await redis.hdel(table, message)
            await asyncio.sleep(1200)
            continue

        if not messages:
            await set_messages(table, redis)
        time_now_str = time_now.strftime('%H:%m')
        message_now = await redis.hget(table, time_now_str)
        if message_now:
            await send_with_typing(
                bot_client=bot,
                chat_id=chat_id,
                message=message_now
            )
            await redis.hdel(table, time_now_str)
        await asyncio.sleep(30)


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
            hour_end.hour
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


async def send_with_typing(bot_client, chat_id, message, typing_time=5):
    """Send message with 'typing...' in set duration."""
    await bot_client.send_chat_action(
        chat_id=chat_id,
        action='typing'
    )
    await asyncio.sleep(typing_time)
    await bot_client.send_message(
        chat_id=chat_id,
        text=message
    )


async def happy_birthday(state, status, chat_id):
    """Отправляет поздравление с ДР, если оно еще не отправлялось."""
    if not status:
        async with state.proxy() as data:
            data['congratulations'] = True
        await send_with_typing(
            bot_client=bot,
            chat_id=chat_id,
            message=constants.BIRTHDAY
        )


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
