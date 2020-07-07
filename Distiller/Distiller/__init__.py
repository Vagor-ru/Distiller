"""
The flask application package.
"""

import os
import threading
import json
from flask import Flask
from flask_socketio import SocketIO

import Distiller.models
from Distiller.config import Config
from Distiller.database import db

# Объект для блокировки потоков при доступе к совместным ресурсам
dbLock = threading.Lock()

# Объект flask
app = Flask(__name__)
# Подгрузка конфигурации приложения из config.py
app.config.from_object(Config)

#Попытка получить uname. Если она неудачна, считаем,
#что запущены не на Raspberry Pi. Если uname содержит
#и 'Linux' и 'armv7l', наиболее вероятно, что программа
#выполняется на Raspberry Pi
try:
    _os=os.uname()
    if 'Linux' in _os and 'armv7l' in _os:
        app.config['RPI']=True
    else:
        app.config['RPI']=False
except Exception as exp:
    app.config['RPI']=False

# Чтение объекта конфигурации устройства из конфигурационного файла
with open('configDistiller.json','r',encoding="utf-8") as f:
    config=json.load(f)

'''Сохранение config:
 with open('configDistiller.json','w',encoding="utf-8") as f:
    json.dump(config,f,ensure_ascii=False, indent=2)
'''

#Создание приложения flask_socketio из flask-приложения
socketio = SocketIO(app)

# Запуск потока, записывающего температурные значения в БД
try:
    from Distiller.sensors.DS18B20 import Thermometers
    thermometers=Thermometers()
    if thermometers.needAutoLocation:
        app.config['Display']='Необходимо запустить автоопределение мест установки DS18B20'
        app.config['Buttons']='WAITAL.html'
    thermometers.name='thermometers'
    thermometers.start()
    pass
except Exception as ex:
    app.config['Display'] = 'Error: ' + str(ex)

#Запуск вольтметра
from Distiller.sensors.Voltmeter import Voltmeter
voltmeter=Voltmeter()
voltmeter.name='voltmeter'
voltmeter.start()

# Запуск регулятора мощности
from Distiller.actuators.power import Power
power=Power()
power.name='power'
power.start()

# Объекты холодильников
from Distiller.actuators.cools import Condensator, Dephlegmator
dephlegmator=Dephlegmator()
condensator=Condensator()


# Подключение функций представления веб-страниц
import Distiller.views
