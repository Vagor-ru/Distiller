"""
$Id: crude.py,v 1.1 2017/09/18 
Copyright (c) 2017 C-Bell (VAGor).

Класс-поток перегонки спирта-сырца

"""
import time, os
from datetime import datetime
import threading
from flask import render_template
from Distiller import models, app, dbLock
from Distiller import power, condensator, dephlegmator
from Distiller.helpers.transmitter import Transmit
from Distiller.helpers.logging import Logging
from Distiller.helpers.coolsRegulator import CoolsRegulator



class Crude(threading.Thread):
    u'''Класс, реализующий алгоритм перегонки спирта-сырца'''

    # Для сохранения состояния дисплея и кнопок
    Display = ''
    Buttons = ''

    def __init__(self):
        threading.Thread.__init__(self)
        self._Begin=datetime.now()
        self.CoolsRegl=CoolsRegulator()
        self.CoolsRegl.name='CoolsRegulator'
        self.Log=Logging()
        self.Log.name='Logger'

    def Duration(self):
        sec=(datetime.now()-self._Begin).seconds
        return u'Нач. {}<br>длит. {}:{:02}:{:02}'\
               .format(self._Begin.strftime('%d.%m.%y %H:%M:%S'), 
                       sec//3600, (sec//60)%60, sec%60)

    def run(self):
        # Сброс переменной прерывания/перехода процесса
        app.config['AB_CON']=''
        #Сохранение состояния веб-интерфейса
        self.Display = app.config['Display']
        self.Buttons = app.config['Buttons']
        # Фиксация момента запуска процесса
        self._Begin=datetime.now()
        # Старт процесса журналирования
        self.Log.start()
        # Вывести сообщение на дисплей и прикрутить кнопку "Останов"
        self.pageUpdate('Заполнение холодильников<br>'+self.Duration(),
                        'ABORT.html')
        #Заполнение холодильников
        condensator.On()
        dephlegmator.On()
        time.sleep(2)
        condensator.Off()
        dephlegmator.Off()
        #старт регулятора охлаждения
        self.CoolsRegl.start()
        #Мощность нагрева=100%
        power.Value=100
        #Ожидание закипания
        while True:
            # Вывести на дисплей состояние
            self.pageUpdate('Разгон (ожидание закипания)<br>'+self.Duration())
            # При получении команды прервать процесс
            if app.config['AB_CON']=='Abort':
                self.abort()
                return
            # Отдохнуть секундочку
            time.sleep(1)
            #Проверить скорость роста температур
            #Извлекаем из лога два последних момента фиксации температур
            dbLock.acquire()
            LastMeasures=models.log.query.order_by(models.db.desc(models.log.id)).limit(2).all()
            #Если их ещё не два, то пропускаем
            if len(LastMeasures) < 2:
                dbLock.release()
                continue
            # Секунд между двумя последними измерениями
            sec=(LastMeasures[0].TimeStamp-LastMeasures[1].TimeStamp).total_seconds()
            for Samp in LastMeasures[0].Tsample:
                #Если скорость роста температуры на каком-либо термометре более 1°C в секунду, значит закипание
                V=(Samp.T - LastMeasures[1].Tsample.filter_by(id_DS18B20=Samp.id_DS18B20).first().T)/sec
                #print(V)
                if V>1.0:
                    dbLock.release()
                    break
            else:
                dbLock.release()
                continue
            break
        #Стабилизация
        tBgn=time.time()        #фиксация времени начала стабилизации
        dbLock.acquire()
        power.Value=models.Parameters2.query.filter(models.Parameters2.Symbol==u'Pst').first().Value
        durationSt=int(60*models.Parameters2.query.filter(models.Parameters2.Symbol==u'tSt').first().Value)
        #durationSt=10       # ВРЕМЕННО!!!УБРАТЬ!!!
        dbLock.release()
        #print(u'Стабилизация=%sсек'%durationSt)
        # Врезать две кнопки "Останов" и "След.этап"
        self.pageUpdate('Стабилизация<br><br>%s'%(self.Duration()), 'ABORT_NEXT.html')
        while (time.time()-tBgn) < durationSt:
            # Вывести на дисплей состояние
            sec=int(durationSt-int(time.time()-tBgn))
            sec_str=u'{:02}:{:02}'\
               .format((sec//60)%60, sec%60)
            self.pageUpdate('Стабилизация<br>%s<br>%s'%(sec_str,self.Duration()))
            # При получении команды прервать процесс
            if app.config['AB_CON']=='Abort':
                self.abort()
                return
            # переход к отбору голов
            if app.config['AB_CON']=='Next':
                app.config['AB_CON']=''
                break
            # Отдохнуть секундочку
            time.sleep(1)
        # Отбор голов
        tBgn=time.time()        #фиксация времени начала отбора голов
        dbLock.acquire()
        self.CoolsRegl.Tdeph=models.Parameters2.query.filter(models.Parameters2.Symbol==u'Thdeph').first().Value
        dbLock.release()
        while True:
            # При получении команды прервать процесс
            if app.config['AB_CON']=='Abort':
                self.abort()
                return
            # переход к отбору тела
            if app.config['AB_CON']=='Next':
                app.config['AB_CON']=''
                break
            # Вывести состояние на дисплей
            sec=int(time.time()-tBgn)
            sec_str=u'{}:{:02}:{:02}'\
               .format(sec//3600, (sec//60)%60, sec%60)
            self.pageUpdate('Отбор голов<br>%s<br>%s'%(sec_str,self.Duration()))
            # Регулировать мощность нагрева
            dbLock.acquire()
            Kp = models.Parameters2.query.filter(models.Parameters2.Symbol=='Kp').first().Value
            Pbase = models.Parameters2.query.filter(models.Parameters2.Symbol=='Pbase').first().Value
            Tbott = models.DS18B20.query.filter(models.DS18B20.Name=='Низ').first().T
            power.Value=(Pbase+Kp*Tbott)
            dbLock.release()
            # Отдохнуть секундочку
            time.sleep(1)
        # Отбор тела
        self.pageUpdate('Отбор тела<br><br>%s'%(self.Duration()), 'ABORT.html')
        while True:
            if app.config['AB_CON']=='Abort':
                self.abort()
                return
            # Освежить дисплей
            self.pageUpdate('Отбор тела<br><br>%s'%(self.Duration()))
            # Регулировать дефлегматор и нагрев
            dbLock.acquire()
            Tbdeph = models.Parameters2.query.filter(models.Parameters2.Symbol=='Tbdeph').first().Value
            Kdeph = models.Parameters2.query.filter(models.Parameters2.Symbol=='Kdeph').first().Value
            Pbase = models.Parameters2.query.filter(models.Parameters2.Symbol=='Pbase').first().Value
            Kp = models.Parameters2.query.filter(models.Parameters2.Symbol=='Kp').first().Value
            Tbott = models.DS18B20.query.filter(models.DS18B20.Name=='Низ').first().T
            self.CoolsRegl.Tdeph=(Tbdeph-Kdeph*Tbott)
            power.Value=(Pbase+Kp*Tbott)
            if models.DS18B20.query.filter(models.DS18B20.Name=='Низ').first().T>models.Parameters2.query.filter(models.Parameters2.Symbol=='Tend').first().Value:
                dbLock.release()
                break
            dbLock.release()
            # Отдохнуть секундочку
            time.sleep(1)
        # Остановить всё
        self.stop()
        self.pageUpdate('Второй перегон завершен<br>%s'%(self.Duration()),
                        'END.html')
        return

    def stop(self):
        power.Value = 0 #отключаем нагрев
        condensator.Off()   #отключаем клапан конденсатора
        dephlegmator.Off()  #отключаем клапан дефлегматора
        self.Log.stop()   #завершить ведение журнала
        self.CoolsRegl.stop()   #остановить регулятор охлаждения

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
