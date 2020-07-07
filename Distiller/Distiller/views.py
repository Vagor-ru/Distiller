"""
Routes and views for the flask application.
"""

from datetime import datetime
from flask import render_template
from Distiller import app, socketio, power, condensator, dephlegmator
from Distiller.helpers.transmitter import Transmit

@app.route('/')
def home():
    """Renders the home page with temperature data."""
    return render_template(
        'layout.html',
        title=app.config['DEVICE_NAME'],
    )

############################################################################
#  Обработчики запросов через веб-сокеты
#===========================================================================
@socketio.on('connect')
def client_connect():
    '''Подключение клиента'''
    print('client connected')
    #socketio.emit('DataFromServer', {'Connect' : 'Connect'}, brodcast=True)

@socketio.on('disconnect')
def client_disconnect():
    '''ОТключение клиента'''
    print('client disconnect')

@socketio.on('GiveDeviceData')
def TransmittDataToClient(dataToServer):
    '''Обработчик запроса клиента. Возвращает (callback) этому клиентe данные
    о текущем состоянии устройства. Клиент запрашивает эти данные при подключении'''
    #print(u'Получен запрос данных от клиента')
    #if 'sid' in dataToServer:
    #    print('sid='+dataToServer['sid'])
    DataFromServer={}   #Словарь, который содержит передаваемые данные
    #DataFromServer.update(power.DataFromServer)
    if 'Thermometers' in app.config:
        DataFromServer['Thermometers']=app.config['Thermometers']
    if 'Voltmeter' in app.config:
        DataFromServer['Voltmeter']=app.config['Voltmeter']
    DataFromServer['Power']=power.value
    DataFromServer['Display']=app.config['Display']
    DataFromServer.update(dephlegmator.DataFromServer)
    DataFromServer.update(condensator.DataFromServer)
    if 'Buttons' in app.config:
        DataFromServer['ModeButtons']=render_template(app.config['Buttons'])
    print (DataFromServer)
    return DataFromServer


@socketio.on('Control')
def Controls(DataControls):
    '''Обработка нажатий кнопок веб-морды'''
    #socketio.emit('DataFromServer', {'Display' : 'Нажата кнопка '+DataControls['Button']}, broadcast=False)
    #return
    #print()
    if 'Button' in DataControls:
        if DataControls['Button']=='StartAL':
            print('Поступила команда запуска автоопределения')
            from Distiller.processes.autolacation import Autolocation
            AL=Autolocation()
            AL.name='Autolocation'
            AL.start()
        if DataControls['Button']=='Wait':
            print('Поступила команда перейти в режим ожидания команд')
        if DataControls['Button']=='Wash':
            print('Поступила команда запуска процесса перегона бражки')
            from Distiller.processes.wash import Wash
            wash = Wash()
            wash.name = 'Wash'
            wash.start()
        if DataControls['Button']=='Crude':
            print('Поступила команда запуска процесса второго перегона')
            from Distiller.processes.crude import Crude
            crude = Crude()
            crude.name = 'Crude'
            crude.start()
        if DataControls['Button']=='ManualMode':
            print('Поступила команда запуска ручного режима')
        if DataControls['Button']=='Abort':
            print('Команда прерывания процесса')
            app.config['AB_CON']='Abort'
        if DataControls['Button']=='Next':
            print('Команда перехода к следующему этапу')
            app.config['AB_CON']='Next'
        if DataControls['Button']=='End':
            print('Команда завершения процесса')
            app.config['Display'] = 'Жду команду'
            app.config['Buttons'] = 'WAIT.html'
            Transmit({'Display' : 'Жду команду',
                      'ModeButtons' : render_template('WAIT.html')})
        if DataControls['Button']=='Parameters':
            print('Команда установки параметров')
        if DataControls['Button']=='Shutdown':
            print('Команда на отключение питания')
            from os import system
            # перед вызовом нужно команде shutdown дать права суперпользователя:
            # sudo chmod +s '/sbin/shutdown'
            system('/sbin/shutdown -h now')
        if DataControls['Button']=='Parameters':
            pass
    if 'SetTrigger' in DataControls:
        print(DataControls['SetTrigger'])
        pass
    if 'SetValue' in DataControls:
        print(DataControls['SetValue'])
        pass

