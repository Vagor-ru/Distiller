
import threading
from simple_pid import PID
from Distiller import config, thermometers
from Distiller.actuators.condensator import CondRun

class CondReg(threading.Thread):
    u"""Класс-поток PID-регулирования температуры конденсатора"""

    def __init__(self):
        #пуск родительской инициализации
        super(CondReg, self).__init__()
        """Загрузка в PID-регулятор коэффициентов и уставки из конфига"""
        self.pidD = PID(config['PARAMETERS']['Kpc']['value'],\
           config['PARAMETERS']['Kic']['value'],\
          config['PARAMETERS']['Kdc']['value'],\
         setpoint=config['PARAMETERS']['Tcond']['value'])
        thermometers.setTtrigger('Конденсатор', self.pidD.setpoint)
        """Установить пределы выхода PID-регулятора"""
        self.pidD.output_limits = (0, 100)
        self.Cond = CondRun()   #Bresenham-регулятор конденсатора
        self.Cond.value=0   #отключить охлаждение конденсатора


    def run(self):
        """Запуск цикла регулирования температуры конденсатора"""
        self._Run = True
        # запустить регулятор конденсатора
        self.Cond.start()
        while self._Run:
            '''цикл регулирования'''
            thermometers.Tmeasured.wait()   #ожидать следующего измерения температуры
            #Заново подгрузить коэффициенты (вдруг изменились)
            self.pidD.tunings = (config['PARAMETERS']['Kpc']['value'],\
                              config['PARAMETERS']['Kic']['value'],\
                              config['PARAMETERS']['Kdc']['value'])
            self.pidD.setpoint = thermometers.getTtrigger('Конденсатор')
            #print(thermometers.getValue('Дефлегматор'), '->', thermometers.getTtrigger('Дефлегматор'))
            #рассчитать и установить охлаждение
            PID_D = self.pidD(thermometers.getValue('Конденсатор'))
            #print('Дефлегматор=', PID_D)
            self.Cond.value = PID_D
        self.Cond.value=0   #отключить охлаждение дефлегматора
        self.Cond.stop()

    def stop(self):
        """Останов регулирования"""
        self._Run = False