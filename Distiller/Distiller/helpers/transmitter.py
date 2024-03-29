import threading
import time
from Distiller import socketio
#from Distiller import power

def Transmit(DataFromServer):
    '''Transmit data in dictioner DataFromServer'''
    socketio.emit('DataFromServer', DataFromServer)


class SendGaugesValues(threading.Thread):
    '''Класс-поток, отправляет значения приборов и термометров клиенту.
    Передача происходит с каждым обновлением значений температур.
    '''

    _Run=False

    def __init__(self):
        super(SendGaugesValues, self).__init__()
        self._Run=False

    def run(self):
        self._Run=True
        while(self._Run):
            #from Distiller import thermometers
            #thermometers.Tmeasured.wait()
            #socketio.emit('DataFromServer', self.CollectData())
            time.sleep(1)
            pass

    def CollectData(self):
        #from Distiller import condensator
        #from Distiller import dephlegmator
        dataFromServer={}
        #dataFromServer.update(thermometers.dataFromServer)  #термометры
        #dataFromServer.update(voltmeter.dataFromServer)     #Вольтметр
        #dataFromServer.update(power.dataFromServer)         #Ваттметр
        #dataFromServer.update(condensator.dataFromServer)   #Конденсатор
        #dataFromServer.update(dephlegmator.dataFromServer)  #Дефлегматор
        #print(dataFromServer)
        return dataFromServer

    def stop(self):
        self._Run = False