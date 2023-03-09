import threading
from simple_pid import PID
from Distiller import config, thermometers
from Distiller.actuators.dephlegmator import DephRun

class DephReg(threading.Thread):
    u"""Класс-поток PID-регулирования температуры верха колонны"""

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
        """Запуск цикла регулирования температуры верха колонны"""
        self._Run = True
        while self._Run:
            '''цикл регулирования'''
            thermometers.Tmeasured.wait()   #ожидать следующего измерения температуры
            #Заново подгрузить коэффициенты (вдруг изменились)
            self.pidD.tunings = (config['PARAMETERS']['Kpd']['value'],\
                              config['PARAMETERS']['Kid']['value'],\
                              config['PARAMETERS']['Kdd']['value'])
            self.pidD.setpoint = thermometers.getTtrigger('Верх')
            print(thermometers.getValue('Верх'), '->', thermometers.getTtrigger('Верх'))
            #рассчитать и установить охлаждение
            self.Deph.value = self.pidD(thermometers.getValue('Верх'))
        self.Deph.value=0   #отключить охлаждение дефлегматора
        self.Deph.stop()

    def stop(self):
        """Останов регулирования"""
        self._Run = False