"""
$Id: crude.py,v 1.3 2020/07/14 
By C-Bell (VAGor).

Класс-поток перегонки спирта-сырца

"""
import time, os
from datetime import datetime
import threading
from flask import render_template
from Distiller import app, dbLock
from Distiller import power, condensator, dephlegmator, thermometers
from Distiller.helpers.transmitter import Transmit



class Crude(threading.Thread):
    u'''Класс, реализующий алгоритм перегонки спирта-сырца'''

    # Для сохранения состояния дисплея и кнопок
    Display = ''
    Buttons = ''

    def __init__(self):
        #threading.Thread.__init__(self)
        super(Crude, self).__init__()
        self._Begin=datetime.now()

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
        # Вывести сообщение на дисплей и прикрутить кнопку "Останов"
        self.pageUpdate('Заполнение холодильников<br>'+self.Duration(),
                        'ABORT.html')

        #Заполнение холодильников
        condensator.On()
        dephlegmator.On()
        time.sleep(2)
        condensator.Off()
        dephlegmator.Off()

        #Мощность нагрева=100%
        power.value=250**2/config['PARAMETERS']['rTEH']
        #Ожидание закипания
        while not thermometers.boiling.wait(0.5):
            # Вывести на дисплей состояние
            self.pageUpdate('2-й перегон ожидание закипания<br>'+self.Duration())
            # При получении команды прервать процесс
            if app.config['AB_CON']=='Abort':
                self.abort()
                return

        # Выход низа на температурную полку
        tBgn=time.time()        #фиксация времени начала ожидания
        tBott=120    #длительность ожидания в сек
        # Новый набор кнопок
        self.pageUpdate(None, 'ABORT_NEXT.html')
        #подать максимальную мощность
        power.value=250**2/config['PARAMETERS']['rTEH']
        #сравнение температур каждые 20 секунд
        countSec=20
        Tbott=thermometers.getValue('Низ')
        # выдержка tBott секунд после закипания
        while (time.time()-tBgn)<tBott:
            # Вывести на дисплей состояние
            sec=int(tBott-int(time.time()-tBgn))
            sec_str=u'{:02}:{:02}'\
               .format((sec//60)%60, sec%60)
            self.pageUpdate('2-й перегон стабилизация Tниз<br>%s<br>%s'%
                            (sec_str,self.Duration()))
            # При получении команды прервать процесс
            if app.config['AB_CON']=='Abort':
                self.abort()
                return
            elif app.config['AB_CON']=='Next':
                app.config['AB_CON']=''
                break
            countSec-=1    #уменьшить счетчик секунд
            if(countSec==0):
                countSec=20
                #если температура меняется не сильно, значит температурная полка достигнута
                if (thermometers.getValue('Низ')-Tbott<0.5):
                    break
                else:
                    Tbott=thermometers.getValue('Низ')
            # Отдохнуть секундочку
            time.sleep(1)

        # Отбор голов
        tBgn=time.time()        #фиксация времени начала отбора голов
        #установка триггера дефлегматора
        Tdeph=config['PARAMETERS']['Tdeph_HEAD']
        thermometers.setTtrigger('Дефлегматор',Tdeph)
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
            '''Мощность устанавливается предзахлёбная, рассчитывается по формуле:
            P=Pводы-Kp*(Tкип_воды-Tниз), где
            Pводы       -предзахлёбная мощность при кипении воды в кубе
            Kp          -коэффициент изменения мощности
            Tкип_воды   -температура низа колонны при кипении воды в кубе
            Tниз        -температура низа колонны
            '''
            power.value=config['PARAMETERS']['P_H2O']-config['PARAMETERS']['Kp']*\
                (config['PARAMETERS']['T_H2O']-thermometers.getValue('Низ'))
            #ждать завершение измерения температур
            thermometers.Tmeasured.wait()

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
