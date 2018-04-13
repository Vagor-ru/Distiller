"""
This script runs the Distiller application using a development server.
"""

from os import environ
from Distiller import app
from Distiller import socketio

if __name__ == '__main__':
    HOST = environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555

    #app.run(HOST, PORT)
    #Запуск сервера с вебсокетами
    socketio.run(app, HOST, PORT)
