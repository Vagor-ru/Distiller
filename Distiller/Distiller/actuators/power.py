"""
$Id: power.py,v 1.3 2017/05/13 

Класс-поток обеспечивает регулировку выдаваемый на ТЭН
мощности по алгоритму Брезенхема.

Регулировка мощности осуществляется последовательным включением/
отключением штырька HEADER_PIN, его номер прописан в файле config.py
"""

import time, threading  #Модули для работы со временем и потоками
from datetime import datetime
#import RPi.GPIO as GPIO #Модуль доступа к GPIO Raspberry Pi
from Distiller import app
from Distiller.helpers.transmitter import Transmit



##Настройка по номеру штырька на плате (не номер GPIO)
#GPIO.setmode(GPIO.BOARD)    #по номеру штырьков на плате

class Power(threading.Thread):
    step=1         #Шаг установки мощности = 1%
    period=50.0    #Длительность преобразования Брезенхема (сек)

    def __init__(self):
        threading.Thread.__init__(self)
        self.HEADER_PIN=int(app.config['HEADER_PIN'])
        self._P=0
        self._Run=False

    @property
    def Value(self):
        return self._P

    @Value.setter
    def Value(self, value):
        try:
            value=int(value)
        except:
            value=0
        if value<0:
            value=0
        if value>100:
            value=100
        new_P=int((int((value+self.step/2)/self.step))*self.step)
        # Если изменилось значение мощности, то отправить новое значение клиентам
        if self._P!=new_P:
            self._P=new_P
            Transmit({'Power':[('Нагрев',self._P)], 'DateTime': time.time()})
        

    def run(self):
        """Реализация алгоритма Брезенхема
        для регулирования мощности ТЭНа"""
        #штырек HEADER_PIN на вывод, подтяжка отключена, низкий уровень
        #GPIO.setup(self.HEADER_PIN, GPIO.OUT, GPIO.PUD_OFF, GPIO.LOW)
        self._Run=True
        while self._Run:
            Pmax=int((100/self.step))    #Приведенная максимальная мощность
            #Pwr=int(self._P/self.step)
            ErrP=Pmax-int(self._P/self.step)
            for x in range(Pmax):
                if not self._Run:
                    break
                if ErrP<Pmax/2:
                    ErrP+=Pmax
                    #GPIO.output(self.HEADER_PIN, GPIO.HIGH)
                    #print('Power=ON')
                else:
                    pass
                    #GPIO.output(self.HEADER_PIN, GPIO.LOW)
                    #print('Power=OFF')
                ErrP-=int(self._P/self.step)
                #print(GPIO.input(config.HEADER_PIN))
                time.sleep(self.period*self.step/100)
            #GPIO.output(self.HEADER_PIN, GPIO.LOW)
            print('Power=OFF')
        #GPIO.cleanup(self.HEADER_PIN)
        #print('штырек HEADER_PIN освобожден')

    def stop(self):
        self.Value=0
        self._Run=False

    @property
    def DataFromServer(self):
        return {'Power':[('Нагрев',self._P)]}

        


def main():
    """Ручная установка мощности и тестовое преобразование"""
    HEADER_PIN=raw_input("Номер штырька регулирования мощности:")
    import power
    power=Power()
    power.start()
    while True:
        End=raw_input("Значение мощности (0...100) или Enter для останова:")
        if End=="":
            power.stop()
            break
        try:
            power.Value=(int(End))
            print("P=%s"%power.Value)
        except ValueError:
            pass

if __name__=="__main__":
    try:
        main()
    finally:
        pass

