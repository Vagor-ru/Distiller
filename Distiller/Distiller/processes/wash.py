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
        """Множители PID-регулятора дефлегматора"""
        MKp = -1    #множитель пропорциональной части
        MKi = -1    #множитель интегральной части
        MKd = -1    #множитель дифференциальной части
        self.pidD = PID(5*MKp, 0.25*MKi, 0.1*MKd, setpoint=66.1)
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
        #thermometers.setTtrigger('Дефлегматор',15)
        self.Deph.value = 100
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
        #thermometers.setTtrigger('Дефлегматор', config['PARAMETERS']['Tdeph_H2O']['value'])
        self.Deph.value = 0
        thermometers.setTtrigger('Конденсатор',config['PARAMETERS']['Tcond']['value'])

        """Ожидание закипания"""
        #Мощность нагрева=100%
        power.value=4.0
        while not thermometers.boiling.wait(1):
            # Вывести на дисплей состояние
            self.pageUpdate('Бражка: Нагрев<br>'+self.Duration())
            # При получении команды прервать процесс
            if app.config['AB_CON']=='Abort':
                self.abort()
                return
        power.value=0   #отключить нагрев

        """Пауза"""
        tBgn=time.time()        #фиксация времени начала паузы
        while (time.time()-tBgn) < 10:
            self.pageUpdate('Бражка: Нагрев<br>'+self.Duration())
            # При получении команды прервать процесс
            if app.config['AB_CON']=='Abort':
                self.abort()
                return

        """Антипена"""
        tBgn=time.time()        #фиксация времени начала стабилизации
        Tbott=thermometers.getValue('Низ')  #фиксация температуры стабилизации
        #Pst=config['PARAMETERS']['P_H2O']['value']-config['PARAMETERS']['Kp']['value']*\
        #    (config['PARAMETERS']['T_H2O']['value']-Tbott)
        #Kst=0.8   #коэффициент пропорционального регулятора
        pidH = PID(10, 0.25, 0.1, setpoint=Tbott)
        pidH.output_limits(0, 4.0)
        self.pageUpdate('Бражка: Антипена<br>%s'%(self.Duration()), 'ABORT_NEXT.html')
        duration=60*float(config['PARAMETERS']['tA_F']['value'])
        while (time.time()-tBgn) < duration:
            # Вывести на дисплей состояние
            sec=int(duration-int(time.time()-tBgn))
            sec_str=u'{:02}:{:02}'\
               .format((sec//60)%60, sec%60)
            self.pageUpdate('Бражка: Антипена %s<br>%s'%(sec_str,self.Duration()))
            #PID-регулятор
            power.value=pidH(thermometers.getValue('Низ'))
            # При получении команды прервать процесс
            if app.config['AB_CON']=='Abort':
                self.abort()
                return
            elif app.config['AB_CON']=='Next':
                app.config['AB_CON']=''
                break
            #ждать завершение измерения температур
            thermometers.Tmeasured.wait()
            # Отдохнуть секундочку
            #time.sleep(1)

        """Вывод верха колонны на температурную полку"""
        #подать максимальную мощность
        power.value=250**2/config['PARAMETERS']['rTEH']['value']
        tBgn=time.time()        #фиксация времени начала этапа
        while True:
            # Вывести на дисплей состояние
            sec=int(time.time()-tBgn)
            sec_str=u'{:02}:{:02}'\
               .format((sec//60)%60, sec%60)
            self.pageUpdate('Бражка: Подогрев %s<br>%s'%(sec_str,self.Duration()))
            # При получении команды прервать процесс
            if app.config['AB_CON']=='Abort':
                self.abort()
                return
            elif app.config['AB_CON']=='Next':
                app.config['AB_CON']=''
                break
            if thermometers.boiling.wait(1) and thermometers.getObjT('Верх').boiling:
                break    #поймали закипание на верхнем термометре

        """Стабилизация колонны"""
        duration = 60   #Продолжительность этапа стабилизации
        tBgn=time.time()        #фиксация времени начала этапа
        self.pidD.setpoint = 64.0   #установить целевую температуру верха колонны
        self.pidD.reset()   #сбросить PID
        self.pidD(thermometers.getValue('Верх'))    #сделать первое вычисление PID
        while (time.time()-tBgn) < duration:
            #установить мощность, соответствующую температуре низа колонны
            power.value=config['PARAMETERS']['P_H2O']['value']-config['PARAMETERS']['Kp']['value']*\
                (config['PARAMETERS']['T_H2O']['value']-thermometers.getValue('Низ'))
            # Вывести на дисплей состояние
            sec=int(time.time()-tBgn)
            sec_str=u'{:02}:{:02}'\
               .format((sec//60)%60, sec%60)
            self.pageUpdate('Бражка: Cтабилизация %s<br>%s'%(sec_str,self.Duration()))
            # При получении команды прервать процесс
            if app.config['AB_CON']=='Abort':
                self.abort()
                return
            elif app.config['AB_CON']=='Next':
                app.config['AB_CON']=''
                break
            thermometers.Tmeasured.wait()   #ожидать следующего измерения температуры
            #рассчитать и установить охлаждение
            self.Deph.value = self.pidD(thermometers.getValue('Верх'))

        """ Отбор тела"""
        self.pageUpdate('Бражка: перегон<br><br>%s'%(self.Duration()), 'ABORT.html')
        self.pidD.setpoint = 66.6   #установить целевую температуру верха колонны
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
            #Tdeph=config['PARAMETERS']['Tdeph_H2O']['value']+config['PARAMETERS']['Kdeph']['value']*\
            #    (config['PARAMETERS']['T_H2O']['value']-thermometers.getValue('Низ'))
            #thermometers.setTtrigger('Дефлегматор',Tdeph)
            '''Мощность устанавливается предзахлёбная, рассчитывается по формуле:
            P=Pводы-Kp*(Tкип_воды-Tниз), где
            Pводы       -предзахлёбная мощность при кипении воды в кубе
            Kp          -коэффициент изменения мощности
            Tкип_воды   -температура низа колонны при кипении воды в кубе
            Tниз        -температура низа колонны
            '''
            power.value=config['PARAMETERS']['P_H2O']['value']-config['PARAMETERS']['Kp']['value']*\
                (config['PARAMETERS']['T_H2O']['value']-thermometers.getValue('Низ'))
            thermometers.Tmeasured.wait()   #ожидать следующего измерения температуры
            #рассчитать и установить охлаждение
            self.Deph.value = self.pidD(thermometers.getValue('Верх'))
            #Новый критерий завершения перегона
            if (thermometers.getValue('Середина')-thermometers.getValue('Верх'))/\
                (thermometers.getValue('Низ')-thermometers.getValue('Середина'))>2:
                break
            #завершение перегона по температуре низа колонны
            if thermometers.getValue('Низ')+1.0>config['PARAMETERS']['T_H2O']['value']:
                break

        """Охлаждение холодильников"""
        self.pageUpdate('Бражка: охлаждение<br><br>%s'%(self.Duration()), 'ABORT.html')
        self.Deph.stop  #остановить дефлегматор
        while True:
            #нажата кнопка Останов
            if app.config['AB_CON']=='Abort':
                self.abort()
                return
            # Освежить дисплей
            self.pageUpdate('Бражка: охлаждение<br><br>%s'%(self.Duration()))

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

