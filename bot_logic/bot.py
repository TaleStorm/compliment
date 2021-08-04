import asyncio
import os
from datetime import datetime as dt
from random import randint

import aioredis
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware
from aiogram.utils import executor
from dotenv import load_dotenv
from loguru import logger
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

import constants
from redis_db.key_schema import KeySchema

logger.add('logs.json', format='{time} {level} {message}',
           level='INFO', rotation='50 KB', compression='zip', serialize=True)

load_dotenv()


class RedisMiddleware(LifetimeControllerMiddleware):
    def __init__(self):
        super().__init__()

    async def pre_process(self, obj, data, *args):
        pool = await aioredis.create_pool(
            "redis://localhost",
            encoding='utf-8'
        )
        data['redis'] = aioredis.Redis(pool_or_conn=pool)


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


async def on_startup(dispatcher):
    """
    Рассылает сообщение о перезапуске бота всем юзерам.
    """
    pool = await aioredis.create_pool(
        'redis://localhost', encoding='utf-8')
    redis = aioredis.Redis(pool_or_conn=pool)
    members = await redis.smembers(KeySchema().users_set())
    for member in members:
        await dispatcher.bot.send_message(
            chat_id=int(member),
            text='Привет.\n'
                 'Мы перезапускали бота.\n'
                 'Если хочешь продолжить получать сообщения - '
                 'введи /continue'
        )
    pool.close()
    await pool.wait_closed()


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
async def cmd_continue(message, state, redis):
    """Возвращает в основной цикл после перезапуска бота."""
    async with state.proxy() as data:
        if data.get('answer') is not None:
            await message.reply('Кажется ты уже активировал бота')
            return
    members = await redis.smembers(KeySchema().users_set())
    chat_id = message.chat.id

    if str(chat_id) in members:
        info = await redis.hgetall(KeySchema().user_info(chat_id))
        name = info.get('name')
        birthday = info.get('birthday')
        birthday_validate = await validate_birthday(birthday)
        if (name is None or birthday is None
                or birthday is None):
            await message.reply('Что-то случилось с данными. '
                                'Заполните их заново. '
                                'Введите имя')
            await Form.name.set()
            await process_name()
        async with state.proxy() as data:
            data['name'] = name
            data['birthday'] = birthday_validate
            data['congratulations'] = False
            data['answer'] = True
        await Form.yes_or_not.set()
        await message.reply('Введи любое сообщение что бы начать!')


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
                        "Если захочешь сново получать сообщения - "
                        "введи /start")


@dp.message_handler(state=Form.name)
async def process_name(message, state, redis):
    """
    Установка имени пользователя.
    """
    async with state.proxy() as data:
        data['name'] = message.text
    await redis.hset(
        KeySchema().user_info(message.chat.id),
        'name', message.text
    )

    await Form.next()
    await message.reply('Введите дату рождения в формате '
                        'ДД-ММ-ГГ')


@dp.message_handler(state=Form.birthday)
async def process_birthday(message, state, redis):
    """
    Установка дня рождения.
    """

    birthday = await validate_birthday(date=message.text)
    if birthday is None:
        await bot.send_message(
            message.chat.id,
            'Введите дату в правильном формате'
        )
        return
    async with state.proxy() as data:
        data['birthday'] = birthday
        data['congratulations'] = False
    await redis.hset(
        KeySchema().user_info(message.chat.id),
        'birthday', message.text
    )
    await Form.next()
    await message.reply('Введи любое сообщение что бы начать!')


@dp.message_handler(state=Form.yes_or_not)
async def message_loop(message, state, redis):
    """
    Основной цикл бота.
    """
    await message.reply('С этого момента ты будешь получать сообщения!')

    await redis.sadd('users:set', message.chat.id)

    async with state.proxy() as data:
        data['answer'] = True

    current_state = await state.get_state()

    while current_state is not None:
        chat_id = message.chat.id
        table = KeySchema().user_messages_key(chat_id=chat_id)
        messages = await redis.hgetall(table)
        async with state.proxy() as data:
            if data.get('answer') is None:
                await reset_user(redis, message, messages, table)
                break
        current_state = await state.get_state()
        date_today = dt.now()
        time_now = date_today.time()
        await birthday_check(
            state=state,
            chat_id=chat_id,
            date_today=date_today
        )
        if time_now < constants.MORNING['hour_start']:
            await night_mode(messages, redis, table)
            continue

        if not messages:
            await set_messages(table, redis)
        time_now_str = time_now.strftime('%H:%M')
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


async def birthday_check(state, chat_id, date_today):
    """Проверяет наступление ДР пользователя и отправляет поздравление."""
    async with state.proxy() as data:
        birthday = data['birthday']
        congratulations = data['congratulations']
        date_today_str = date_today.strftime('%d-%m')
        birthday_str = birthday.strftime('%d-%m')
        if (date_today_str == birthday_str and
                not congratulations):
            data['congratulations'] = True
            await send_with_typing(
                bot_client=bot,
                chat_id=chat_id,
                message=constants.BIRTHDAY
            )
        elif congratulations:
            data['congratulations'] = False


async def night_mode(messages, redis, table):
    if messages:
        for message in messages.keys():
            await redis.hdel(table, message)
    await asyncio.sleep(1200)


async def reset_user(redis, message, messages, table):
    await redis.srem('users:set', message.chat.id)
    for message in messages.keys():
        await redis.hdel(table, message)


async def validate_birthday(date):
    try:
        birthday = dt.strptime(date, '%d-%m-%y')
    except ValueError:
        return None
    else:
        return birthday
