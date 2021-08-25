import asyncio

from dotenv import load_dotenv

from client_config.client_logic import (contact_exist_check,
                                        contact_messages_check)
from client_config.client_logic import client_manager, manager

load_dotenv()


async def main():
    await client_manager.on_startup()
    redis = client_manager.redis
    while True:
        await client_manager.clients_activate()
        for user_chat_id, client in client_manager.clients.items():
            client_contacts = await manager.get_client_contacts(user_chat_id)
            await contact_exist_check(client, redis)
            for contact in client_contacts:
                await contact_messages_check(
                    client=client,
                    contact=contact,
                    user_chat_id=user_chat_id,
                    redis=redis
                )
            try:
                await client.stop()
            except ConnectionError:
                pass
            await asyncio.sleep(1)


if __name__ == '__main__':
    asyncio.run(main())
