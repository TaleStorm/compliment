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

    def create_table(self, obj):
        obj.metadata.create_all(self.engine)

    def add(self, obj):
        self.session.add(obj)
        self.session.commit()

    def getById(self, obj, id):
        for result in self.session.query(obj).filter_by(id=id):
            return result
