import asyncio

import aioredis
from pyrogram import Client


class ClientManager:
    def __init__(self):
        self.clients = {}
        self.redis = None

    async def add_client(self, client_id, client):
        self.clients[client_id] = client

    async def on_startup(self):
        # активирую эту функцию при перезапуске бота
        # она вытакскивает из редиса активные клиенты, активирует их и добавляет в self.clients
        pool = await aioredis.create_pool(
            "redis://localhost",
            encoding='utf-8'
        )
        self.redis = aioredis.Redis(pool_or_conn=pool)
        # тут мини костыль с присваеванием клиента редиса классу
        activated_clients_id = await self.redis.smembers('list:activated')
        # ^тут список чат айди активных юзеров
        for client_id in activated_clients_id:

            client_info = await self.redis.hgetall(
                f'hash:activated:{client_id}'
            )
            # ^тут по их чат айди вытаскаваются api_id и api_hash
            api_id = client_info['api_id']
            api_hash = client_info['api_hash']
            client = Client(
                f'{client_id}',
                api_id=api_id,
                api_hash=api_hash
            )
            await self.add_client(
                client_id=client_id,
                client=client
            )

    async def clients_activate(self):
        wait_activation = await self.redis.smembers('list:wait_activation')
        # ^в эту таблицу бот добавляет новых пользователей, которым надо активировать клиент
        for client_id in wait_activation:
            # пробегаемся по этим клиентам и активируем их
            user_info = await self.redis.hgetall(f'hash:wait_activation:{client_id}')
            api_id = user_info['api_id']
            api_hash = user_info['api_hash']
            phone_number = user_info['phone_number']
            client = Client(
                f'{client_id}',
                api_id=int(api_id),
                api_hash=api_hash,
                phone_number=phone_number,
                phone_code_handler=await get_confirmation_code(redis=self.redis, client_id=client_id)
                # вот тут скорее всего всё будет лочиться, пока юзер не введет код
            )
            await client.start()
            await client.stop()
            # запускам/выключаем, что бы потом можно было запускать их только по api_id api_hash
            await self.delete_wait_activation(client_id=client_id)
            await self.redis.hmset_dict(
                f'hash:activated:{client_id}',
                {
                    'api_id': api_id,
                    'api_hash': api_hash
                }
            )
            await self.redis.sadd('list:activated', client_id)
            await self.add_client(f'{client_id}', client)

    async def delete_wait_activation(self, client_id):
        await self.redis.srem('list:wait_activation', client_id)
        await self.redis.hdel(
            f'hash:wait_activation:{client_id}',
            ['api_id', 'api_hash', 'phone_number']
        )
        await self.redis.hdel(
            'hash:id_conf_code',
            client_id
        )


client_manager = ClientManager()


async def main():
    await client_manager.on_startup()
    while True:
        # цикл сначала чекает, не появилось ли новых клиентов и затем начинает рассылку сообщений
        await client_manager.clients_activate()
        for client_id, client in client_manager.clients.items():
            await client.start()
            # тут будет логика отправки сообщение по контактам с логикой из предыдущего бота внутри
            await client.stop()


async def get_confirmation_code(redis, client_id):
    # это как раз та блокирующая функция
    # после того, как произойдет активация клиента эта функция будет ждать пока человек отправит код боту
    # а бот добавит его в редис
    async def _stab():
        while True:
            code = await redis.hget(
                'hash:id_conf_code',
                client_id
            )
            if code:
                break
        return code
    return _stab

if __name__ == '__main__':
    asyncio.run(main())
