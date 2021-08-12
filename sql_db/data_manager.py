from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class DataManager:
    def __init__(self, str_connection, base):
        self.engine = create_engine(str_connection)
        self.engine.connect()
        self._create_table(base)
        Session = sessionmaker()
        Session.configure(bind=self.engine)
        self.session = Session()

    def _create_table(self, obj):
        obj.metadata.create_all(self.engine)
