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
from Distiller.helpers.stabTop import StabTop
from Distiller.helpers.log import Logging



class Crude(threading.Thread):
    u'''Класс, реализующий алгоритм перегонки спирта-сырца'''

    # Для сохранения состояния дисплея и кнопок
    Display = ''
    Buttons = ''
    Stab_Top = StabTop()

    def __init__(self):
        #threading.Thread.__init__(self)
        super(Crude, self).__init__()
        self.log = Logging('Crude')
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
        # Вывести сообщение на дисплей и прикрутить кнопку "Останов"
        self.pageUpdate('Заполнение холодильников<br>'+self.Duration(),
                        'ABORT.html')
        self.log.start()    #старт записи лога


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


        '''Ожидание закипания'''
        #Мощность нагрева=100%
        power.value=250**2/config['PARAMETERS']['rTEH']['value']
        while not thermometers.boiling.wait(1):
            # Вывести на дисплей состояние
            self.pageUpdate('2-й перегон: ожидание закипания<br>'+self.Duration())
            # При получении команды прервать процесс
            if app.config['AB_CON']=='Abort':
                self.abort()
                return


        '''прогрев колонны'''
        #tBgn=time.time()
        #duration=10
        ## Новый набор кнопок
        #self.pageUpdate(None, 'ABORT_NEXT.html')
        #while time.time()-tBgn<duration:
        #    # Вывести на дисплей состояние
        #    sec=int(duration-int(time.time()-tBgn))
        #    sec_str=u'{:02}:{:02}'\
        #       .format((sec//60)%60, sec%60)
        #    self.pageUpdate('2-й перегон: прогрев колонны %s<br>%s'%(sec_str,self.Duration()))
        #    # При получении команды прервать процесс
        #    if app.config['AB_CON']=='Abort':
        #        self.abort()
        #        return
        #    # переход к отбору голов
        #    if app.config['AB_CON']=='Next':
        #        app.config['AB_CON']=''
        #        break
        #    time.sleep(1)


        '''Отбор голов'''
        # Новый набор кнопок
        self.pageUpdate(None, 'ABORT_NEXT.html')
        # запустить поток стабилизации температуры верха колонны
        self.Stab_Top.start()
        tBgn=time.time()        #фиксация времени начала отбора голов
        #установка триггера дефлегматора
        #Tdeph=46.3
        #thermometers.setTtrigger('Дефлегматор',Tdeph)
        while True:
            '''Цикл отбора голов'''
            #установить порог срабатывания клапана конденсатора из конфига
            thermometers.setTtrigger('Конденсатор',config['PARAMETERS']['Tcond']['value'])
            # установить температуру стабилизации верха колонны
            self.Stab_Top.value = config['PARAMETERS']['T_Head']['value']
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

        '''Отбор тела'''
        self.pageUpdate('2-й перегон: тело<br><br>%s'%(self.Duration()), 'ABORT_NEXT.html')
        count_end = 0
        while True:
            '''Цикл отбора тела'''
            #установить порог срабатывания клапана конденсатора из конфига
            thermometers.setTtrigger('Конденсатор',config['PARAMETERS']['Tcond']['value'])
            # установить температуру стабилизации верха колонны
            self.Stab_Top.value = config['PARAMETERS']['T_Body']['value']
            # При получении команды прервать процесс
            if app.config['AB_CON']=='Abort':
                self.abort()
                return
            # переход к отбору тела
            if app.config['AB_CON']=='Next':
                app.config['AB_CON']=''
                break
            if app.config['AB_CON']=='Abort':
                self.abort()
                return
            # Освежить дисплей
            self.pageUpdate('2-й перегон тело<br><br>%s'%(self.Duration()))
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
            #Новый критерий завершения перегона по температуре затворения дефлегматора
            if thermometers.getTtrigger("Дефлегматор") < config['PARAMETERS']["Tdephlock"]["value"]:
                count_end += 1
                if count_end > 15:
                    break
            else:
                """сброс числа обнаружения критериев"""
                count_end = 0
            # Критерий завершения по соотношению температур
            #if (thermometers.getValue('Середина')-thermometers.getValue('Верх'))/\
            #    (thermometers.getValue('Низ')-thermometers.getValue('Середина'))>5.7:
            #    break
            #завершение перегона по температуре низа колонны
            if thermometers.getValue('Низ')+1.0>config['PARAMETERS']['T_H2O']['value']:
                break
            #ждать завершение измерения температур
            thermometers.Tmeasured.wait()


        '''Отбор хвостов'''
        self.pageUpdate('2-й перегон: тело<br><br>%s'%(self.Duration()), 'ABORT_NEXT.html')
        count_end = 0
        while True:
            '''Цикл отбора тела'''
            #установить порог срабатывания клапана конденсатора из конфига
            thermometers.setTtrigger('Конденсатор',config['PARAMETERS']['Tcond']['value'])
            # установить температуру стабилизации верха колонны
            self.Stab_Top.value = config['PARAMETERS']['T_Tails']['value']
            if app.config['AB_CON']=='Abort':
                self.abort()
                return
            # Освежить дисплей
            self.pageUpdate('2-й перегон тело<br><br>%s'%(self.Duration()))
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
            #Новый критерий завершения перегона по температуре затворения дефлегматора
            if thermometers.getTtrigger("Дефлегматор") < config['PARAMETERS']["Tdephlock"]["value"]:
                count_end += 1
                if count_end > 15:
                    break
            else:
                """сброс числа обнаружения критериев"""
                count_end = 0
            # Критерий завершения по соотношению температур
            #if (thermometers.getValue('Середина')-thermometers.getValue('Верх'))/\
            #    (thermometers.getValue('Низ')-thermometers.getValue('Середина'))>5.7:
            #    break
            #завершение перегона по температуре низа колонны
            if thermometers.getValue('Низ')+1.0>config['PARAMETERS']['T_H2O']['value']:
                break
            #ждать завершение измерения температур
            thermometers.Tmeasured.wait()


        # установить температуру стабилизации верха колонны
        self.Stab_Top.value = config['PARAMETERS']['T_Body']['value']
        self.Stab_Top.stop()



        """Охлаждение холодильников"""
        self.pageUpdate('Охлаждение колонны<br><br>%s'%(self.Duration()), 'ABORT.html')
        power.value = 0 #отключить нагрев
        tBgn=time.time()        #фиксация времени начала этапа
        while (time.time()-tBgn) < 60:
            #нажата кнопка Останов
            if app.config['AB_CON']=='Abort':
                self.abort()
                return
            #установить порог срабатывания клапана конденсатора 15°C
            thermometers.setTtrigger('Конденсатор',15)
            #установить целевую температуру дефлегматора
            thermometers.setTtrigger('Дефлегматор',15)
            # Освежить дисплей
            self.pageUpdate('Охлаждение колонны<br><br>%s'%(self.Duration()))
            # Отдохнуть секундочку
            time.sleep(1)
        #установить нормальный порог срабатывания клапана конденсатора
        thermometers.setTtrigger('Конденсатор', config['PARAMETERS']['Tcond']['value'])
        #установить целевую температуру затворения дефлегматора
        thermometers.setTtrigger('Дефлегматор', config['PARAMETERS']['Tdephlock']['value'])


        '''Остановить всё'''
        self.stop()
        self.pageUpdate('Второй перегон завершен<br>%s'%(self.Duration()),
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
