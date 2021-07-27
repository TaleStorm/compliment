from sqlalchemy import create_engine
from datetime import datetime
from sqlalchemy import MetaData, Table, String, Integer, Column, Text, DateTime, Boolean
from sqlalchemy.orm import sessionmaker

class DataManager:
    def __init__(self, str_connection):
        self.engine = create_engine(str_connection)
        self.engine.connect()
        Session = sessionmaker()
        Session.configure(bind=self.engine)
        self.session = Session()

    def _create_table(self, obj):
        obj.metadata.create_all(self.engine)

    def add(self, obj):
        self.session.add(obj)
        self.session.commit()

    def get_by_id(self, obj, id):
        """
        Возвращает объект по id
        """
        result = self.session.query(obj).get(id)
        return result

    def del_by_id(self, obj, id):
        self.session.delete(self.session.query(obj).get(id))
        self.session.commit()

    def del_obj(self, obj):
        self.session.delete(obj)
        self.session.commit()

    def get_by_all(self,obj):
        for ins in self.session.query(obj).order_by(obj.id):
            print(ins)
            print (ins.name, ins.id, ins.chat_id)

    def update(self, obj, value):
        self.session.query(obj).update(value)

