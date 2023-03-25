"""
The flask application package.

!!!
В файл requirements.txt должны быть включены строки:
smbus
RPi.GPIO
!!!

"""

import os
import threading
import json
from flask import Flask
from flask_socketio import SocketIO

from Distiller.config import Config

# Создание папки для логов
if not os.path.isdir('logs'):
    os.mkdir('logs')

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

# Проверка наличия предыдущей версии конфигурации после обновления ПО
if os.path.isfile('preconfigDistiller.json'):
    with open('preconfigDistiller.json','r',encoding="utf-8") as f:
        preconfig=json.load(f)
    if "CONDER_PIN#" in preconfig:
        '''если обнаружена предыдущая версия конфигурации'''
        from Distiller.helpers.transferConfig import transferConfig
        transferConfig.transfer(config, preconfig)  #перенести часть предыдущих параметров в новую версию конфига
    elif "EDITION" in preconfig and preconfig['EDITION'] =='2023-03-08':
        '''если версия та же, использовать конфиг с raspberry'''
        config=preconfig
    '''Сохранение config:'''
    with open('configDistiller.json','w',encoding="utf-8") as f:
        json.dump(config,f,ensure_ascii=False, indent=2)
    os.remove('preconfigDistiller.json')    #удалить ненужный файл конфига
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

#запуск потока регулирования конденсатора
#from Distiller.helpers.coolsRegulator import CoolsRegulator
#coolsRegulator=CoolsRegulator()
#coolsRegulator.name='coolsRegulator'
#coolsRegulator.start()

#запуск потока PID-регулятора температуры конденсатора
thermometers.setTtrigger('Конденсатор', config['PARAMETERS']['Tcond']['value'])
from Distiller.helpers.condReg import CondReg
cond_Reg = CondReg()
cond_Reg.name = 'cond_Reg'
cond_Reg.start()

#запуск потока PID-регулятора температуры дефлегматора
thermometers.setTtrigger('Дефлегматор', config['PARAMETERS']['Tdephlock']['value'])
from Distiller.helpers.DephReg import DephReg
deph_Reg = DephReg()
deph_Reg.name = 'deph_Reg'
deph_Reg.start()

#Запуск потока, отправляющего значения приборов клиенту
from Distiller.helpers.transmitter import SendGaugesValues
sendGaugesValues=SendGaugesValues()
sendGaugesValues.name='sendGaugesValues'
sendGaugesValues.start()

for Thread in threading.enumerate():
    print(Thread.name)

# Подключение функций представления веб-страниц
import Distiller.views
