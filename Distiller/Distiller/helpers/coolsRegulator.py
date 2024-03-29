"""
$Id: coolsRegulator.py,v 1.1 2020/07/09 $

By C-Bell (VAGor).

Класс-поток обеспечивает регулировку
конденсатора и дефлегматора.
"""

import time
import threading
from Distiller import config
from Distiller import condensator
from Distiller import thermometers


class CoolsRegulator(threading.Thread):
    u'''Реализует регулирование охладителей'''

    def __init__(self,
                 Tdeph=None,
                 Tcond=None):
        #threading.Thread.__init__(self)
        super(CoolsRegulator, self).__init__()
        self.Run=False
        if Tdeph==None:
            self._Tdeph=config['PARAMETERS']['Tdephlock']['value']
        else:
            self._Tdeph=Tdeph
        if Tcond==None:
            self._Tcond=config['PARAMETERS']['Tcond']['value']
        else:
            self._Tcond=Tcond

    @property
    def Tdeph(self):
        return self._Tdeph

    @Tdeph.setter
    def Tdeph(self, tdeph):
        if tdeph>85:
            tdeph=85
        if tdeph<16:
            tdeph=16
        self._Tdeph=tdeph

    @property
    def Tcond(self):
        return self._Tcond

    @Tdeph.setter
    def Tcond(self, tcond):
        if tcond>85:
            tcond=85
        if tcond<16:
            tcond=16
        self._Tcond=Tcond

    def run(self):
        self.Run=True
        while self.Run:
            thermometers.Tmeasured.wait() #ждать срабатывание триггера
            #dataFromServer=None
            for Th in thermometers.Tlist:
                if Th.Name=='Конденсатор':
                    if Th.trigger:
                        condensator.On()
                    else:
                        condensator.Off()
                #if Th.Name=='Дефлегматор':
                #    if Th.trigger:
                #        dephlegmator.On()
                #    else:
                #        dephlegmator.Off()
        #dephlegmator.Off()
        condensator.Off()
        return

    def stop(self):
        self.Run=False