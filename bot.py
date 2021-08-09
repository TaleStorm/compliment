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


from sql_db.tables import User, UserContacts, Base
from sql_db.data_manager import DataManager
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError

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

manager = DataManager('sqlite:///test.db', base=Base)
session = manager.session


class Form(StatesGroup):
    phone_number = State()
    conf_code = State()
    yes_or_not = State()


class FormAddContact(StatesGroup):
    number_input = State()
    birthday = State()


@dp.message_handler(commands='start', state='*')
async def cmd_start(message):
    await Form.phone_number.set()
    await message.reply('Введите номер телефона')


@dp.message_handler(commands='cancel', state=[FormAddContact.number_input, FormAddContact.birthday])
async def cmd_cancel_add_contact(message):
    await Form.yes_or_not.set()
    return await message.reply('Добавление нового контактка отменено')


@dp.message_handler(commands='cancel', state=Form.yes_or_not)
async def cmd_cancel(message, state):
    await state.finish()
    session.execute(
        update(User).
        where(User.chat_id == message.chat.id).
        values(is_active=False)
    )
    session.commit()
    return await message.reply('С этого момента вы не будете получать сообщения')


@dp.message_handler(commands='add', state=Form.yes_or_not)
async def add_contact(message):
    await FormAddContact.number_input.set()
    await message.reply('Отправьте контак из контактной книжки.\n'
                        'У контакта обязательно должен быть указан '
                        'номер телефона.')


@dp.message_handler(content_types=ContentType.CONTACT, state=FormAddContact.number_input)
async def process_contact(message, state):
    async with state.proxy() as data:
        data['contact_id'] = message.contact.user_id
    await FormAddContact.next()
    await message.reply('Теперь введите день рождения данного контакта')


@dp.message_handler(state=FormAddContact.birthday)
async def process_contact_birthday(message, state):
    async with state.proxy() as data:
        contact_id = data['contact_id']
    birthday = await validate_birthday(date=message.text)
    if birthday is None:
        await bot.send_message(
            message.chat.id,
            'Введите дату в правильном формате'
        )
    contact = UserContacts(
        contact_id=contact_id,
        birthday=birthday,
        user_chat_id=message.chat.id
    )
    try:
        session.add(contact)
        session.commit()
    except IntegrityError:
        return await message.reply('Данный контак уже есть в вашем списке')
    else:
        await message.reply('C этого момента дайнный контакт будет получать '
                            'от вас сообщения')
    finally:
        await Form.yes_or_not.set()


@dp.message_handler(state=FormAddContact.number_input)
async def not_contact(message):
    await message.reply('Отправьте именно контак из контактной книжки!')


@dp.message_handler(state=Form.phone_number)
async def process_phone(message, state):
    async with state.proxy() as data:
        data['phone_number'] = message.text
        phone_number = data['phone_number']
        try:
            user = User(
                chat_id=message.chat.id,
                phone_number=phone_number
            )
            session.add(user)
            session.commit()
        except IntegrityError:
            return await message.reply('Вы уже зарегистрировались')
        await message.reply('Теперь введите код подтверждения.')
        await Form.next()


@dp.message_handler(state=Form.conf_code)
async def process_conf_code(message, state, redis):
    async with state.proxy() as data:
        code = message.text[0:-1]
        await redis.hset(
            'hash:id_conf_code', str(message.chat.id), code
        )
    await Form.next()


async def validate_birthday(date):
    try:
        dt.strptime(date, '%d-%m-%y')
    except ValueError:
        return None
    else:
        return date


if __name__ == '__main__':
    dp.middleware.setup(RedisMiddleware())
    executor.start_polling(dp, skip_updates=True)
