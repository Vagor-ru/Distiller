"""
$Id: cools.py,v 1.0 2017/06/20 $

Copyright (c) C-Bell (VAGor). All rights reserved.

Классы для управления электроклапанами охладителей.
"""

import time
import RPi.GPIO as GPIO #Модуль доступа к GPIO Raspberry Pi
from Distiller import app
from Distiller.helpers.transmitter import Transmit

##Настройка по номеру штырька на плате (не номер GPIO)
GPIO.setmode(GPIO.BOARD)    #по номеру штырьков на плате


    

##Настройка по номеру штырька на плате (не номер GPIO)
GPIO.setmode(GPIO.BOARD)    #по номеру штырьков на плате

class Dephlegmator():
    '''класс дефлегматора'''

    def __init__(self):
        self._State = False
        self.PIN = app.config['DEPH_PIN']
        GPIO.setup(self.PIN, GPIO.OUT)
        GPIO.output(self.PIN, GPIO.LOW)

    @property
    def State(self):
        return self._State

    def On(self):
        GPIO.output(self.PIN, GPIO.HIGH)
        #print(u'Включение Dph')
        if not self._State:
            self._State = True
            Transmit({'DephState' : self._State, 'DateTime' :time.time()})

    def Off(self):
        GPIO.output(self.PIN, GPIO.LOW)
        #print(u'Отключение Dph')
        if self._State:
            self._State = False
            Transmit({'DephState' : self._State, 'DateTime' :time.time()})

    @property
    def DataFromServer(self):
        return {'DephState' : self._State}



class Condensator():
    '''класс конденсатора'''
    def __init__(self):
        self._State = False
        self.PIN = app.config['CONDER_PIN']
        GPIO.setup(self.PIN, GPIO.OUT)
        GPIO.output(self.PIN, GPIO.LOW)

    @property
    def State(self):
        return self._State

    def On(self):
        GPIO.output(self.PIN, GPIO.HIGH)
        if not self._State:
            self._State = True
            Transmit({'CondState' : self._State, 'DateTime' :time.time()})

    def Off(self):
        GPIO.output(self.PIN, GPIO.LOW)
        if self._State:
            self._State = False
            Transmit({'CondState' : self._State, 'DateTime' :time.time()})

    @property
    def DataFromServer(self):
        return {'CondState' : self._State}

