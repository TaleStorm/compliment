import os
from datetime import datetime as dt

import aioredis
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware
from aiogram.types import ContentType
from aiogram.utils import executor
from dotenv import load_dotenv
from loguru import logger


from redis_db.key_schema import KeySchema

logger.add(
    'logs.json', format='{time} {level} {message}',
    level='INFO', rotation='50 KB', compression='zip', serialize=True
)

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
    api_id = State()
    api_hash = State()
    phone_number = State()
    conf_code = State()
    yes_or_not = State()


class FormAddContact(StatesGroup):
    number_input = State()
    birthday = State()


@dp.message_handler(commands='start', state='*')
async def cmd_start(message, state):
    await Form.api_id.set()
    await message.reply('Введите api_id')


@dp.message_handler(commands='add', state=Form.yes_or_not)
async def add_contact(message, state, redis):
    await FormAddContact.number_input.set()
    await message.reply('Отправьте контак из контактной книжки.\n'
                        'У контакта обязательно должен быть указан '
                        'номер телефона.')


@dp.message_handler(content_types=ContentType.CONTACT, state=FormAddContact.number_input)
async def process_contact(message, state, redis):
    phone_number = message.contact.get('phone_number')
    if phone_number is None:
        return await message.reply('У данного контакта не указан номер телефона')
    await redis.sadd(f'list:user_contacts:{message.chat.id}')
    await Form.next()
    await message.reply('Теперь введите день рождения данного контакта')


@dp.message_handler(state=FormAddContact.birthday)
async def process_contact_birthday(message, state, redis):
    birthday = await validate_birthday(date=message.text)
    if birthday is None:
        await bot.send_message(
            message.chat.id,
            'Введите дату в правильном формате'
        )
    await Form.yes_or_not.set()


@dp.message_handler(state=FormAddContact.number_input)
async def not_contact(message):
    await message.reply('Отправьте именно контак из контактной книжки!')


@dp.message_handler(state=Form.api_id)
async def process_api_id(message, state, redis):
    async with state.proxy() as data:
        await redis.hset(
            KeySchema().user_info(message.chat.id),
            'api_id',
            message.text
        )
        data['api_id'] = message.text
    await message.reply('Теперь api_hash')
    await Form.next()


@dp.message_handler(state=Form.api_hash)
async def process_api_hash(message, state, redis):
    async with state.proxy() as data:
        data['api_hash'] = message.text
        await redis.hset(
            KeySchema().user_info(message.chat.id),
            'api_hash',
            message.text
        )
    await message.reply('Теперь номер телефона')
    await Form.next()


@dp.message_handler(state=Form.phone_number)
async def process_phone(message, state, redis):
    async with state.proxy() as data:
        data['phone_number'] = message.text
        api_id = data['api_id']
        api_hash = data['api_hash']
        phone_number = data['phone_number']
        await redis.hmset_dict(
            f'hash:wait_activation:{message.chat.id}',
            {
                'api_id': api_id,
                'api_hash': api_hash,
                'phone_number': phone_number
            }
        )
        await redis.sadd('list:wait_activation', message.chat.id)
        await message.reply('Теперь введите код подтверждения.')
        await Form.next()


@dp.message_handler(state=Form.conf_code)
async def process_conf_code(message, state, redis):
    async with state.proxy() as data:
        data['conf_code'] = message.text
        await redis.hset(
            'hash:id_conf_code', str(message.chat.id), message.text
        )
    await message.reply('Введите любое сообщение')
    await Form.next()


async def validate_birthday(date):
    try:
        birthday = dt.strptime(date, '%d-%m-%y')
    except ValueError:
        return None
    else:
        return birthday


if __name__ == '__main__':
    dp.middleware.setup(RedisMiddleware())
    executor.start_polling(dp, skip_updates=True)
