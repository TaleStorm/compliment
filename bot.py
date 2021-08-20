import asyncio
import os
from datetime import datetime as dt

import aioredis
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from dotenv import load_dotenv
from loguru import logger
from sqlalchemy.exc import IntegrityError

from sql_db.data_manager import DataManager

logger.add(
    'logs.json', format='{time} {level} {message}',
    level='INFO', rotation='50 KB', compression='zip', serialize=True
)

load_dotenv()

manager = DataManager('sqlite+aiosqlite:///test.db')


class RedisMiddleware(LifetimeControllerMiddleware):
    def __init__(self):
        super().__init__()

    async def pre_process(self, obj, data, *args):
        pool = await aioredis.create_pool(
            "redis://localhost",
            encoding='utf-8'
        )
        data['redis'] = aioredis.Redis(pool_or_conn=pool)
        data['async_session'] = manager.async_session


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

manager = DataManager('sqlite+aiosqlite:///test.db')
async_session = manager.async_session


async def on_startup(dispatcher):
    active_users = await manager.get_active_users()
    for user in active_users:
        chat_id = user.chat_id
        await dispatcher.bot.send_message(
            chat_id=chat_id,
            text='Мы перезапустили бота.\n'
                 'Что бы сново получить доступ к '
                 'его функционалу введите /rerun'
        )


class Form(StatesGroup):
    phone_number = State()
    conf_code = State()
    activated = State()


class FormAddContact(StatesGroup):
    username_input = State()
    username_confirm = State()
    birthday = State()


class FormDeleteContact(StatesGroup):
    whom_delete = State()
    delete_confirm = State()


@dp.message_handler(commands='start', state='*')
async def cmd_start(message):
    user = await manager.get_user(message.chat.id)
    if user:
        if user.is_active == False:
            await manager.set_user_active_status(
                message.chat.id,
                True
            )
            await Form.activated.set()
            message_reply = 'С возвращением!\n\n'
            contacts = await contacts_list(message.chat.id)
            if contacts is not None:
                message_reply += contacts
            return await message.reply(message_reply)
        return await message.reply('Вы уже зарегистрировались')
    await Form.phone_number.set()
    await message.reply('Введите номер телефона')


@dp.message_handler(commands='rerun', state='*')
async def cmd_rerun(message):
    user = await manager.get_user(message.chat.id)
    if user is None:
        return await message.reply('Вы еще не зарегистрировались.\n'
                                   'Введите команду /start, что бы '
                                   'начать регистрацию')
    await Form.activated.set()
    await message.reply('Теперь вы сново можете использовать '
                        'весь функционал бота')


@dp.message_handler(commands='contacts', state=Form.activated)
async def cmd_contacts(message):
    message_contacts = await contacts_list(message.chat.id)
    if message_contacts is None:
        return await message.reply('Вы еще не добавили ни один контакт.\n'
                                   'Что бы добавить контакт введите /add')
    await message.reply(message_contacts)


@dp.message_handler(
    commands='cancel',
    state=[FormDeleteContact.whom_delete, FormDeleteContact.delete_confirm]
)
async def cmd_cancel_delete_contact(message):
    await Form.activated.set()
    return await message.reply(
        'Удаление контакта отменено',
        reply_markup=ReplyKeyboardRemove()
    )


@dp.message_handler(
    commands='cancel',
    state=[FormAddContact.username_input, FormAddContact.birthday]
)
async def cmd_cancel_add_contact(message):
    await Form.activated.set()
    return await message.reply('Добавление нового контактка отменено')


@dp.message_handler(commands='delete', state=Form.activated)
async def cmd_delete_contact(message):
    reply_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    user_contacts = await manager.get_client_contacts(message.chat.id)
    for contact in user_contacts:
        username = f'@{contact.contact_username}'
        reply_keyboard.add(username)
    await message.reply(
        'Выберите пользователя из списка добавленных контактов.\n'
        'Пользователь больше не будет получать от вас сообщения',
        reply_markup=reply_keyboard
    )
    await FormDeleteContact.whom_delete.set()


@dp.message_handler(state=FormDeleteContact.whom_delete)
async def delete_contact_whom(message, state):
    contact_username = message.text[1::]
    user_contact = await manager.get_contact(contact_username)
    if user_contact is None:
        return await message.reply('Воспользуйтесь клавиатурой для выбора '
                                   'контакта')
    async with state.proxy() as data:
        data['contact_delete_username'] = contact_username
    reply_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    button_yes = 'Да'
    button_no = 'Нет'
    reply_keyboard.add(button_yes, button_no)
    await message.reply(
        f'Вы действительно хотите удалить '
        f'пользователя {message.text} из списка?',
        reply_markup=reply_keyboard
    )
    await FormDeleteContact.next()


@dp.message_handler(state=FormDeleteContact.delete_confirm)
async def delete_confirm(message, state):
    if message.text == 'Да':
        async with state.proxy() as data:
            contact_username = data['contact_delete_username']
        await manager.delete_contact(contact_username)
        await Form.activated.set()
        return await message.reply(
            'Контакт успешно удален',
            reply_markup=ReplyKeyboardRemove()
        )
    elif message.text == 'Нет':
        await message.reply(
            'Удаление контакта отменено',
            reply_markup=ReplyKeyboardRemove()
        )
        return await Form.activated.set()
    await message.reply('Воспользуйтесь клавиатурой')


@dp.message_handler(commands='cancel', state=Form.activated)
async def cmd_cancel(message, state):
    await state.finish()
    await manager.set_user_active_status(message.chat.id, False)
    return await message.reply('С этого момента вы не '
                               'будете получать сообщения')


@dp.message_handler(commands='add', state=Form.activated)
async def add_contact(message):
    await FormAddContact.username_input.set()
    await message.reply('Отправьте имя пользователя в формате '
                        '"@username"')


@dp.message_handler(state=FormAddContact.username_input)
async def process_contact(message, state, redis):
    if message.text[0] != '@':

        return await message.reply('Введите имя пользователя в '
                                   'правильном формате')
    await redis.sadd('list:check_contact', message.text[1::])
    while True:
        status_or_fullname = await redis.hget(
            'hash:check_contact_status', message.text[1::]
        )
        if status_or_fullname:
            if status_or_fullname == 'False':
                return await message.reply('Данного контакта не существует')
            async with state.proxy() as data:
                data['contact_username'] = message.text[1::]
            reply_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
            button_yes = 'Да'
            button_no = 'Нет'
            reply_keyboard.add(button_yes, button_no)
            await FormAddContact.next()
            await redis.hdel(
                'hash:check_contact_status', message.text[1::]
            )
            return await message.reply(
                f'Вы действительно хотите добавить контакт '
                f'"{status_or_fullname}"?',
                reply_markup=reply_keyboard
            )


@dp.message_handler(state=FormAddContact.username_confirm)
async def confirm_contact(message):
    if message.text == 'Да':
        await FormAddContact.next()
        return await message.reply(
            'Теперь введите день рождения данного '
            'контакта в формате ДД-ММ-ГГ',
            reply_markup=ReplyKeyboardRemove()
        )
    elif message.text == 'Нет':
        await message.reply(
            'Добавление контакта отменено',
            reply_markup=ReplyKeyboardRemove()
        )
        return await Form.activated.set()
    await message.reply('Воспользуйтесь клавиатурой')


@dp.message_handler(state=FormAddContact.birthday)
async def process_contact_birthday(message, state):
    async with state.proxy() as data:
        contact_username = data['contact_username']
    birthday = await validate_birthday(date=message.text)
    if birthday is None:
        await bot.send_message(
            message.chat.id,
            'Введите дату в правильном формате'
        )
    try:
        await manager.create_contact(
            contact_username=contact_username,
            contact_birthday=birthday,
            user_chat_id=message.chat.id
        )
    except IntegrityError:
        return await message.reply('Данный контак уже есть в вашем списке')
    else:
        await message.reply('C этого момента дайнный контакт будет получать '
                            'от вас сообщения')
    finally:
        await Form.activated.set()


@dp.message_handler(state=FormAddContact.username_input)
async def not_contact(message):
    await message.reply('Отправьте именно контак из контактной книжки!')


@dp.message_handler(state=Form.phone_number)
async def process_phone(message, state):
    async with state.proxy() as data:
        data['phone_number'] = message.text
        phone_number = data['phone_number']
        try:
            await manager.create_user(
                user_chat_id=message.chat.id,
                user_phone_number=phone_number
            )
        except IntegrityError:
            return await message.reply('Вы уже зарегистрировались')
        await message.reply('Теперь введите код подтверждения.')
        await Form.next()


@dp.message_handler(state=Form.conf_code)
async def process_conf_code(message, state, redis):
    code = message.text[0:-1]
    await redis.hset(
        'hash:id_conf_code', str(message.chat.id), code
    )
    while True:
        code_entered = await redis.smembers('set:code_entered')
        if str(message.chat.id) in code_entered:
            await asyncio.sleep(5)
            user = await manager.get_user(message.chat.id)
            if user.is_activated == True:
                await message.reply('Вы успешно зарегистрировались')
                await Form.next()
            else:
                await message.reply('Код неверный.\n'
                                    'Введите код еще раз')
            await redis.srem('set:code_entered', message.chat.id)
            break
        await asyncio.sleep(0)


async def contacts_list(chat_id):
    user_contacts = await manager.get_client_contacts(chat_id)
    if not user_contacts:
        return None
    message_contacts = 'Список ваших контактов:\n'
    counter = 1
    for contact in user_contacts:
        message_contacts += f'{counter}. @{contact.contact_username}\n'
        counter += 1
    return message_contacts


async def validate_birthday(date):
    try:
        dt.strptime(date, '%d-%m-%y')
    except ValueError:
        return None
    else:
        return date


if __name__ == '__main__':
    dp.middleware.setup(RedisMiddleware())
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
