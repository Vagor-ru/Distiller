import threading
import time
from simple_pid import PID
from Distiller import config, thermometers, app
from Distiller.actuators.condensator import CondRun

class CondReg(threading.Thread):
    u"""Класс-поток PID-регулирования температуры конденсатора"""

    _Run = False    # сбросить флаг исполнения
    # Для сохранения состояния дисплея
    Display = ''

    def __init__(self):
        #пуск родительской инициализации
        super(CondReg, self).__init__()
        """Загрузка в PID-регулятор коэффициентов и уставки из конфига"""
        self.pidD = PID(config['PARAMETERS']['Kpc']['value'],\
           config['PARAMETERS']['Kic']['value'],\
          config['PARAMETERS']['Kdc']['value'],\
         setpoint=config['PARAMETERS']['Tcond']['value'])
        thermometers.setTtrigger('Конденсатор', self.pidD.setpoint)
        """Установить пределы выхода PID-регулятора"""
        self.pidD.output_limits = (0, 100)
        self.Cond = CondRun()   #Bresenham-регулятор конденсатора
        self.Cond.value=0   #отключить охлаждение конденсатора
        self._Run = False   # сбросить флаг запуска процесса


    def run(self):
        """Запуск цикла регулирования температуры конденсатора"""
        self._Run = True
        # запустить регулятор конденсатора
        self.Cond.start()
        # время старта охлаждения
        coolingStartTime = time.time()
        Display = app.config['Display']
        while self._Run:
            '''цикл регулирования'''
            thermometers.Tmeasured.wait()   #ожидать следующего измерения температуры
            #Заново подгрузить коэффициенты (вдруг изменились)
            '''Если разность более, чем 4°C, ужесточить PID'''
            if thermometers.getValue('Конденсатор')-thermometers.getTtrigger('Конденсатор') > 4:
                self.pidD.tunings = (1000*config['PARAMETERS']['Kpc']['value'],\
                                  config['PARAMETERS']['Kic']['value'],\
                                  config['PARAMETERS']['Kdc']['value'])
            else:
                self.pidD.tunings = (config['PARAMETERS']['Kpc']['value'],\
                                  config['PARAMETERS']['Kic']['value'],\
                                  config['PARAMETERS']['Kdc']['value'])
            self.pidD.setpoint = thermometers.getTtrigger('Конденсатор')
            #print(thermometers.getValue('Конденсатор'), '->', thermometers.getTtrigger('Конденсатор'))
            #рассчитать и установить охлаждение
            PID_D = self.pidD(thermometers.getValue('Конденсатор'))
            #print('Дефлегматор=', PID_D)
            self.Cond.value = PID_D
            if thermometers.getTtrigger('Конденсатор')+1 < thermometers.getValue('Конденсатор'):
                if time.time() - coolingStartTime > config['PARAMETERS']['tCooling']['value']:
                    # гасить всё и выдавать ошипку
                    #Display = app.config['Display']
                    app.config['Error'] = 'Error: нет охлаждения'
                    #for th in threading.enumerate():
                    #    if th.name == 'Wash' or th.name == 'Crude' or th.name == 'ManualMode':
                    #        th.stop
                    #    #print(th.name)
                    pass
            else:
                #сбросить засечку времени
                coolingStartTime = time.time()
                #восстановить дисплей
                app.config['Error'] = ''
                #app.config['Display'] = Display

        self.Cond.value=0   #отключить охлаждение дефлегматора
        self.Cond.stop()

    def stop(self):
        """Останов регулирования"""
        self.Cond.value = 0
        self._Run = False