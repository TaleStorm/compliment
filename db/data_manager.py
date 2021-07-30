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
        '''
        Удаляет объект obj
        '''
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


    def update_all(self, obj, id, new_data):
        '''
        Изменяет объекта по id из словаря new_data
        {'атрибут obj':'новое значение атрибута'}
        new_data - dict
        '''
        try:
            val = self.session.query(obj).get(id)
            for k, v in new_data.items():
                setattr(val, k, v)
            self.session.commit()
        except:
            print('Error in def update_all')

    def update_ch(self, obj, ch_id, new_data):
        '''
        Изменяет объекта по chat_id из словаря new_data
        {'атрибут obj':'новое значение атрибута'}
        new_data - dict
        '''
        try:
            vall = self.session.query(obj).filter(obj.chat_id == ch_id).all()
            print(vall)
            for i in vall:
                for k, v in new_data.items():
                    setattr(i, k, v)
                self.session.commit()
        except:
            print('Error in def update_ch')
