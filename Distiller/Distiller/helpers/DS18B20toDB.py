"""
$Id: DS18B20toDB.py,v 1.0 2017/07/19
Copyright (c) C-Bell (VAGor). All rights reserved.

Класс-поток обеспечивает запись значений температур от
цифровых термометров в базу данных.
Данные будут записаны как только будут получены.
"""

import threading, time
from datetime import datetime
from Distiller import models, app, dbLock, socketio
            
from Distiller.sensors.DS18B20 import Measure
from Distiller.helpers.transmitter import Transmit

#Класс исключения при несовпадении количеств термометров
class NumThermometersMismatch(Exception):
    '''Исключение при несовпадении количества термометров
    на шине 1-wire и в конфигурации'''
    pass


class DS18B20toDB(threading.Thread):
    """Класс записывает показания DS18B20 в базу данных"""

    # событие записи в БД очередных показаний термометров
    ReadyDS18B20 = threading.Event()
    # список термометров с их показаниями
    TlistToClient = []

    def CheckTlist(self):
        '''Проверяет списки термометров на шине 1-Wire и в базе данных,
        дает заключение о необходимости определения мест их расположения.'''
        # Список термометров на шине
        Tlist = Measure()
        '''Если длина списка термометров в конфиге не совпадает
        с количеством термометров на 1-Wire, поднять исключение.'''
        if len(Tlist)!=len(app.config['T_LOCATION']):
            raise NumThermometersMismatch('Number of thermometers on 1-Wire bus mismatched number of thermometers in config.')
        # Список ID термометров
        TIDlist=[T[0] for T in Tlist]
        dbLock.acquire()
        # список термометров в БД
        TfromDB=models.DS18B20.query.all()
        #Если БД ещё пустая
        if len(TfromDB) == 0:
            # Набор кнопок для запуска
            app.config['Buttons']='WAITAL.html'
            # Надпись на дисплее
            app.config['Display']='Требуется определение мест расположения термометров'
            dbLock.release()
            return
        for TDB in TfromDB:
            if not TDB.IDthermometer in TIDlist:
                print('Удаление термометра %s из БД'%TDB.IDthermometer)
                models.db.session.delete(TDB)
        # Количество несовпадений имен термометров
        Mismatch = 0
        # Имя нового термометра
        Tm=''
        # Проверка мест расположения термометров
        for Tname in app.config['T_LOCATION']:
            Thrmmtr = models.DS18B20.query.filter_by(Name=Tname).all()
            if len(Thrmmtr) == 0:
                Mismatch += 1
                Tm = Tname
                #print('Термометр с именем %s не найден'%Tname)
            elif len(Thrmmtr)>1:
                Mismatch += 2
                #print('Более одного термометра с именем %s'%Tname)
            else:
                #print('Термометр %s имеет ID %s'%(Tname,Thrmmtr[0].IDthermometer))
                pass
        # Набор кнопок для запуска
        app.config['Buttons']='WAIT.html'
        # Надпись на дисплее
        app.config['Display']='Жду команду.'
        # Заменён один термометр
        if Mismatch == 1:
            Thrmmtr = models.DS18B20.query.filter_by(Name='').first()
            Thrmmtr.Name = Tm
        # Требуется определение расположения термометров
        elif Mismatch > 1:
            # Набор кнопок для запуска
            app.config['Buttons']='WAITAL.html'
            # Надпись на дисплее
            app.config['Display']='Требуется определение мест расположения термометров'
        models.db.session.commit()
        dbLock.release()


    def __init__(self):
        '''инициализация'''
        #threading.Thread.__init__(self)
        super(DS18B20toDB, self).__init__()
        self.__Run = False
        self.CheckTlist()
        self.ReadyDS18B20.clear()

    def run(self):
        self.__Run = True
        while self.__Run:
            # Если флаг готовности температурных данных в БД установлен,
            # сбросить его
            if self.ReadyDS18B20.isSet(): self.ReadyDS18B20.clear()
            # Получаем температурные данные(параметром передаётся таймаут в
            # секундах)
            Tlist = Measure(6)
            # Блокируем другие потоки
            dbLock.acquire()
            # Признак изменения температурных данных
            IsNew=False
            # Ложим в базу температурные данные
            for eashT in Tlist:
                Thrmmtr = models.DS18B20.query.filter_by(IDthermometer=eashT[0]).first()
                if Thrmmtr == None:
                    #Если в БД не найден термометр с соответствующим ID,
                    #сохраняем новый термометр
                    Thrmmtr = models.DS18B20(IDthermometer=eashT[0], Name='',
                                            T=eashT[1], Timestamp=eashT[2])
                    IsNew=True
                else:
                    #Если найден, изменяем температуру и время её фиксации
                    if Thrmmtr.T != eashT[1]:
                        IsNew=True
                        Thrmmtr.T = eashT[1]
                    Thrmmtr.Timestamp = eashT[2]
                models.db.session.add(Thrmmtr)
            models.db.session.commit()  #сохраняем изменения в БД
            # Разблокируем другие потоки
            dbLock.release()
            # Обновление и передача температурных значений только если они отличаются от предыдущих
            if IsNew:
                Transmit({'Thermometers' : self.TlistToClient, 'DateTime' :time.time()})
            self.GiveTemperatureFromDB()
            # Вскидываем флаг готовности свежих температурных данных в БД
            self.ReadyDS18B20.set()
        return

    def stop(self):
        self.__Run = False

    def GiveTemperatureFromDB(self):
        u'''Собирает и возвращает список кортежей имен термометров и значений температур
        в том порядке, в котором они прописаны в config.py'''
        dbLock.acquire()
        self.TlistToClient=[]
        if len(models.DS18B20.query.filter(models.DS18B20.Name!='').all())!=0:
            for NameT in app.config['T_LOCATION']:
                Thrmmtr=models.DS18B20.query.filter_by(Name=NameT).first()
                if Thrmmtr!=None:
                    self.TlistToClient.append((Thrmmtr.Name,Thrmmtr.T))
        Tlist=models.DS18B20.query.filter(models.DS18B20.Name=='').all()
        for eachT in Tlist:
            self.TlistToClient.append((eachT.IDthermometer,eachT.T))
        dbLock.release()
        app.config['Thermometers'] = self.DataFromServer

    @property
    def DataFromServer(self):
        return {'Thermometers' : self.TlistToClient}


