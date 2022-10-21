import time, threading  #Модули для работы со временем и потоками
from Distiller import app, config
from Distiller.helpers.bresenham import Bresenham
from Distiller.actuators.cools import Dephlegmator

class DephRun(threading.Thread):
    """Класс-поток регулирования интенсивности охлаждения дефлегматора с использованием алгоритма Брезенхема"""

    def __init__(self, value=0):
        """Конструктор дефлегматора"""
        self.Bresenham = Bresenham()
        self.Dephlegmator = Dephlegmator()
        self.__value = 0
        self.value = value
        self._Run = False

    def run(self):
        """Цикл регулирования"""
        self._Run = True
        while self._Run:
            self.Dephlegmator.State = self.Bresenham(self.value)
            #if self.Dephlegmator.State:
            #    print("1")
            #else:
            #    print("0")
            time.sleep(1)
        self.Dephlegmator.State = False

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


