import threading
from simple_pid import PID
from Distiller import config, thermometers, cond_Reg
#from Distiller.actuators.condensator import CondRun

class StabTop(threading.Thread):
    u"""Класс-поток PID-стабилизации температуры верха колонны"""

    def __init__(self, Tstab=config['PARAMETERS']['T_Head']['value']):
        '''Инициализация объекта-потока PID-стабилизации температуры верха колонны'''
        # пуск родительской инициализации
        super(StabTop, self).__init__()
        # Загрузка в PID-регулятор коэффициентов и уставки из конфига
        self.pidT = PID(config['PARAMETERS']['Kpt']['value'],\
            config['PARAMETERS']['Kit']['value'],\
            config['PARAMETERS']['Kdt']['value'],\
            setpoint=Tstab)
        # Установить пределы выхода PID-регулятора
        self.pidT.output_limits = (40, 70)
        # Сохранить уставку
        self.__value = Tstab
        #thermometers.setTtrigger('Конденсатор', self.pidD.setpoint)

    def run(self):
        """Запуск цикла регулирования температуры конденсатора"""
        self._Run = True
        while self._Run:
            '''цикл регулирования'''
            thermometers.Tmeasured.wait()   #ожидать следующего измерения температуры
            #Заново подгрузить коэффициенты (вдруг изменились)
            self.pidT.tunings = (config['PARAMETERS']['Kpt']['value'],\
                              config['PARAMETERS']['Kit']['value'],\
                              config['PARAMETERS']['Kdt']['value'])
            self.pidT.setpoint = self.value
            #рассчитать и установить необходимую для стабилизации температуру дефлегматора
            thermometers.setTtrigger('Верх', self.pidT(thermometers.getValue('Верх')))

    def stop(self):
        """Останов регулирования"""
        self._Run = False

    @property
    def value(self):
        return self.__value
    @value.setter
    def value(self, value):
        if value < 50:
            self.__value = 50
        elif value > 100:
            self.__value = 100
        else:
            self.__value = value
