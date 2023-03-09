import time, threading  #Модули для работы со временем и потоками
from Distiller import app, config, dephlegmator
from Distiller.helpers.bresenham import Bresenham
from Distiller.actuators.cools import Dephlegmator

class DephRun(threading.Thread):
    """Класс-поток регулирования интенсивности охлаждения дефлегматора с использованием алгоритма Брезенхема"""

    def __init__(self, value=0):
        """Конструктор дефлегматора"""
        super(DephRun, self).__init__()
        self.Bresenham = Bresenham()
        #self.Dephlegmator = Dephlegmator()
        dephlegmator.Off()
        self.__value = 0
        self.value = value
        self._Run = False

    def run(self):
        """Запуск цикла регулирования охлаждения дефлегматора"""
        self._Run = True
        while self._Run:
            #print('Сейчас Bresenham будет расчитан.')
            if self.Bresenham(self.value):
                dephlegmator.On()
            else:
                dephlegmator.Off()
            #if self.Dephlegmator.State:
            #    print("1")
            #else:
            #    print("0")
            time.sleep(1)
        dephlegmator.Off()

    @property
    def value(self):
        return self.__value
    @value.setter
    def value(self, value):
        if value < 0:
            self.__value = 0
        elif value > 100:
            self.__value = 100
        else:
            self.__value = int(value)
        self.Bresenham.value = self.__value

    def stop(self):
        self.value = 0
        self._Run = False


