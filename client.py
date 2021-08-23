import asyncio
import os

from dotenv import load_dotenv

from client_config.client_logic import (contact_exist_check,
                                        contact_messages_check)
from client_config.client_manager import ClientManager
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


async def main():
    await client_manager.on_startup()
    redis = client_manager.redis
    while True:
        await client_manager.clients_activate()
        for user_chat_id, client in client_manager.clients.items():
            client_contacts = await manager.get_client_contacts(user_chat_id)
            await client.start()
            await contact_exist_check(client, redis)
            for contact in client_contacts:
                await contact_messages_check(
                    client=client,
                    contact=contact,
                    user_chat_id=user_chat_id,
                    redis=redis
                )
            await client.stop()
            await asyncio.sleep(1)


if __name__ == '__main__':
    asyncio.run(main())
