import time, threading  #Модули для работы со временем и потоками
from Distiller import condensator
from Distiller.helpers.bresenham import Bresenham

class CondRun(threading.Thread):
    """Класс-поток регулирования интенсивности охлаждения конденсатора
   с использованием алгоритма Брезенхема"""

    def __init__(self, value=0):
        """Конструктор регулятора конденсатора"""
        super(CondRun, self).__init__()
        self.Bresenham = Bresenham()
        condensator.Off()
        self.__value = 0
        self.value = value
        self._Run = False

    def run(self):
        """Запуск цикла регулирования охлаждения конденсатора"""
        self._Run = True
        while self._Run:
            #print('Сейчас Bresenham будет расчитан.')
            if self.Bresenham(self.value):
                condensator.On()
            else:
                condensator.Off()
            time.sleep(0.1)
        condensator.Off()

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



