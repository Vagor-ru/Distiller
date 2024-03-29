"""
Routes and views for the flask application.
"""

import json
from datetime import datetime
from flask import render_template, request, flash, redirect
from Distiller import app, socketio, power, condensator, dephlegmator, thermometers,voltmeter, config
from Distiller.helpers.transmitter import Transmit

@app.route('/')
def home():
    """Renders the home page with temperature data."""
    return render_template(
        'layout.html',
        title=app.config['DEVICE_NAME'],
    )

@app.route('/parameters', methods=['GET', 'POST'])
def parameters():
    """Renders the page parameters data."""
    if request.method == 'POST':
        form = request.form.to_dict()
        #print(form)
        for field in form:
            config['PARAMETERS'][field]['value'] = float(form[field])
            #print(field, config['PARAMETERS'][field]['value'])
        with open('configDistiller.json','w',encoding="utf-8") as f:
            json.dump(config,f,ensure_ascii=False, indent=2)
        flash('Параметры успешно сохранены', 'success')
        return redirect('/')
    else:
        #return redirect('/')
        pass
    #print(config['PARAMETERS'])
    return render_template('parameters.html', title='Параметры', parameters=config['PARAMETERS'])

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
    DataFromServer.update(thermometers.dataFromServer)  #Термометры
    DataFromServer.update(voltmeter.dataFromServer)     #Вольтметр
    DataFromServer.update(power.dataFromServer)         #Ваттметр
    DataFromServer.update(condensator.dataFromServer)   #Конденсатор
    DataFromServer.update(dephlegmator.dataFromServer)  #Дефлегматор
    if 'Display' in app.config:
        DataFromServer['Display']=app.config['Display'] #Экран монитора
    if 'Buttons' in app.config:
        DataFromServer['ModeButtons']=render_template(app.config['Buttons'])    #кнопки
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
            app.config['Display'] = 'Жду команду'
            print('Поступила команда запуска процесса перегона бражки')
            from Distiller.processes.wash import Wash
            wash = Wash()
            wash.name = 'Wash'
            wash.start()
        if DataControls['Button']=='Crude':
            app.config['Display'] = 'Жду команду'
            print('Поступила команда запуска процесса второго перегона')
            from Distiller.processes.crude import Crude
            crude = Crude()
            crude.name = 'Crude'
            crude.start()
        if DataControls['Button']=='ManualMode':
            app.config['Display'] = 'Жду команду'
            print('Поступила команда запуска ручного режима')
            from Distiller.processes.manualMode import ManualMode
            manualMode=ManualMode()
            manualMode.name='ManualMode'
            manualMode.start()
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
        if app.config['Mode']=='MANUAL_MODE':
            thermometers.setTtrigger(DataControls['SetTrigger'][0],DataControls['SetTrigger'][1])
        pass
    if 'SetValue' in DataControls:
        print(DataControls['SetValue'])
        if DataControls['SetValue'][0]=='Power' and app.config['Mode']=='MANUAL_MODE':
            power.value=float(DataControls['SetValue'][1])
        else:
            power.value=power.value
        pass

