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
        """Список сообщений, которые надо отправить контакту."""
        return f'hash:messages:{user_chat_id}:{contact_username}'

    def user_info(self, chat_id):
        """Хэш-информация о юзере."""
        return f'user:info:{chat_id}'

    def check_contact_status(self):
        """Хэш-таблица с результатом проверки, существует ли юзер."""
        return 'hash:check_contact_status'

    def check_contact(self):
        """Список имен пользователей, существование которых надо проверить."""
        return 'list:check_contact'

    def conf_code_by_id(self):
        """Список id пользователей с их кодом активации."""
        return 'hash:id_conf_code'

    def code_entered(self):
        """Список пользователей, которые уже ввели код активации."""
        return 'set:code_entered'
