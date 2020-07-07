import threading
import time
import random   #Модуль случайных чисел
from Distiller import app, config

#если работаем на Raspberry Pi, подгружаем модуль
#для работы с шиной I2C в Python "python-smbus"
if app.config['RPI']:
    try:
        from smbus import SMBus
    except Exception as expSMBus:
        app.config['Display'] = 'Error: ' + str(expSMBus)

class Voltmeter(threading.Thread):
    """Класс обеспечивает измерение напряжения сети 220V
    с помощью АЦП модуля PCF8591"""
    def __init__(self):
        super(Voltmeter, self).__init__()
        self._V=220.0
        self._Run=False

    @property
    def value(self):
        return self._V

    def run(self):
        self._Run=True
        while(True):
            if not self._Run:
                break
            self._V=self.GetVoltage()
            app.config['Voltmeter']=self._V
            time.sleep(0.5)

    def stop(self):
        self._Run=False

    def GetVoltage(self):
        if app.config['RPI']:
            return self.MeasureVoltage()
        else:
            return self.EmulateVoltage()

    def MeasureVoltage(self):
        SMBus(1).write_byte(config['ADC_ADDR'], 0b1000010)
        SMBus(1).read_byte(config['ADC_ADDR']) # read last value
        SMBus(1).read_byte(config['ADC_ADDR']) # repeat reading last value
        return round(config['PARAMETERS']['K_V']*SMBus(1).read_byte(config['ADC_ADDR']))

    def EmulateVoltage(self):
        return round(210+random.random()*20)


