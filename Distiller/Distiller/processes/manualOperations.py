"""
$Id: manualOperations.py,v 1.1 2020/07/01 
C-Bell (VAGor).

Класс-поток для ручного управления мощностью нагрева и порогами срабатывания
клапанов конденсатора и дефлегматора

"""

import threading
from flask import render_template
from Distiller.helpers.transmitter import Transmit
from Distiller.helpers.DS18B20toDB import ReadyDS18B20
from Distiller.helpers.coolsRegulator import CoolsRegulator


class ManualOperations(threading.Thread):
    """класс-поток, предоставляющий ручное управление дистиллятором"""

    # Для сохранения состояния дисплея и кнопок
    Display = ''
    Buttons = ''

    def __init__(self):
        threading.Thread.__init__(self)
        self.CoolsRegl=CoolsRegulator()
        self.CoolsRegl.name='CoolsRegulator'


    def run(self):
        # Сброс переменной прерывания/перехода процесса
        app.config['AB_CON']=''
        #Сохранение состояния веб-интерфейса
        self.Display = app.config['Display']
        self.Buttons = app.config['Buttons']
        # Вывести сообщение на дисплей и прикрутить кнопку "Останов"
        self.pageUpdate('Ручной режим<br>',
                        'ABORT.html')
        self.CoolsRegl.Tdeph=40
        self.CoolsRegl.Tcond=29
        #старт регулятора охлаждения
        self.CoolsRegl.start()
        #Мощность нагрева=100%
        power.Value=100
        #Ожидание закипания
        while True:
            # ждать свежие данные о температурах
            ReadyDS18B20.wait()
    
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

