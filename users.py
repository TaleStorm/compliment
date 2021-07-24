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
        return "<User('%s','%s', '%s')>" % (self.name, self.birthday, self.chat_id)