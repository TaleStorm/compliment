from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    birthday = Column(String)
    chat_id = Column(Integer)

    def __init__(self, name, birthday, chat_id):
        self.name = name
        self.birthday = birthday
        self.chat_id = chat_id

    def __repr__(self):
        return f"<User id=> {self.id} имя: {self.name}, день рождения: {self.birthday}, chat_id = {self.chat_id}"


class ContactsUser(Base):
    __tablename__ = 'contacts'
    id = Column(Integer, primary_key=True)
    nickname = Column(String)
    firstname = Column(String)
    lastname = Column(String)
    birthday = Column(String)
    chat_id = Column(Integer)

    def __init__(self, nickname, firstname, chat_id, lastname=None, birthday=None):
        self.nickname = nickname
        self.firstname = firstname
        self.lastname = lastname
        self.birthday = birthday
        self.chat_id = chat_id

    def __repr__(self):
        return f"<User id=> {self.id}  ник: {self.nickname}, имя: {self.firstname} день рождения: {self.birthday}, chat_id = {self.chat_id}"
