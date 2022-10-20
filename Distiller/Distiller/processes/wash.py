"""
$Id: wash.py,v 1.3 2020/07/09 
 By C-Bell (VAGor).

Класс-поток перегонки бражки

"""
import time, os
from datetime import datetime
import threading
from flask import render_template
from simple_pid import PID
from Distiller import app, dbLock,config
from Distiller import power, condensator, dephlegmator, coolsRegulator, thermometers
from Distiller.helpers.transmitter import Transmit
from Distiller.actuators.dephlegmator import DephRun

class Wash(threading.Thread):
    u'''Класс, реализующий алгоритм перегонки бражки'''

    # Для сохранения состояния дисплея и кнопок
    Display = ''
    Buttons = ''

    def __init__(self):
        #threading.Thread.__init__(self)
        super(Wash, self).__init__()
        self.pid = PID(5, 0.25, 0.1, setpoint=66.1)
        self.pid.output_limits = (0, 100)
        self.Deph = DephRun()
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
        #Запуск регулятора охладителя дефлегматора
        self.Deph.run()
        # Вывести сообщение на дисплей и прикрутить кнопку "Останов"
        self.pageUpdate('Заполнение холодильников<br>'+self.Duration(),
                        'ABORT.html')

        #Заполнение холодильников
        tBgn=time.time()        #фиксация времени начала заполнения
        thermometers.setTtrigger('Дефлегматор',15)
        thermometers.setTtrigger('Конденсатор',15)
        while (time.time()-tBgn) < config['PARAMETERS']['tFillCoolers']['value']:
            # При получении команды прервать процесс
            if app.config['AB_CON']=='Abort':
                self.abort()
                return
            elif app.config['AB_CON']=='Next':
                app.config['AB_CON']=''
                break
            # Отдохнуть секундочку
            time.sleep(1)
        thermometers.setTtrigger('Дефлегматор', config['PARAMETERS']['Tdeph_H2O']['value'])
        thermometers.setTtrigger('Конденсатор',config['PARAMETERS']['Tcond']['value'])

        #Мощность нагрева=100%
        power.value=4.0
        #Ожидание закипания
        while not thermometers.boiling.wait(1):
            # Вывести на дисплей состояние
            self.pageUpdate('Бражка: ожидание закипания<br>'+self.Duration())
            # При получении команды прервать процесс
            if app.config['AB_CON']=='Abort':
                self.abort()
                return

        # антипена
        tBgn=time.time()        #фиксация времени начала стабилизации
        Tbott=thermometers.getValue('Низ')  #фиксация температуры стабилизации
        Pst=config['PARAMETERS']['P_H2O']-config['PARAMETERS']['Kp']*\
            (config['PARAMETERS']['T_H2O']-Tbott)
        Kst=0.8   #коэффициент пропорционального регулятора
        self.pageUpdate('Бражка: антипена<br>%s'%(self.Duration()), 'ABORT_NEXT.html')
        duration=60*float(config['PARAMETERS']['tA_F'])
        while (time.time()-tBgn) < duration:
            # Вывести на дисплей состояние
            sec=int(duration-int(time.time()-tBgn))
            sec_str=u'{:02}:{:02}'\
               .format((sec//60)%60, sec%60)
            self.pageUpdate('Бражка: антипена %s<br>%s'%(sec_str,self.Duration()))
            #пропорциональный регулятор
            power.value=Pst-Kst*(thermometers.getValue('Низ')-Tbott)
            # При получении команды прервать процесс
            if app.config['AB_CON']=='Abort':
                self.abort()
                return
            elif app.config['AB_CON']=='Next':
                app.config['AB_CON']=''
                break
            # Отдохнуть секундочку
            time.sleep(1)

        #Вывод верха колонны на температурную полку
        #подать максимальную мощность
        power.value=250**2/config['PARAMETERS']['rTEH']
        tBgn=time.time()        #фиксация времени начала этапа
        while True:
            # Вывести на дисплей состояние
            sec=int(time.time()-tBgn)
            sec_str=u'{:02}:{:02}'\
               .format((sec//60)%60, sec%60)
            self.pageUpdate('Бражка: стабилизация1 %s<br>%s'%(sec_str,self.Duration()))
            # При получении команды прервать процесс
            if app.config['AB_CON']=='Abort':
                self.abort()
                return
            elif app.config['AB_CON']=='Next':
                app.config['AB_CON']=''
                break
            if thermometers.boiling.wait(1) and thermometers.getObjT('Верх').boiling:
                break    #поймали закипание на верхнем термометре
        Vt=0    #накопитель скоростей роста температуры
        numberSec =5  #Количество секунд, за которые измеряется средняя скорость
        while True:
            #установить мощность, соответствующую температуре низа колонны
            power.value=config['PARAMETERS']['P_H2O']-config['PARAMETERS']['Kp']*\
                (config['PARAMETERS']['T_H2O']-thermometers.getValue('Низ'))
            # Вывести на дисплей состояние
            sec=int(time.time()-tBgn)
            sec_str=u'{:02}:{:02}'\
               .format((sec//60)%60, sec%60)
            self.pageUpdate('Бражка: стабилизация2 %s<br>%s'%(sec_str,self.Duration()))
            # При получении команды прервать процесс
            if app.config['AB_CON']=='Abort':
                self.abort()
                return
            elif app.config['AB_CON']=='Next':
                app.config['AB_CON']=''
                break
            thermometers.Tmeasured.wait()   #ожидать следующего измерения температуры
            numberSec-=1
            if numberSec==0:
                numberSec =5
                if Vt/numberSec < 0.2:  #если скорость роста температуры низкая, значит температурная полка
                    #print(u"температурная полка")
                    break
                Vt=0
            else:
                objT=thermometers.getObjT('Верх')
                Vt+=objT.V_T

        # Отбор тела
        self.pageUpdate('Бражка: перегон<br><br>%s'%(self.Duration()), 'ABORT.html')
        while True:
            #нажата кнопка Останов
            if app.config['AB_CON']=='Abort':
                self.abort()
                return
            # Освежить дисплей
            self.pageUpdate('Бражка: перегон<br><br>%s'%(self.Duration()))
            # Регулировать дефлегматор и нагрев
            '''Температура срабатывания клапана дефлегматора рассчитывается по формуле:
            Tдеф=Tдеф_воды+Kдеф*(Tкип_воды-Tниз), где
            Tдеф_воды   -затворяющая температура дефлегматора при кипении воды в кубе
            Kдеф        -коэффициент изменения температуры срабатывания дефлегматора
            Tкип_воды   -температура низа колонны при кипении воды в кубе
            Tниз        -температура низа колонны
            '''
            Tdeph=config['PARAMETERS']['Tdeph_H2O']['value']+config['PARAMETERS']['Kdeph']*\
                (config['PARAMETERS']['T_H2O']-thermometers.getValue('Низ'))
            thermometers.setTtrigger('Дефлегматор',Tdeph)
            '''Мощность устанавливается предзахлёбная, рассчитывается по формуле:
            P=Pводы-Kp*(Tкип_воды-Tниз), где
            Pводы       -предзахлёбная мощность при кипении воды в кубе
            Kp          -коэффициент изменения мощности
            Tкип_воды   -температура низа колонны при кипении воды в кубе
            Tниз        -температура низа колонны
            '''
            power.value=config['PARAMETERS']['P_H2O']-config['PARAMETERS']['Kp']*\
                (config['PARAMETERS']['T_H2O']-thermometers.getValue('Низ'))
            #Новый критерий завершения перегона
            if (thermometers.getValue('Середина')-thermometers.getValue('Верх'))/\
                (thermometers.getValue('Низ')-thermometers.getValue('Середина'))>2:
                break
            #завершение перегона по температуре низа колонны
            if thermometers.getValue('Низ')+1.0>config['PARAMETERS']['T_H2O']:
                break
            #ждать завершение измерения температур
            thermometers.Tmeasured.wait()
        # Остановить всё
        self.stop()
        self.pageUpdate('Перегон бражки завершен<br>%s'%(self.Duration()),
                        'END.html')
        return

    def stop(self):
        self.Deph.value = 0
        self.Deph.stop()    # останов охлаждения дефлегматора
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

