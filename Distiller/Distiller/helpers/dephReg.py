import threading
import time
from simple_pid import PID
from Distiller import config, thermometers, app
from Distiller.actuators.dephlegmator import DephRun



class DephReg(threading.Thread):
    u"""Класс-поток регулирования температуры верха колонны"""

    _Run = False

    def __init__(self):
        #пуск родительской инициализации
        super(DephReg, self).__init__()
        """Загрузка в PID-регулятор коэффициентов и уставки из конфига"""
        self.pidD = PID(config['PARAMETERS']['Kpd']['value'],\
           config['PARAMETERS']['Kid']['value'],\
          config['PARAMETERS']['Kdd']['value'],\
         setpoint=config['PARAMETERS']['Tdephlock']['value'])
        thermometers.setTtrigger('Верх', self.pidD.setpoint)
        """Установить пределы выхода PID-регулятора"""
        self.pidD.output_limits = (0, 100)
        self.Deph = DephRun()   #Bresenham-регулятор дефлегматора
        self.Deph.value=0   #отключить охлаждение дефлегматора


    def run(self):
        """Запуск цикла регулирования температуры дефлегматора"""
        self._Run = True
        # запустить регулятор дефлегматора
        self.Deph.start()
        while self._Run:
            '''цикл регулирования'''
            thermometers.Tmeasured.wait()   #ожидать следующего измерения температуры
            #dbLock.acquire()    #захватить управление текущему потоку
            #if thermometers.getValue('Дефлегматор') > thermometers.getTtrigger('Дефлегматор'):
            #    dephlegmator.On()
            #else:
            #    dephlegmator.Off()
            #dbLock.release()    #освободить другие потоки на выполнение
            '''Заново подгрузить коэффициенты (вдруг изменились)'''
            '''Если разность более, чем 5°C, ужесточить PID'''
            if thermometers.getValue('Верх')-thermometers.getTtrigger('Верх') > 5:
                self.pidD.tunings = (1000*config['PARAMETERS']['Kpd']['value'],\
                                  config['PARAMETERS']['Kid']['value'],\
                                  config['PARAMETERS']['Kdd']['value'])
            else:
                self.pidD.tunings = (config['PARAMETERS']['Kpd']['value'],\
                                  config['PARAMETERS']['Kid']['value'],\
                                  config['PARAMETERS']['Kdd']['value'])
            self.pidD.setpoint = thermometers.getTtrigger('Дефлегматор')
            #print(thermometers.getValue('Верх'), '->', thermometers.getTtrigger('Верх'))
            '''рассчитать и установить охлаждение'''
            PID_D = self.pidD(thermometers.getValue('Верх'))
            #print('Дефлегматор=', PID_D)
            self.Deph.value = PID_D
        self.Deph.value = 0
        self.Deph.stop()
        #dbLock.acquire()    #захватить управление текущему потоку
        #dephlegmator.Off()   #отключить охлаждение дефлегматора
        #dbLock.release()    #освободить другие потоки на выполнение

    @property
    def value(self):
        return thermometers.getTtrigger('Верх')
    @value.setter
    def value(self, value):
        if value < 0.0:
            __value = 0.0
        elif value > 100.0:
            __value = 100.0
        else:
            __value = value
        thermometers.setTtrigger('Верх', __value)


    def stop(self):
        """Останов регулирования"""
        #self.Deph.value = 0
        #self.Deph.stop()
        self._Run = False