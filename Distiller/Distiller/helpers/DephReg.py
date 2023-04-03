import threading
from simple_pid import PID
from Distiller import config, thermometers
from Distiller.actuators.dephlegmator import DephRun

class DephReg(threading.Thread):
    u"""Класс-поток PID-регулирования температуры дефлегматора"""

    _Run = False

    def __init__(self):
        #пуск родительской инициализации
        super(DephReg, self).__init__()
        """Загрузка в PID-регулятор коэффициентов и уставки из конфига"""
        self.pidD = PID(config['PARAMETERS']['Kpd']['value'],\
           config['PARAMETERS']['Kid']['value'],\
          config['PARAMETERS']['Kdd']['value'],\
         setpoint=config['PARAMETERS']['Tdephlock']['value'])
        thermometers.setTtrigger('Дефлегматор', self.pidD.setpoint)
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
            #Заново подгрузить коэффициенты (вдруг изменились)
            self.pidD.tunings = (config['PARAMETERS']['Kpd']['value'],\
                              config['PARAMETERS']['Kid']['value'],\
                              config['PARAMETERS']['Kdd']['value'])
            self.pidD.setpoint = thermometers.getTtrigger('Дефлегматор')
            #print(thermometers.getValue('Дефлегматор'), '->', thermometers.getTtrigger('Дефлегматор'))
            #рассчитать и установить охлаждение
            PID_D = self.pidD(thermometers.getValue('Дефлегматор'))
            #print('Дефлегматор=', PID_D)
            self.Deph.value = PID_D
        self.Deph.value=0   #отключить охлаждение дефлегматора
        self.Deph.stop()

    def stop(self):
        """Останов регулирования"""
        self.Deph.value = 0
        self._Run = False