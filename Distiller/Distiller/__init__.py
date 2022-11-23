"""
The flask application package.
"""

import os
import threading
import json
from flask import Flask
from flask_socketio import SocketIO

from Distiller.config import Config

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
    '''содержит настраиваемые параметры устройства'''
'''Сохранение config:
 with open('configDistiller.json','w',encoding="utf-8") as f:
    json.dump(config,f,ensure_ascii=False, indent=2)
'''

# Проверка наличия предыдущей конфигурации
if os.path.isfile('preconfigDistiller.json'):
    pass

#Создание приложения flask_socketio из flask-приложения
socketio = SocketIO(app)

# Запуск потока, измеряющего температурные значения
try:
    from Distiller.sensors.DS18B20 import Thermometers
    thermometers=Thermometers()
    if thermometers.needAutoLocation:
        app.config['Mode']='WAITAL'
        app.config['Display']='Требуется автоопределение мест установки DS18B20'
        app.config['Buttons']='WAITAL.html'
    else:
        app.config['Mode']='WAIT'
        app.config['Display']='Жду команду'
        app.config['Buttons']='WAIT.html'

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
#print(voltmeter.value)

# Запуск регулятора мощности
from Distiller.actuators.power import Power
power=Power()
power.name='power'
power.start()

# Объекты холодильников
from Distiller.actuators.cools import Condensator, Dephlegmator
dephlegmator=Dephlegmator()
condensator=Condensator()

#запуск потока регулирования охладителей
from Distiller.helpers.coolsRegulator import CoolsRegulator
coolsRegulator=CoolsRegulator()
coolsRegulator.name='coolsRegulator'
coolsRegulator.start()

#Запуск потока, отправляющего значения приборов клиенту
from Distiller.helpers.transmitter import SendGaugesValues
sendGaugesValues=SendGaugesValues()
sendGaugesValues.name='sendGaugesValues'
sendGaugesValues.start()

for Thread in threading.enumerate():
    print(Thread.name)

# Подключение функций представления веб-страниц
import Distiller.views
