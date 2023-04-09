import threading
import time
import random   #Модуль случайных чисел
from Distiller import app, config
from Distiller.helpers.transmitter import Transmit

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

    # Событие готовности результатов измерения напряжения сети
    VoltReady = threading.Event()

    def __init__(self):
        super(Voltmeter, self).__init__()
        self._V=self.GetVoltage()   # Первое измерение
        self._Run=False             # Пока скинуть флаг запуска
        self.VoltReady.clear()      # Скинуть флаг готовности измерения
        app.config['Voltmeter']=self.dataFromServer

    @property
    def value(self):
        '''Возвращает измеренное напряжение сети'''
        return self._V

    @property
    def dataFromServer(self):
        '''Возвращает словарь, содержащий измеренное напряжение сети
           для передачи в веб-интерфейс клиента'''
        return {'Voltmeter':[('Сеть',self._V)]}

    def run(self):
        '''Функция start() объекта вольтметра'''
        self._Run=True
        while(self._Run):
            if self.VoltReady.isSet():  #если флаг установлен, сбросить его
                self.VoltReady.clear()
            self._V=self.GetVoltage()
            app.config['Voltmeter']=self.dataFromServer
            self.VoltReady.set()    #установить флаг готовности результатов измеерния вольтметра
            Transmit(self.dataFromServer())
            time.sleep(0.5)

    def stop(self):
        self._Run=False

    def GetVoltage(self):
        if app.config['RPI']:
            return self.MeasureVoltage()
        else:
            return self.EmulateVoltage()

    def MeasureVoltage(self):
        SMBus(1).write_byte(config['ADC_ADDR']['value'], 0b1000010)
        SMBus(1).read_byte(config['ADC_ADDR']['value']) # read last value
        SMBus(1).read_byte(config['ADC_ADDR']['value']) # repeat reading last value
        return round(config['PARAMETERS']['K_V']['value']*SMBus(1).read_byte(config['ADC_ADDR']['value']))

    def EmulateVoltage(self):
        return round(210+random.random()*20)


