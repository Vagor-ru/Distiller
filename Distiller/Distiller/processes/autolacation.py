"""
$Id: autolocation.py,v 1.3 2020/07/08 

C-Bell (VAGor). 

Модуль автоматически определяет и сохраняет в конфигурации
места расположения цифровых термометров DS18B20

Нужно заправить аппаратуру перед запуском.
По завершении его работы в БД будут сохранены места расположения
цифровых термометров DS18B20 (в таблице DS18B20cur).

"""

import time
from datetime import datetime
import threading
import json
from flask import render_template
from Distiller import app, dbLock, config
from Distiller import power, condensator, dephlegmator,thermometers
from Distiller.helpers.transmitter import Transmit

class Autolocation(threading.Thread):
    u'''Класс-поток, определяющий расположение термометров.'''

    # Для сохранения состояния дисплея и кнопок
    Display = ''
    Buttons = ''

    def __init__(self):
        #threading.Thread.__init__(self)
        super(Autolocation, self).__init__()
        self._Begin=datetime.now()

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
        self.pageUpdate('Ожидание закипания<br>'+self.Duration())
        power.value=4.0
        #Ожидание закипания
        while not thermometers.boiling.wait(0.5):
            self.pageUpdate('Ожидание закипания<br>'+self.Duration())
            # При получении команды прервать процесс
            if app.config['AB_CON']=='Abort':
                self.abort()
                return

        #Уменьшить мощность
        power.value=4.0/4
        # Пауза 
        tBegin=time.time()
        duration=80
        while time.time()-tBegin<duration:
            # При получении команды прервать процесс
            if app.config['AB_CON']=='Abort':
                self.abort()
                return
            sec=duration-int(time.time()-tBegin)
            sec_str=u'{:02}:{:02}'\
               .format((sec//60)%60, sec%60)
            self.pageUpdate('Прогрев колонны %s<br>%s'%
                            (sec_str,self.Duration()))
            time.sleep(1)
        #Включить клапаны дефлегматора и конденсатора на 20 сек
        duration=20
        condensator.On()
        dephlegmator.On()
        tBegin=time.time()
        while time.time()-tBegin<duration:
            # При получении команды прервать процесс
            if app.config['AB_CON']=='Abort':
                self.abort()
                return
            sec=duration-int(time.time()-tBegin)
            sec_str=u'{:02}:{:02}'\
               .format((sec//60)%60, sec%60)
            self.pageUpdate('Охлаждение холодильников %s<br>%s'%
                            (sec_str,self.Duration()))
            time.sleep(1)
        #Отключить клапан дефлегматора и ждать ещё 30 сек
        duration=30
        dephlegmator.Off()
        tBegin=time.time()
        while time.time()-tBegin<duration:
            # При получении команды прервать процесс
            if app.config['AB_CON']=='Abort' or app.config['AB_CON']=='Error':
                self.abort()
                return
            sec=duration-int(time.time()-tBegin)
            sec_str=u'{:02}:{:02}'\
               .format((sec//60)%60, sec%60)
            self.pageUpdate('Прогрев дефлегматора<br>%s<br>%s'%
                            (sec_str,self.Duration()))
            time.sleep(1)
        #Сортировать в порядке убывания температур, присвоить имена и завершить
        self.pageUpdate('Присвоение имен термометрам<br>%s'%
                        (self.Duration()))
        dbLock.acquire()    #захватить исполнение только этим потоком
        #сортировка списка термометров в порядке возрастания температур
        i=0
        T_LOCATIONS={}
        for Th in sorted(thermometers.Tlist, key=lambda thermometer: thermometer.T):
            #print (Th.T)
            Th.Name=config['LOCATIONS'][i]  #имя (место расположения) термометра
            T_LOCATIONS[Th.ID]=config['LOCATIONS'][i]   #имя, соответствующее ID, для сохранения в конфигурации
            Th.Ttrigger=None
            if Th.Name=='Конденсатор':
                Th.Ttrigger=config['PARAMETERS']['Tcond']['value']
            if Th.Name=='Дефлегматор':
                Th.Ttrigger=config['PARAMETERS']['Tdephlock']['value']
            i+=1
        #сохранить конфигурацию
        config['LOCATIONS']["locations"]=T_LOCATIONS
        thermometers.needAutoLocation=False #сбросить флаг автоопределения мест установки термометров
        with open('configDistiller.json','w',encoding="utf-8") as f:
            json.dump(config,f,ensure_ascii=False, indent=2)
        dbLock.release()    #включить многопоточный режим
        self.stop()
        self.pageUpdate('Автоопределение завершено<br>%s'%(self.Duration()),
                        'END.html')
        return

    def stop(self):
        power.value = 0 #отключаем нагрев
        condensator.Off()   #отключаем клапан конденсатора
        dephlegmator.Off()  #отключаем клапан дефлегматора

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
