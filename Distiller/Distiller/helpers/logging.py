"""
$Id: logging.py,v 1.1 2017/07/03 $

Copyright (c) C-Bell (VAGor). All rights reserved.

Класс-поток обеспечивает запись значений параметров
устройства в журнал с фиксацией времени записи.
"""


import os
import threading
from datetime import datetime
from Distiller import ds18B20toDB
from Distiller import power, condensator, dephlegmator
from Distiller import models, dbLock


class Logging(threading.Thread):
    u"""Класс журналирования показаний датчиков, состояний нагрева и клапанов"""

    # событие записи в журнал очередных данных
    ReadyLog=threading.Event()

    def __init__(self):
        threading.Thread.__init__(self)
        self.__Run=False
        self.ReadyLog.clear()

    def run(self):
        self.__Run=True
        while self.__Run:
            if self.ReadyLog.isSet(): self.ReadyLog.clear()
            ds18B20toDB.ReadyDS18B20.wait()    #Дождаться сигнала об окончании измерения температур
            #Записать новые данные в лог
            dbLock.acquire()
            timestamp=models.log(TimeStamp=datetime.now(), P=power.Value)
            for Th in models.DS18B20.query.all():
                newT=models.logT(T=Th.T, Thermometer=Th, TimeStamp=timestamp)
            models.db.session.commit()
            dbLock.release()
            self.ReadyLog.set()

    def stop(self):
        self.__Run=False

