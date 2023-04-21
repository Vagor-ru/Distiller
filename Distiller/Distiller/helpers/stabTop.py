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
        self.pidT.output_limits = (30, 60)
        # Сохранить уставку
        self.__value = Tstab
        #thermometers.setTtrigger('Конденсатор', self.pidD.setpoint)

    def run(self):
        """Запуск цикла регулирования температуры конденсатора"""
        self._Run = True
        mult = 10   # множитель агрессии PID-регулятора для подвода к целевой температуре
        threshold = 2   #порог действия агрессии (град)
        while self._Run:
            '''цикл регулирования'''
            thermometers.Tmeasured.wait()   #ожидать следующего измерения температуры
            #рассчитать и установить необходимую для стабилизации температуру дефлегматора
            T = thermometers.getValue('Верх')
            if abs(self.value - T) < threshold:
                # подгрузить нормальные коэффициенты 
                self.pidT.tunings = (config['PARAMETERS']['Kpt']['value'],\
                                  config['PARAMETERS']['Kit']['value'],\
                                  config['PARAMETERS']['Kdt']['value'])
            else:
                # подгрузить агрессивные коэффициенты 
                self.pidT.tunings = (config['PARAMETERS']['Kpt']['value']*mult,\
                                  config['PARAMETERS']['Kit']['value']*mult,\
                                  config['PARAMETERS']['Kdt']['value']*mult)
            self.pidT.setpoint = self.value # уставка
            PID_T = self.pidT(T)            # расчитать PID
            #print(f"Tверх={T}, PID_T={PID_T}, Run={self._Run}")
            dbLock.acquire()    # захватить единоличный доступ
            # установить триггер верхнего термометра
            thermometers.setTtrigger('Дефлегматор', PID_T)
            dbLock.release()    # освободить доступ
        return

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
