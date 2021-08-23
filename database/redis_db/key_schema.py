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

    def contact_messages(self, user_chat_id, contact_username):
        return f'hash:messages:{user_chat_id}:{contact_username}'

    def user_info(self, chat_id):
        """Хэш-информация о юзере."""
        return f'user:info:{chat_id}'

    def check_contact_status(self):
        return 'hash:check_contact_status'

    def check_contact(self):
        return 'list:check_contact'

    def conf_code_by_id(self):
        return 'hash:id_conf_code'

    def code_entered(self):
        return 'set:code_entered'
