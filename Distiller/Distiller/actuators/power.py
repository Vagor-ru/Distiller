"""
$Id: power.py,v 1.3 2020/07/07 

Класс-поток обеспечивает регулировку выдаваемый на ТЭН
мощности по алгоритму Брезенхема.

Регулировка мощности осуществляется последовательным включением/
отключением штырька HEATER_PIN, его номер прописан в файле config.py
"""

import time, threading  #Модули для работы со временем и потоками
from Distiller import app, config, voltmeter
from Distiller.helpers.transmitter import Transmit
from Distiller.helpers.bresenham import Bresenham


if app.config['RPI']:
    try:
        import RPi.GPIO as GPIO #Модуль доступа к GPIO Raspberry Pi
        ##Настройка по номеру штырька на плате (не номер GPIO)
        GPIO.setmode(GPIO.BOARD)    #по номеру штырьков на плате
    except Exception as exp:
        app.config['Display'] = 'Error: ' + str(exp)




class Power(threading.Thread):
    '''Класс-поток регулирования мощности нагрева'''
    step=1         #Шаг установки мощности = 1%
    period=50.0    #Длительность преобразования Брезенхема (сек)
    _Run=False

    def __init__(self):
        #threading.Thread.__init__(self)
        super(Power, self).__init__()
        self.HEATER_PIN=int(config['HEATER_PIN']['number'])
        self.Bresenham = Bresenham()
        self._Pa=0
        self._Pmax=voltmeter.value**2/config['PARAMETERS']['rTEH']['value']/1000
        

    @property
    def Pmax(self):
        '''Текущая максимальная мощность в кВт
        (зависит от напряжения сети питания и
        сопротивления нагревателя)'''
        return self._Pmax

    @property
    def value(self):
        '''значение заданной мощности в кВт'''
        return self._Pa
    @value.setter
    def value(self, value):
        '''установка мощности в кВт'''
        if value<0:
            self._Pa = 0.0
        elif value > self._Pmax:
            self._Pa = self._Pmax
        else:
            self._Pa = float(value)
        self.Bresenham.value = self.Bresenham.range*self.value/self.Pmax
        app.config['Power']=self.dataFromServer
        Transmit(self.dataFromServer)

    def run(self):
        """Поток регулирования мощности ТЭНа по алгоритму Брезенхема"""
        if not app.config['RPI']:
            self._Run=True
            while self._Run:
                V=voltmeter.value
                if self.value >= self.Pmax:
                    self._Pmax = self.value = V**2/config['PARAMETERS']['rTEH']['value']/1000
                    Transmit(self.dataFromServer)
                else:
                    self._Pmax = V**2/config['PARAMETERS']['rTEH']['value']/1000
                self.Bresenham.value = self.Bresenham.range*self.value/self.Pmax
                time.sleep(1)
            return
        #штырек HEATER_PIN на вывод, подтяжка отключена, низкий уровень
        GPIO.setup(self.HEATER_PIN, GPIO.OUT, GPIO.PUD_OFF, GPIO.LOW)
        self._Run=True
        while self._Run:
            V=voltmeter.value
            if self.value >= self.Pmax:
                self._Pmax = self.value = V**2/config['PARAMETERS']['rTEH']['value']/1000
                Transmit(self.dataFromServer)
            else:
                self._Pmax = V**2/config['PARAMETERS']['rTEH']['value']/1000
            #self.Bresenham.value = self.Bresenham.range*self.value/self.Pmax
            GPIO.output(self.HEATER_PIN, self.Bresenham(self.Bresenham.range*self.value/self.Pmax))
            time.sleep(1)
        GPIO.output(self.HEATER_PIN, GPIO.LOW)
        #print('Power=OFF')
        GPIO.cleanup(self.HEATER_PIN)
        #print('штырек HEATER_PIN освобожден')

    def stop(self):
        self.value=0
        self._Run=False

    @property
    def dataFromServer(self):
        return {'Power':[('Нагрев',self._Pa)]}



def main():
    """Ручная установка мощности и тестовое преобразование"""
    pass

if __name__=="__main__":
    try:
        main()
    finally:
        pass

