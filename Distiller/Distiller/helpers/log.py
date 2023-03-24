"""
$Id: log.py,v 2017 - 2023 $

Copyright (c) C-Bell (VAGor). All rights reserved.

Класс-поток обеспечивает запись значений параметров
устройства в журнал с фиксацией времени записи.
"""


import os
import threading
import logging
import pathlib
from datetime import datetime, time
from time import strftime, localtime
#from Distiller import ds18B20toDB
from Distiller import power, condensator, dephlegmator, thermometers
#from Distiller import models, dbLock


class Logging(threading.Thread):
    u"""Класс журналирования показаний датчиков, состояний нагрева и клапанов"""

    __Run=False

    # событие записи в журнал очередных данных
    ReadyLog=threading.Event()

    def __init__(self, name=__name__):
        threading.Thread.__init__(self)
        self.__Run=False
        self.ReadyLog.clear()

        self.logger = logging.getLogger(name)   # объект логирования
        self.logger.setLevel(logging.INFO)      # уровень логирования
        # Писать будем в файл, при каждом запуске логгера создаём новый
        # имя файла с директорией логов
        f_log = pathlib.Path('logs', f"{name}{strftime('%y%m%d%H%M%S', localtime())}.log")
        handler = logging.FileHandler(f_log, mode='w')
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        msg=f"Время"
        for thermometer in thermometers.values:
            msg += f"\t{thermometer.Name}"
        self.logger.info(msg)   # Вывести в лог заголовки
        # подготовить форматтер для записи впемени и значений
        formatter = logging.Formatter("%(relativeCreated)d%(message)s")
        handler.setFormatter(formatter)

    def run(self):
        self.__Run=True
        while self.__Run:
            if self.ReadyLog.isSet(): self.ReadyLog.clear()
            thermometers.Tmeasured.wait()    #Дождаться сигнала об окончании измерения температур
            #Записать новые данные в лог
            msg = ''
            for thermometer in thermometers.values:
                msg += f"\t{thermometer.T}"
            self.logger.info(msg)   # Вывести в лог значения
            self.ReadyLog.set()
        #handler.close()
        self.logger.handlers[0].close()

    def stop(self):
        self.__Run=False

