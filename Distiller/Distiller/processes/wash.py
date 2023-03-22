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
from Distiller.helpers.log import Logging

class Wash(threading.Thread):
    u'''Класс, реализующий алгоритм перегонки бражки'''

    # Для сохранения состояния дисплея и кнопок
    Display = ''
    Buttons = ''

    def __init__(self):
        #threading.Thread.__init__(self)
        super(Wash, self).__init__()
        self._Begin=time.time()
        self.log = Logging('Wash')

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
        # Вывести сообщение на дисплей и прикрутить кнопку "Останов"
        self.pageUpdate('Заполнение холодильников<br>'+self.Duration(),
                        'ABORT.html')
        self.log.start()

        #Заполнение холодильников
        tBgn=time.time()        #фиксация времени начала заполнения
        #установить порог срабатывания клапана конденсатора 15°C
        thermometers.setTtrigger('Конденсатор',15)
        #установить температуру удержания Дефлегматора
        thermometers.setTtrigger('Дефлегматор', 15)
        while (time.time()-tBgn) < config['PARAMETERS']['tFillCoolers']['value']:
            '''цикл заполнения холодильников'''
            # При получении команды прервать процесс
            if app.config['AB_CON']=='Abort':
                self.abort()
                return
            elif app.config['AB_CON']=='Next':
                app.config['AB_CON']=''
                break
            # Отдохнуть секундочку
            time.sleep(1)
        #установить порог срабатывания клапана конденсатора из конфига
        thermometers.setTtrigger('Конденсатор',config['PARAMETERS']['Tcond']['value'])
        thermometers.setTtrigger('Дефлегматор',config['PARAMETERS']['Tdephlock']['value'])

        """Ожидание закипания"""
        #Мощность нагрева=100%
        power.value=power.Pmax
        while not thermometers.boiling.wait(1):
            # Вывести на дисплей состояние
            self.pageUpdate('Бражка: Нагрев<br>'+self.Duration())
            # При получении команды прервать процесс
            if app.config['AB_CON']=='Abort':
                self.abort()
                return

        """Пауза в 15 секунд для прогрева низа колонны"""
        tBgn=time.time()        #фиксация времени начала паузы
        while (time.time()-tBgn) < 15:
            self.pageUpdate('Бражка: Нагрев - пауза<br>'+self.Duration())
            # При получении команды прервать процесс
            if app.config['AB_CON']=='Abort':
                self.abort()
                return
            # Отдохнуть секундочку
            time.sleep(1)
        power.value=0   #отключить нагрев

        """Пауза в 15 секунд инерции нагрева низа колонны"""
        tBgn=time.time()        #фиксация времени начала паузы
        while (time.time()-tBgn) < 15:
            self.pageUpdate('Бражка: Пауза<br>'+self.Duration())
            # При получении команды прервать процесс
            if app.config['AB_CON']=='Abort':
                self.abort()
                return
            # Отдохнуть секундочку
            time.sleep(1)

        """Антипена"""
        tBgn=time.time()        #фиксация времени начала стабилизации
        #PID-регулятор температуры низа колонны (сразу фиксируется температура низа колонны)
        pidH = PID(config['PARAMETERS']['Kph']['value'],\
           config['PARAMETERS']['Kih']['value'],\
          config['PARAMETERS']['Kdh']['value'],\
         setpoint=thermometers.getValue('Низ'))
        #Установка диапазона рассчитываемой PID-регулятором мощности
        #print('МаксиМощь=', power.Pmax)
        pidH.output_limits = (0, power.Pmax)
        pidH.reset()
        self.pageUpdate('Бражка: Антипена<br>%s'%(self.Duration()), 'ABORT_NEXT.html')
        duration=60*float(config['PARAMETERS']['tA_F']['value'])
        while (time.time()-tBgn) < duration:
            # Вывести на дисплей состояние
            sec=int(duration-int(time.time()-tBgn))
            sec_str=u'{:02}:{:02}'\
               .format((sec//60)%60, sec%60)
            self.pageUpdate('Бражка: Антипена<br>%s %s<br>%s'%(pidH.setpoint, sec_str, self.Duration()))
            #установка коэффициентов PID-регулятора (на случай, если во время антипены их кто поменял)
            pidH.tunings = (config['PARAMETERS']['Kph']['value'],\
               config['PARAMETERS']['Kih']['value'],\
              config['PARAMETERS']['Kdh']['value'])
            #расчёт PID-регулятором необходимой мощности для поддержания температуры низа колонны
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

        """Прогрев колонны"""
        #подать максимальную мощность
        power.value=power.Pmax
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
                thermometers.values
                break    #поймали закипание на верхнем термометре
            if thermometers.getValue('Верх') > thermometers.getTtrigger('Верх'):
                break    #выше не нужно
        power.value=0   #отключить нагрев

        """Стабилизация колонны"""
        duration = 60   #Продолжительность этапа стабилизации (сек)
        tBgn=time.time()        #фиксация времени начала этапа
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
            #Заново подгрузить коэффициенты PID-регулятора дефлегматора (вдруг изменились)
            thermometers.setTtrigger('Дефлегматор',config['PARAMETERS']['T_Head']['value'])
            # Отдохнуть секундочку
            time.sleep(1)

        """ Отбор тела"""
        self.pageUpdate('Бражка: перегон<br><br>%s'%(self.Duration()), 'ABORT.html')
        #установить целевую температуру дефлегматора на отбор тела
        thermometers.setTtrigger('Дефлегматор', config['PARAMETERS']['T_Body']['value'])
        count_end = 0
        while True:
            #нажата кнопка Останов
            if app.config['AB_CON']=='Abort':
                self.abort()
                return
            # Освежить дисплей
            self.pageUpdate('Бражка: перегон<br><br>%s'%(self.Duration()))
            # Регулировать нагрев
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
            #Новый критерий завершения перегона
            if (thermometers.getValue('Середина')-thermometers.getValue('Верх'))/\
                (thermometers.getValue('Низ')-thermometers.getValue('Середина'))>2:
                count_end += 1
                if count_end > 15:
                    break
            else:
                """сброс числа обнаружения критериев"""
                count_end = 0
            #завершение перегона по температуре низа колонны
            if thermometers.getValue('Низ')+1.0>config['PARAMETERS']['T_H2O']['value']:
                break

        """Охлаждение холодильников"""
        self.pageUpdate('Охлаждение колонны<br><br>%s'%(self.Duration()), 'ABORT.html')
        power.value = 0 #отключить нагрев
        #установить порог срабатывания клапана конденсатора 15°C
        thermometers.setTtrigger('Конденсатор',15)
        #установить целевую температуру дефлегматора
        thermometers.setTtrigger('Дефлегматор',15)
        tBgn=time.time()        #фиксация времени начала этапа
        while (time.time()-tBgn) < 60:
            #нажата кнопка Останов
            if app.config['AB_CON']=='Abort':
                self.abort()
                return
            # Освежить дисплей
            self.pageUpdate('Охлаждение колонны<br><br>%s'%(self.Duration()))
            # Отдохнуть секундочку
            time.sleep(1)
        #установить нормальный порог срабатывания клапана конденсатора
        thermometers.setTtrigger('Конденсатор', config['PARAMETERS']['Tcond']['value'])
        #установить целевую температуру затворения дефлегматора
        thermometers.setTtrigger('Дефлегматор', config['PARAMETERS']['Tdephlock']['value'])

        # Остановить всё
        self.stop()
        self.pageUpdate('Перегон бражки завершен<br>%s'%(self.Duration()),
                        'END.html')
        return

    def stop(self):
        power.value = 0 #отключаем нагрев
        condensator.Off()   #отключаем клапан конденсатора
        dephlegmator.Off()  #отключаем клапан дефлегматора
        self.log.stop()     #остановить лог

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

