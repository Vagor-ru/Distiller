"""
$Id: power.py,v 1.3 2020/07/07 

Класс-поток обеспечивает регулировку выдаваемый на ТЭН
мощности по алгоритму Брезенхема.

Регулировка мощности осуществляется последовательным включением/
отключением штырька HEATER_PIN, его номер прописан в файле config.py
"""

import time, threading  #Модули для работы со временем и потоками
from datetime import datetime
from Distiller import app, config, voltmeter

if app.config['RPI']:
    try:
        import RPi.GPIO as GPIO #Модуль доступа к GPIO Raspberry Pi
        ##Настройка по номеру штырька на плате (не номер GPIO)
        GPIO.setmode(GPIO.BOARD)    #по номеру штырьков на плате
    except Exception as exp:
        app.config['Display'] = 'Error: ' + str(exp)




class Power(threading.Thread):
    step=1         #Шаг установки мощности = 1%
    period=50.0    #Длительность преобразования Брезенхема (сек)

    def __init__(self):
        threading.Thread.__init__(self)
        self.HEATER_PIN=int(config['HEATER_PIN'])
        self._P=0
        self._Pa=0
        self._Run=False

    @property
    def value(self):
        return self._Pa

    @value.setter
    def value(self, value):
        try:
            value=float(value)
            if value<0:
                value=0.0
            if value>250**2/config['PARAMETERS']['rTEH']/1000:
                value=250**2/config['PARAMETERS']['rTEH']/1000
        except Exception as ex:
            print(ex)
            value=0.0
        new_P=value*100*config['PARAMETERS']['rTEH']*1000/(voltmeter.value**2)
        if new_P>100:
            self._P=100
            self._Pa=(voltmeter.value**2)/config['PARAMETERS']['rTEH']/1000
        else:
            self._P=new_P
            self._Pa=value
        app.config['Power']=self.dataFromServer

        #new_P=int((int((value+self.step/2)/self.step))*self.step)
        ## Если изменилось значение мощности, то отправить новое значение клиентам
        #if self._P!=new_P:
        #    self._P=new_P
        #    Transmit({'Power':[('Нагрев',self._P)], 'DateTime': time.time()})
        

    def run(self):
        """Реализация алгоритма Брезенхема
        для регулирования мощности ТЭНа"""
        if not app.config['RPI']:
            self._Run=True
            while self._Run:
                V=voltmeter.value
                if self._P==100:
                    self._Pa=(V**2)/config['PARAMETERS']['rTEH']/1000
                else:
                    self._P=self.value*100*config['PARAMETERS']['rTEH']*1000/(V**2)
                time.sleep(1)
            return
        #штырек HEATER_PIN на вывод, подтяжка отключена, низкий уровень
        GPIO.setup(self.HEATER_PIN, GPIO.OUT, GPIO.PUD_OFF, GPIO.LOW)
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
                    GPIO.output(self.HEATER_PIN, GPIO.HIGH)
                    #print('Power=ON')
                else:
                    pass
                    GPIO.output(self.HEATER_PIN, GPIO.LOW)
                    #print('Power=OFF')
                ErrP-=int(self._P/self.step)
                #print(GPIO.input(config.HEATER_PIN))
                if self._P==100:
                    self._Pa=(voltmeter.value**2)/config['PARAMETERS']['rTEH']/1000
                else:
                    self._P=self.value*100*config['PARAMETERS']['rTEH']*1000/(voltmeter.value**2)
                app.config['Power']=self._Pa
                time.sleep(self.period*self.step/100)
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
    HEATER_PIN=raw_input("Номер штырька регулирования мощности:")
    import Power
    power=Power()
    power.start()
    while True:
        End=raw_input("Значение мощности (0...100) или Enter для останова:")
        if End=="":
            power.stop()
            break
        try:
            power.value=(int(End))
            print("P=%s"%power.value)
        except ValueError:
            pass

if __name__=="__main__":
    try:
        main()
    finally:
        pass

