"""
$Id: cools.py,v 1.0 2020/07/01 $

By C-Bell (VAGor). 

Классы для управления электроклапанами охладителей.
"""

import time
from Distiller.helpers.transmitter import Transmit
from Distiller import app
if app.config['RPI']:
    import RPi.GPIO as GPIO #Модуль доступа к GPIO Raspberry Pi

##Настройка по номеру штырька на плате (не номер GPIO)
if app.config['RPI']:
    GPIO.setmode(GPIO.BOARD)    #по номеру штырьков на плате



class Dephlegmator():
    '''класс дефлегматора'''

    def __init__(self):
        self._State = False
        self.PIN = app.config['DEPH_PIN']
        if app.config['RPI']:
            GPIO.setup(self.PIN, GPIO.OUT)
            GPIO.output(self.PIN, GPIO.LOW)

    @property
    def State(self):
        return self._State

    @State.setter
    def State(self,state):
        self._State=state
        Transmit(self.dataFromServer)

    def On(self):
        if app.config['RPI']:
            GPIO.output(self.PIN, GPIO.HIGH)
        #print(u'Включение Dph')
        if not self.State:
            self.State = True

    def Off(self):
        if app.config['RPI']:
            GPIO.output(self.PIN, GPIO.LOW)
        #print(u'Отключение Dph')
        if self.State:
            self.State = False

    @property
    def dataFromServer(self):
        return {'DephState' : self.State}



class Condensator():
    '''класс конденсатора'''
    def __init__(self):
        self._State = False
        self.PIN = app.config['CONDER_PIN']
        if app.config['RPI']:
            GPIO.setup(self.PIN, GPIO.OUT)
            GPIO.output(self.PIN, GPIO.LOW)

    @property
    def State(self):
        return self._State

    @State.setter
    def State(self,state):
        self._State = state
        Transmit(self.dataFromServer)

    def On(self):
        if app.config['RPI']:
            GPIO.output(self.PIN, GPIO.HIGH)
        if not self.State:
            self.State = True

    def Off(self):
        if app.config['RPI']:
            GPIO.output(self.PIN, GPIO.LOW)
        if self.State:
            self.State = False

    @property
    def dataFromServer(self):
        return {'CondState' : self.State}

