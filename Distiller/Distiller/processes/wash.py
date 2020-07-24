"""
$Id: wash.py,v 1.3 2020/07/09 
 By C-Bell (VAGor).

Класс-поток перегонки бражки

"""
import time, os
from datetime import datetime
import threading
from flask import render_template
from Distiller import app, dbLock,config
from Distiller import power, condensator, dephlegmator, coolsRegulator, thermometers
from Distiller.helpers.transmitter import Transmit


class Wash(threading.Thread):
    u'''Класс, реализующий алгоритм перегонки бражки'''

    # Для сохранения состояния дисплея и кнопок
    Display = ''
    Buttons = ''

    def __init__(self):
        #threading.Thread.__init__(self)
        super(Wash, self).__init__()
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
        #Заполнение холодильников
        condensator.On()
        dephlegmator.On()
        time.sleep(2)
        condensator.Off()
        dephlegmator.Off()
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
        #установить мощность, соответствующую температуре низа колонны
        while True:
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

        ##балансировка колонны по температурам
        ## Новый набор кнопок
        #self.pageUpdate(None, 'ABORT_NEXT.html')
        ##подать максимальную мощность
        #power.value=250**2/config['PARAMETERS']['rTEH']
        #while (thermometers.getValue('Середина')-thermometers.getValue('Верх'))/\
        #        (thermometers.getValue('Низ')-thermometers.getValue('Середина'))>1:
        #    # Вывести на дисплей состояние
        #    self.pageUpdate('Бражка: ожидание закипания<br>'+self.Duration())
        #    # При получении команды прервать процесс
        #    if app.config['AB_CON']=='Abort':
        #        self.abort()
        #        return
        #    elif app.config['AB_CON']=='Next':
        #        app.config['AB_CON']=''
        #        break
        #    # Отдохнуть секундочку
        #    time.sleep(1)

        ## Выход низа на температурную полку
        #tBgn=time.time()        #фиксация времени начала ожидания
        #tBott=120    #длительность ожидания в сек
        ## Новый набор кнопок
        #self.pageUpdate(None, 'ABORT_NEXT.html')
        ##подать максимальную мощность
        #power.value=250**2/config['PARAMETERS']['rTEH']
        ##сравнение температур каждые 20 секунд
        #countSec=20
        #Tbott=thermometers.getValue('Низ')
        ## выдержка tBott секунд после закипания
        #while (time.time()-tBgn)<tBott:
        #    # Вывести на дисплей состояние
        #    sec=int(tBott-int(time.time()-tBgn))
        #    sec_str=u'{:02}:{:02}'\
        #       .format((sec//60)%60, sec%60)
        #    self.pageUpdate('Стабилизация Tниз<br>%s<br>%s'%
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


        #ожидание прогрева колонны 
        #power.value=5.0 #(max)
        #self.pageUpdate('Прогрев колонны<br>%s'%(self.Duration()))
        ##последовательно ожидать закипание на середине, затем наверху колонны
        #for i in range(2):
        #    while not thermometers.boiling.wait(0.5):
        #        self.pageUpdate('Прогрев колонны<br>%s'%(self.Duration()))
        #        # При получении команды прервать процесс
        #        if app.config['AB_CON']=='Abort':
        #            self.abort()
        #            return
        #        elif app.config['AB_CON']=='Next':
        #            app.config['AB_CON']=''
        #            break
        #        # Отдохнуть секундочку
        #        time.sleep(1)

        #стабилизация
        #power.value=config['PARAMETERS']['P_H2O']-config['PARAMETERS']['Kp']*\
        #        (config['PARAMETERS']['T_H2O']-thermometers.getValue('Низ'))
        #duration=60
        #tBgn=time.time()
        #while (time.time()-tBgn<duration):
        #    # Вывести на дисплей состояние
        #    sec=int(duration-int(time.time()-tBgn))
        #    sec_str=u'{:02}:{:02}'\
        #       .format((sec//60)%60, sec%60)
        #    self.pageUpdate('Бражка: стабилизация %s<br>%s'%(sec_str,self.Duration()))
        #    if app.config['AB_CON']=='Abort':
        #        self.abort()
        #        return
        #    elif app.config['AB_CON']=='Next':
        #        app.config['AB_CON']=''
        #        break
        #    # Отдохнуть секундочку
        #    time.sleep(1)

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
            Tdeph=config['PARAMETERS']['Tdeph_H2O']+config['PARAMETERS']['Kdeph']*\
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

