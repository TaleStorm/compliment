from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    chat_id = Column(String, unique=True)
    phone_number = Column(String, unique=True)
    is_activated = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)


class UserContacts(Base):
    __tablename__ = 'user_contacts'
    id = Column(Integer, primary_key=True)
    contact_id = Column(String, unique=True)
    birthday = Column(String)
    birthday_congrats = Column(Boolean, default=False)
    user_chat_id = Column(Integer,
                          ForeignKey('user.chat_id', ondelete='CASCADE')
                          )
