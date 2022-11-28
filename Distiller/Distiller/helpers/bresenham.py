class Bresenham(object):
    """Реализует распределение заданного количества квантов по определённому диапазону"""

    def __init__(self, range=100, value=0):
        """Конструктор класса bresenham"""
        self.__range, self.__value = 100, 0
        self.range, self.value = range, value
        self.reset()

    def __call__(self, value=None):
        """реализация алгоритма брезенхема, устанавливает и возвращает требуемое значение текущего кванта,
           можно задать необходимое значение, если не задать, используется предыдущее"""
        if not value is None:
            self.value = value
        if self.__error < self.range/2:
            self.__error += self.range
            self.__quantum = True
        else:
            self.__quantum = False
        self.__error -= self.value
        self.__step += 1
        if self.__step >= self.range:
            self.__step = 0
            self.__error = self.range-self.value
        return self.__quantum

    @property
    def range(self):
        '''Диапазон, в котором распределяются кванты'''
        return self.__range
    @range.setter
    def range(self, range):
        '''Установка диапазона, в котором распределяются кванты'''
        if range <= 0:
            self.__range = 1
        else:
            self.__range = int(range)

    @property
    def value(self):
        '''Количество квантов в диапазоне'''
        return self.__value
    @value.setter
    def value(self, value):
        '''Установка количества квантов в диапазоне'''
        if value < 0:
            self.__value = 0
        elif value > self.range:
            self.__value = self.range
        else:
            self.__value = int(value)

    @property
    def quantum(self):
        '''Состояние текущего кванта (включен/выключен)'''
        return self.__quantum

    def reset(self):
        '''Сброс алгоритма к началу диапазона'''
        self.__step=0
        self.__error=self.range-self.value
        self.__quantum = False



