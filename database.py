from datetime import datetime as dt

import psycopg2


def create_connection():
    conn = psycopg2.connect(dbname='compliment', user='dima',
                            password='2108', host='localhost')
    return conn


def response_parse(response, columns):
    """Is used to make dict from DB response."""
    results = []
    for row in response:
        row_dict = {}
        for i, col in enumerate(columns):
            row_dict[col.name] = row[i]
        results.append(row_dict)
    if len(results) == 1:
        return results[0]
    return results


# user
def get_user(chat_id):
    """Returns dict with User info."""
    conn = create_connection()
    cursor = conn.cursor()
    query = f"""SELECT *
    FROM users
    WHERE chat_id = {chat_id}"""
    cursor.execute(query)
    user = cursor.fetchall()
    columns = list(cursor.description)
    conn.close
    return response_parse(user, columns)


def get_message(day_part_id):
    """Is used to get message for different parts of day."""
    conn = create_connection()
    cursor = conn.cursor()
    query = f"""SELECT * FROM messages
    WHERE day_part_id = {day_part_id}
    """
    cursor.execute(query)
    message = cursor.fetchall()
    column = list(cursor.description)
    return response_parse(message, column)


def update_message_time(chat_id, message_time, message_text):
    """Is used to set time for message sending."""
    conn = create_connection()
    cursor = conn.cursor()
    query = f"""UPDATE users
    SET message_time = '{message_time}',
    message_text = '{message_text}'
    WHERE chat_id = {chat_id}"""
    cursor.execute(query)
    return conn.commit()


def set_last_message(chat_id):
    """Is used to set time of last message."""
    conn = create_connection()
    cursor = conn.cursor()
    time_now = dt.now().time()
    hour = time_now.hour
    minute = time_now.minute
    last_message = f'{hour}:{minute}'
    query = f"""UPDATE users
        SET message_time = NULL,
        message_text = NULL,
        last_message = '{last_message}'
        WHERE chat_id = {chat_id}"""
    cursor.execute(query)
    return conn.commit()


# day parts
def get_day_parts():
    """Return list of day parts with time frames."""
    conn = create_connection()
    cursor = conn.cursor()
    query = """SELECT * FROM day_parts"""
    cursor.execute(query)
    result = cursor.fetchall()
    columns = list(cursor.description)

    return response_parse(result, columns)


# birthday
def get_birthday_status(user_id):
    """Is used to get was user congratulated this year or not."""
    conn = create_connection()
    cursor = conn.cursor()
    query = f"""SELECT * FROM birtday
    WHERE user_id = {user_id}"""
    cursor.execute(query)
    result = cursor.fetchall()
    columns = list(cursor.description())

    return response_parse(result, columns)


def set_congratulate_status(user_id, boolean: bool):
    """Is used to change congratulate status."""
    conn = create_connection()
    cursor = conn.cursor()
    query = f"""UPDATE birthday
    SET
    congratulate = {boolean}
    WHERE
    user_id = {user_id}"""
    cursor.execute(query)
    return conn.commit()
