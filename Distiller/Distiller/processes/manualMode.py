"""
$Id: manualOperations.py,v 1.1 2020/07/01 
C-Bell (VAGor).

Класс-поток для ручного управления мощностью нагрева и порогами срабатывания
клапанов конденсатора и дефлегматора

"""

import threading
import time
from flask import render_template
from Distiller import app, power,thermometers,config
from Distiller.helpers.transmitter import Transmit
from Distiller.helpers.condReg import CondReg
from Distiller.helpers.DephReg import DephReg
from Distiller.helpers.log import Logging


class ManualMode(threading.Thread):
    """класс-поток, предоставляющий ручное управление дистиллятором"""

    # Для сохранения состояния дисплея и кнопок
    Display = ''
    Buttons = ''
    _Run=False

    def __init__(self):
        #threading.Thread.__init__(self)
        super(ManualMode, self).__init__()
        self.cond_Reg = CondReg()   #регулятор конденсатора
        self.deph_Reg = DephReg()   #регулятор дефлегматора
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
        # Запустить регуляторы холодильников
        self.cond_Reg.start()
        self.deph_Reg.start()

        #Ожидание в цикле
        while self._Run:
            if app.config['AB_CON']=='Abort' or app.config['AB_CON']=='Error':
                break
            app.config['Error'] = ''    #сбросить ошибку
            time.sleep(0.5) #не частить

        #power.value=0
        self.log.stop()
        thermometers.setTtrigger('Конденсатор',config['PARAMETERS']['Tcond']['value'])
        thermometers.setTtrigger('Дефлегматор',config['PARAMETERS']['Tdephlock']['value'])
        self._Run=False
        app.config['Mode']='WAIT'
        app.config['Display']=self.Display
        app.config['Buttons']=self.Buttons
        self.pageUpdate(app.config['Display'],app.config['Buttons'])
        return

    def stop(self):
        '''Функция останавливает ручной режим'''
        power.value=0
        self.cond_Reg.stop()    # остановить регулятор конденсатора
        self.deph_Reg.stop()    # остановить регулятор дефлегматора
        #Восстановление состояния веб-интерфейса
        app.config['Display'] = self.Display
        app.config['Buttons'] = self.Buttons
        self._Run = False
    
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

