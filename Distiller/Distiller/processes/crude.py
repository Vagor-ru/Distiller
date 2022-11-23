"""
$Id: crude.py,v 1.3 2020/07/14 
By C-Bell (VAGor).

Класс-поток перегонки спирта-сырца

"""
import time, os
from datetime import datetime
import threading
from flask import render_template
from Distiller import app, dbLock, config
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
        self._Begin=time.time()

    def Duration(self):
        sec=int(time.time()-self._Begin)
        return u'Нач. {}<br>длит. {}:{:02}:{:02}'\
               .format(time.strftime("%d.%m.%y %H:%M:%S", time.localtime(self._Begin)), 
                       sec//3600, (sec//60)%60, sec%60)

    def run(self):
        # Сброс переменной прерывания/перехода процесса
        app.config['AB_CON']=''
        #Сохранение состояния веб-интерфейса
        self.Display = app.config['Display']
        self.Buttons = app.config['Buttons']
        # Фиксация момента запуска процесса
        self._Begin=time.time()

        #Заполнение холодильников
        # Вывести сообщение на дисплей и прикрутить кнопку "Останов"
        self.pageUpdate('Заполнение холодильников<br>'+self.Duration(),
                        'ABORT.html')
        condensator.On()
        dephlegmator.On()
        time.sleep(2)
        condensator.Off()
        dephlegmator.Off()

        #Ожидание закипания
        #Мощность нагрева=100%
        power.value=250**2/config['PARAMETERS']['rTEH']['value']
        while not thermometers.boiling.wait(1):
            # Вывести на дисплей состояние
            self.pageUpdate('2-й перегон: ожидание закипания<br>'+self.Duration())
            # При получении команды прервать процесс
            if app.config['AB_CON']=='Abort':
                self.abort()
                return

        #прогрев колонны
        tBgn=time.time()
        duration=10
        # Новый набор кнопок
        self.pageUpdate(None, 'ABORT_NEXT.html')
        while time.time()-tBgn<duration:
            # Вывести на дисплей состояние
            sec=int(duration-int(time.time()-tBgn))
            sec_str=u'{:02}:{:02}'\
               .format((sec//60)%60, sec%60)
            self.pageUpdate('2-й перегон: прогрев колонны %s<br>%s'%(sec_str,self.Duration()))
            # При получении команды прервать процесс
            if app.config['AB_CON']=='Abort':
                self.abort()
                return
            # переход к отбору голов
            if app.config['AB_CON']=='Next':
                app.config['AB_CON']=''
                break
            time.sleep(1)


        ## Выход низа на температурную полку
        #tBgn=time.time()        #фиксация времени начала ожидания
        #tBott=120    #длительность ожидания в сек
        ## Новый набор кнопок
        #self.pageUpdate(None, 'ABORT_NEXT.html')
        ##подать максимальную мощность
        #power.value=250**2/config['PARAMETERS']['rTEH']['value']
        ##сравнение температур каждые 20 секунд
        #countSec=20
        #Tbott=thermometers.getValue('Низ')
        ## выдержка tBott секунд после закипания
        #while (time.time()-tBgn)<tBott:
        #    # Вывести на дисплей состояние
        #    sec=int(tBott-int(time.time()-tBgn))
        #    sec_str=u'{:02}:{:02}'\
        #       .format((sec//60)%60, sec%60)
        #    self.pageUpdate('2-й перегон стабилизация Tниз<br>%s<br>%s'%
        #                    (sec_str,self.Duration()))
        #    # При получении команды прервать процесс
        #    if app.config['AB_CON']=='Abort':
        #        self.abort()
        #        return
        #    elif app.config['AB_CON']=='Next':
        #        app.config['AB_CON']=''
        #        break
        #    countSec-=1    #уменьшить счетчик секунд
        #    if(countSec==0):
        #        countSec=20
        #        #если температура меняется не сильно, значит температурная полка достигнута
        #        if (thermometers.getValue('Низ')-Tbott<0.5):
        #            break
        #        else:
        #            Tbott=thermometers.getValue('Низ')
        #    # Отдохнуть секундочку
        #    time.sleep(1)

        # Отбор голов
        tBgn=time.time()        #фиксация времени начала отбора голов
        #установка триггера дефлегматора
        Tdeph=46.3
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
            self.pageUpdate('2-й перегон: головы<br>%s<br>%s'%(sec_str,self.Duration()))
            # Регулировать мощность нагрева
            '''Мощность устанавливается предзахлёбная, рассчитывается по формуле:
            P=Pводы-Kp*(Tкип_воды-Tниз), где
            Pводы       -предзахлёбная мощность при кипении воды в кубе
            Kp          -коэффициент изменения мощности
            Tкип_воды   -температура низа колонны при кипении воды в кубе
            Tниз        -температура низа колонны
            '''
            power.value=config['PARAMETERS']['P_H2O']['value']-config['PARAMETERS']['Kp']['value']*\
                (config['PARAMETERS']['T_H2O']['value']-thermometers.getValue('Низ'))
            #ждать завершение измерения температур
            thermometers.Tmeasured.wait()

        # Отбор тела
        self.pageUpdate('2-й перегон: тело<br><br>%s'%(self.Duration()), 'ABORT.html')
        while True:
            if app.config['AB_CON']=='Abort':
                self.abort()
                return
            # Освежить дисплей
            self.pageUpdate('2-й перегон тело<br><br>%s'%(self.Duration()))
            # Регулировать дефлегматор и нагрев
            # Регулировать дефлегматор и нагрев
            '''Температура срабатывания клапана дефлегматора рассчитывается по формуле:
            Tдеф=Tдеф_воды+Kдеф*(Tкип_воды-Tниз), где
            Tдеф_воды   -затворяющая температура дефлегматора при кипении воды в кубе
            Kдеф        -коэффициент изменения температуры срабатывания дефлегматора
            Tкип_воды   -температура низа колонны при кипении воды в кубе
            Tниз        -температура низа колонны
            '''
            Tdeph=config['PARAMETERS']['Tdephlock']['value']+config['PARAMETERS']['Kdeph']['value']*\
                (config['PARAMETERS']['T_H2O']['value']-thermometers.getValue('Низ'))
            thermometers.setTtrigger('Дефлегматор',Tdeph)
            '''Мощность устанавливается предзахлёбная, рассчитывается по формуле:
            P=Pводы-Kp*(Tкип_воды-Tниз), где
            Pводы       -предзахлёбная мощность при кипении воды в кубе
            Kp          -коэффициент изменения мощности
            Tкип_воды   -температура низа колонны при кипении воды в кубе
            Tниз        -температура низа колонны
            '''
            power.value=config['PARAMETERS']['P_H2O']['value']-config['PARAMETERS']['Kp']['value']*\
                (config['PARAMETERS']['T_H2O']['value']-thermometers.getValue('Низ'))
            #Новый критерий завершения перегона
            if (thermometers.getValue('Середина')-thermometers.getValue('Верх'))/\
                (thermometers.getValue('Низ')-thermometers.getValue('Середина'))>2:
                break
            #завершение перегона по температуре низа колонны
            if thermometers.getValue('Низ')+1.0>config['PARAMETERS']['T_H2O']['value']:
                break
            #ждать завершение измерения температур
            thermometers.Tmeasured.wait()
        # Остановить всё
        self.stop()
        self.pageUpdate('Второй перегон завершен<br>%s'%(self.Duration()),
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
