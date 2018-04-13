"""
The flask application package.
"""

import threading
from flask import Flask
from flask_socketio import SocketIO

import Distiller.models
from Distiller.config import Config
from Distiller.database import db

# Объект для блокировки потоков при доступе к совместным ресурсам
dbLock = threading.Lock()

# Объект flask
app = Flask(__name__)
# Загрузка конфигурации из config.py
app.config.from_object(Config)

#Создание приложения flask_socketio из flask-приложения
socketio = SocketIO(app)

# Подключение, инициализация и создание (при необходимости) базы данных
db.app=app
db.init_app(app)
# Создать базу данных
db.create_all(bind='Distiller') 
db.create_all(bind='log') 

#Проверка параметров колонны, при необходимости - заполнение баз из файла config.py
dbLock.acquire()
ListParameters1=models.Parameters1.query.all()
ListParameters2=models.Parameters2.query.all()
#Если в БД нет записей, добавляем их из конфига
if len(ListParameters1)==0:
    for Prmtr in Config.PARAMETERS1:
        Row=models.Parameters1(Symbol=Prmtr[0], Value=Prmtr[1], Note=Prmtr[2])
        db.session.add(Row)
    db.session.commit()
if len(ListParameters2)==0:
    for Prmtr in Config.PARAMETERS2:
        Row=models.Parameters2(Symbol=Prmtr[0], Value=Prmtr[1], Note=Prmtr[2])
        db.session.add(Row)
    db.session.commit()
dbLock.release()


# Запуск потока, записывающего температурные значения в БД
try:
    from Distiller.helpers.DS18B20toDB import DS18B20toDB
    ds18B20toDB=DS18B20toDB()
    ds18B20toDB.name='ds18B20toDB'
    ds18B20toDB.start()
except Exception as ex:
    app.config['Display'] = 'Error: ' + str(ex)

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
