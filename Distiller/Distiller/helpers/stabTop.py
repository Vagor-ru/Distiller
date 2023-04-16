import threading
from simple_pid import PID
from Distiller import config, thermometers, dbLock
#from Distiller.actuators.condensator import CondRun

class StabTop(threading.Thread):
    u"""Класс-поток PID-стабилизации температуры верха колонны"""

    # сбросить флаг запуска
    _Run = False

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
        self.pidT.output_limits = (30, 65)
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
            dbLock.acquire()    # захватить единоличный доступ
            #рассчитать и установить необходимую для стабилизации температуру дефлегматора
            T = thermometers.getValue('Верх')
            PID_T = self.pidT(T)
            #print(f"Tверх={T}, PID_T={PID_T}, Run={self._Run}")
            thermometers.setTtrigger('Дефлегматор', PID_T)
            dbLock.release()    # освободить доступ


    def stop(self):
        """Останов регулирования"""
        self._Run = False
        #print(f"__Run={self._Run}")

    def reset(self):
        self.pidT.reset()

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
