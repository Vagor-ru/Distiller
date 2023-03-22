"""
$Id: manualOperations.py,v 1.1 2020/07/01 
C-Bell (VAGor).

Класс-поток для ручного управления мощностью нагрева и порогами срабатывания
клапанов конденсатора и дефлегматора

"""

import threading
import time
from flask import render_template
from Distiller import app, coolsRegulator,power,thermometers,config
from Distiller.helpers.transmitter import Transmit
from Distiller.helpers.coolsRegulator import CoolsRegulator
from Distiller.helpers.log import Logging


class ManualMode(threading.Thread):
    """класс-поток, предоставляющий ручное управление дистиллятором"""

    # Для сохранения состояния дисплея и кнопок
    Display = ''
    Buttons = ''

    def __init__(self):
        #threading.Thread.__init__(self)
        super(ManualMode, self).__init__()
        self._Run=False
        self.log = Logging('Manual')

    def run(self):
        # Сброс переменной прерывания/перехода процесса
        app.config['AB_CON']=''
        app.config['Mode']='MANUAL_MODE'
        #Сохранение состояния веб-интерфейса
        self.Display = app.config['Display']
        self.Buttons = app.config['Buttons']
        self.log.start()
        # Вывести сообщение на дисплей и прикрутить кнопку "Останов"
        self.pageUpdate('Ручной режим<br>',
                        'ABORT.html')
        self._Run=True
        #Ожидание в цикле
        while self._Run:
            if app.config['AB_CON']=='Abort' or app.config['AB_CON']=='Error':
                break
            time.sleep(0.5) #не частить

        power.value=0
        self.log.stop()
        thermometers.setTtrigger('Конденсатор',config['PARAMETERS']['Tcond']['value'])
        thermometers.setTtrigger('Дефлегматор',config['PARAMETERS']['Tdephlock']['value'])
        self._Run=False
        app.config['Mode']='WAIT'
        app.config['Display']=self.Display
        app.config['Buttons']=self.Buttons
        self.pageUpdate(app.config['Display'],app.config['Buttons'])
        return
    
    def pageUpdate(self, Display=None, Buttons=None):
        DataFromServer={}
        if Display != None:
            app.config['Display'] = Display
            DataFromServer['Display'] = Display
        if Buttons != None:
            app.config['Buttons'] = Buttons
            with app.test_request_context():
                DataFromServer['ModeButtons'] = render_template(Buttons)
        if len(DataFromServer) > 0:
            Transmit(DataFromServer)

