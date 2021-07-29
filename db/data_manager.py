from sqlalchemy import create_engine
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
        '''
        Добавляет новый объект
        '''
        self.session.add(obj)
        self.session.commit()

    def get_by_id(self, obj, id):
        """
        Возвращает объект по id
        """
        result = self.session.query(obj).get(id)
        return result

    def del_by_id(self, obj, id):
        '''
        Удаляет объект по id
        '''
        self.session.delete(self.session.query(obj).get(id))
        self.session.commit()

    def del_obj(self, obj):
        self.session.delete(obj)
        self.session.commit()

    def update_state(self, obj, id, state, new):
        '''
        Изменяет значение атрибута state на new
        '''
        try:
            user = self.session.query(obj).get(id)
            setattr(user, state, new)
            self.session.commit()
        except:
            print('Error in def update_state')

    # def get_by_all(self, obj):
    #     for ins in self.session.query(obj).order_by(obj.id):
    #         print(ins)

    #     print(self.session.query(obj).all())
