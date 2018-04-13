"""
$Id: autolocation.py,v 1.0 2017/06/22 

Copyright (c) 2017 C-Bell (VAGor). All rights reserved.

Модуль автоматически определяет и сохраняет в базе данных
места расположения цифровых термометров DS18B20

Нужно заправить аппаратуру перед запуском.
По завершении его работы в БД будут сохранены места расположения
цифровых термометров DS18B20 (в таблице DS18B20cur).

"""

import time
from datetime import datetime
import threading
from flask import render_template
from Distiller import models, app, dbLock
from Distiller import power, condensator, dephlegmator
from Distiller.helpers.transmitter import Transmit
from Distiller.helpers.logging import Logging

class Autolocation(threading.Thread):
    u'''Класс-поток, определяющий расположение термометров.'''

    # Для сохранения состояния дисплея и кнопок
    Display = ''
    Buttons = ''

    def __init__(self):
        threading.Thread.__init__(self)
        self._Begin=datetime.now()
        self.logger=Logging()
        self.logger.setName('Logger')

    def Duration(self):
        sec=(datetime.now()-self._Begin).seconds
        return u'Нач.{}<br>длит. {}:{:02}:{:02}'\
               .format(self._Begin.strftime('%d.%m.%y %H:%M:%S'), sec//3600, (sec//60)%60, sec%60)

    def run(self):
        """Процесс автоопределения мест расположения термометров"""
        # сброс переменной прерывания/перехода процесса
        app.config['AB_CON']=''
        #Фиксация момента запуска процесса
        self._Begin=datetime.now()
        #Сохранение состояния веб-интерфейса
        self.Display = app.config['Display']
        self.Buttons = app.config['Buttons']
        # создание и запуск объекта ведения журнала 
        self.logger.start()
        # Вывести сообщение на дисплей и прикрутить кнопку "Останов"
        self.pageUpdate('Заполнение холодильников<br>'+self.Duration(),
                        'ABORT.html')
        #Заполнение холодильников 2сек
        condensator.On()
        dephlegmator.On()
        time.sleep(2)
        condensator.Off()
        dephlegmator.Off()
        #Мощность нагрева=100%
        self.pageUpdate('Мощность нагрева=100%<br>ожидание закипания<br>'+self.Duration())
        power.Value=100
        #Ожидание закипания
        while True:
            # При получении команды прервать процесс
            if app.config['AB_CON']=='Abort':
                self.abort()
                return
            #self.logger.ReadyLog.wait()    #Ждем завершение записи в журнал
            #спим одну секунду
            time.sleep(1)
            self.pageUpdate('Мощность нагрева=100%<br>ожидание закипания<br>'+self.Duration())
            #Проверить скорость роста температур
            #Извлекаем из лога два последних момента фиксации температур
            dbLock.acquire()
            LastMeasures=models.log.query.order_by(models.db.desc(models.log.id)).limit(2).all()
            #Если их ещё не два, то пропускаем
            if len(LastMeasures)==2:
                #Количество секунд между двумя последними измерениями
                sec=(LastMeasures[0].TimeStamp-LastMeasures[1].TimeStamp).total_seconds()
                for Samp in LastMeasures[0].Tsample:
                    #Если скорость роста температуры на каком-либо термометре более 1°C в секунду, значит закипание
                    if (Samp.T - LastMeasures[1].Tsample.filter_by(id_DS18B20=Samp.id_DS18B20).first().T)/sec>1:
                        dbLock.release()
                        break
                else:   #если цикл for не был прерван, продолжаем цикл while
                    dbLock.release()
                    continue
                break   #при прерывании цикла for прерываем цикл while
        #Уменьшаем мощность до 30%
        power.Value=25
        # Пауза 30 сек
        tBegin=time.time()
        while time.time()-tBegin<30:
            # При получении команды прервать процесс
            if app.config['AB_CON']=='Abort':
                self.abort()
                return
            sec=20-int(time.time()-tBegin)
            sec_str=u'{:02}:{:02}'\
               .format((sec//60)%60, sec%60)
            self.pageUpdate('Мощность нагрева=25%%<br>Пауза %s<br>%s'%
                            (sec_str,self.Duration()))
            time.sleep(1)
        #Включаем клапаны дефлегматора и конденсатора на 40 сек
        condensator.On()
        dephlegmator.On()
        tBegin=time.time()
        while time.time()-tBegin<40:
            # При получении команды прервать процесс
            if app.config['AB_CON']=='Abort':
                self.abort()
                return
            sec=40-int(time.time()-tBegin)
            sec_str=u'{:02}:{:02}'\
               .format((sec//60)%60, sec%60)
            self.pageUpdate('Мощность нагрева=25%%<br>Охладители %s<br>%s'%
                            (sec_str,self.Duration()))
            time.sleep(1)
        #Отключаем клапан дефлегматора и ждем ещё 40 сек
        dephlegmator.Off()
        tBegin=time.time()
        while time.time()-tBegin<40:
            # При получении команды прервать процесс
            if app.config['AB_CON']=='Abort' or app.config['AB_CON']=='Error':
                self.stop()
                return
            sec=40-int(time.time()-tBegin)
            sec_str=u'{:02}:{:02}'\
               .format((sec//60)%60, sec%60)
            self.pageUpdate('Прогрев дефлегматора<br>%s<br>%s'%
                            (sec_str,self.Duration()))
            time.sleep(1)
        #Читаем из базы в порядке убывания температур, присваиваем имена и завершаем
        self.pageUpdate('Присвоение имен термометрам<br>%s'%
                        (self.Duration()))
        dbLock.acquire()
        Tlist=models.DS18B20.query.order_by(models.db.desc(models.DS18B20.T)).all()
        for i in range(len(Tlist)):
            Tlist[i].Name=app.config['T_LOCATION'][i]
        models.db.session.commit()
        dbLock.release()
        self.stop()
        self.pageUpdate('Автоопределение завершено<br>%s'%(self.Duration()),
                        'END.html')
        return

    def stop(self):
        power.Value = 0 #отключаем нагрев
        condensator.Off()   #отключаем клапан конденсатора
        dephlegmator.Off()  #отключаем клапан дефлегматора
        self.logger.stop()   #завершить ведение журнала

    def abort(self):
        self.stop()
        #Восстановление состояния интерфейса
        self.pageUpdate(self.Display, self.Buttons)

    def pageUpdate(self, Display=None, Buttons=None):
        DataFromServer={}
        if Display != None:
            app.config['Display'] = Display
            DataFromServer['Display'] = Display
        if Buttons != None:
            app.config['Buttons'] = Buttons
            with app.test_request_context():
                DataFromServer['ModeButtons'] = render_template(Buttons)
        if len(DataFromServer) > 0:
            Transmit(DataFromServer)
