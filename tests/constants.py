import os
from datetime import datetime as dt
from datetime import time

TESTS_PATH = os.path.abspath(os.path.dirname(__file__))
# config
TEST_DB_NAME = 'test_db.db'
# user
USER_CHAT_ID = '12345'
USER_PHONE_NUMBER = '+79102345678'
USER_CONF_CODE = '12345'


# contact
CONTACT_FIRSTNAME = 'User'
CONTACT_LASTNAME = 'Test'
CONTACT_USERNAME = 'TestUser'
CONTACT_BIRTHDAY = '17-01-01'
CONTACT_BIRTHDAY_DT = dt(2001, 1, 17)

WRONG_DATE = dt(2001, 10, 29)

FAKE_TIME = time(8)
