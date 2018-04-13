"""
$Id: coolsRegulator.py,v 1.1 2017/07/03 $

Copyright (c) C-Bell (VAGor). All rights reserved.

Класс-поток обеспечивает запись значений параметров
устройства в журнал с фиксацией времени.
"""

import time
import threading
from Distiller import models, dbLock
from Distiller import condensator, dephlegmator
from Distiller import ds18B20toDB


class CoolsRegulator(threading.Thread):
    u'''Реализует регулирование охладителей'''

    def __init__(self,
                 Tdeph=None,
                 Tcond=None):
        threading.Thread.__init__(self)
        self.Run=False
        if Tdeph==None:
            dbLock.acquire()
            self._Tdeph=models.Parameters1.query.filter(models.Parameters1.Symbol==u'Tdephlock').first().Value
            dbLock.release()
        else:
            self._Tdeph=Tdeph
        if Tcond==None:
            dbLock.acquire()
            self._Tcond=models.Parameters1.query.filter(models.Parameters1.Symbol==u'Tcond').first().Value
            dbLock.release()
        else:
            self._Tcond=Tcond

    @property
    def Tdeph(self):
        return self._Tdeph

    @Tdeph.setter
    def Tdeph(self, tdeph):
        if tdeph>85:
            tdeph=85
        if tdeph<4:
            tdeph=4
        self._Tdeph=tdeph

    @property
    def Tcond(self):
        return self._Tcond

    @Tdeph.setter
    def Tcond(self, tcond):
        if tcond>85:
            tcond=85
        if tcond<4:
            tcond=4
        self._Tcond=Tcond

    def run(self):
        self.Run=True
        while self.Run:
            ds18B20toDB.ReadyDS18B20.wait()
            dbLock.acquire()
            if models.DS18B20.query.filter_by(Name='Деф').first().T>self._Tdeph:
                dephlegmator.On()
            else:
                dephlegmator.Off()
            if models.DS18B20.query.filter_by(Name='Конд').first().T>self._Tcond:
                condensator.On()
            else:
                condensator.Off()
            dbLock.release()
        dephlegmator.Off()
        condensator.Off()
        return

    def stop(self):
        self.Run=False