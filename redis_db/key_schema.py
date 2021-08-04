class KeySchema:
    """
    Возвращает название таблиц для Redis.
    """
    def user_messages_key(self, chat_id):
        """Хэш-таблица с сообщениями."""
        return f'user:list:{chat_id}'

    def users_set(self):
        """Список юзеров, использующих бота."""
        return 'users:set'

    def user_info(self, chat_id):
        """Хэш-информация о юзере."""
        return f'user:info:{chat_id}'
