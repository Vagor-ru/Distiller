"""
$Id: DS18B20.py, 2020/07/03
C-Bell (VAGor).
Снимает показания цифровых термометров DS18B20

Использование:
import DS18B20
DS18B20list=DS18B20.Measure()
где DS18B20list - список кортежей (ID термометра, значение температуры)

Особенности:
используется модуль threading для "одновременного"
запуска "измерения" температуры всеми "цифровыми термометрами DS18B20"
так же как в реальном модуле
"""

import random   #Модуль случайных чисел
import os       #Модуль функций для работы с операционной системой
import sys      #Модуль доступа к некоторым системным переменным и функциям
import glob     #находит все пути, совпадающие с заданным шаблоном 
import time     #Модуль для работы со временем
import datetime #Модуль для работы с датой и временем
import threading    #Модуль для работы с потоками
from Distiller import app, config, dbLock
from Distiller.helpers.transmitter import Transmit

#Шаблон ID термометра
TemplateDS18B20="28-000000"

#Класс исключения отсутствия наличия шины 1-wire
class NoOneWireError(Exception):
    '''Исключение отсутствия наличия шины 1-wire'''
    pass

#Класс исключения при отсутствии цифровых термометров на шине 1-wire
class NoDS18B20Error(Exception):
    '''Исключение при отсутствии цифровых термометров на шине 1-wire'''
    pass

#Класс исключения при таймауте цифровых термометров на шине 1-wire
class TimeOutDS18B20Error(Exception):
    '''Исключение при таймауте измерения температуры'''
    pass

#Проверка наличия шины 1-wire (редкий случай)
#Проверка наличия шины 1-wire
if app.config['RPI'] and not os.path.isdir('/sys/bus/w1'):
    #Генерить исключение.
    raise NoOneWireError('No 1-wire bus')
    print("Включите поддержку 1-Wire в  конфигурации Raspberry!")
    exit()

#Создание фейкового списка термометров
Tlist=[]    #Пустой список термометров
if not app.config['RPI']:
    NumbT=5  #Количество термометров
    #Создать ID каждому термометру
    for i in range(NumbT):
        Tlist.append("28-000000"+chr(ord('E')-i)*6)
    #print(Tlist)

#Каталог, отражающий устройства на шине 1-wire
base_dir = '/sys/bus/w1/devices/'


class T(threading.Thread):
    u'''Класс для получения температуры от одного цифрового термометра'''
    def __init__(self, device_folder):
        '''Инициализация класса'''
        #threading.Thread.__init__(self)
        super(T, self).__init__()
        self._device_folder = device_folder
        #self.name = device_folder
        self._T = None
    def run(self):
        u'''Функция, вызываемая при старте потока'''
        self._T = self.read_temp_raw(self._device_folder)
    @property
    def T(self):
        u'''Возвращает текущее значение температуры'''
        return self._T
    @property
    def name(self):
        u'''Возвращает название папки термометра'''
        return self._device_folder

    #Читает и возвращает значение температуры с указанного термометра
    def read_temp_raw(self, device_folder):
        '''Читает и возвращает текущее значение температуры'''
        #Если не на Raspberry Pi, вернуть фейк
        if not app.config['RPI']:
            return self.temp_fake(device_folder)
        device_file = device_folder + '/temperature'
        #dbLock.acquire()
        temp_c=0.0
        while True:
            f = open(device_file, 'r')
            val = f.read()
            f.close()
            try:
                temp_c = float(val) / 1000.0
                break
            except ValueError:
                pass
        #dbLock.release()
        return (os.path.basename(device_folder),
                round(temp_c, 1),
                datetime.datetime.now())

    def temp_fake(self, device_folder):
        u'''Возвращает сгенерированное значение температуры'''
        time.sleep(1+random.random()*0.05)  #Имитируем процесс измерения
        return (device_folder, round(random.random()*100,1))

#--------------------
    
#Возвращает список кортежей названий термометров с температурами
#и временем измерения
def Measure(Sort=False, SortByT=False, TimeOut=None):
    u'''Функция Measure() ищет все цифровые термометры DS18B20 на шине 1-wire
    читает значения измеренных ими температур и возвращает в виде кортежа
    (список кортежей (ID термометра, температура), момент времени измерения)'''
    if app.config['RPI']:
        device_folders = glob.glob(base_dir + '28*')
    else:
        device_folders = Tlist
    #Если термометры DS18B20 на шине не найдены, генерировать исключение
    if len(device_folders)==0:
        #Генерить исключение.
        raise NoDS18B20Error('DS18B20 not found on 1-wire bus')
    
    #Список объектов-потоков
    Threads=[]

    #Список термометров
    DS18B20list=[]

    #Создание объектов-потоков для каждого термометра
    for device_folder in device_folders:
        Threads.append(T(device_folder))

    #Запуск всех потоков
    for eashT in Threads:
        eashT.start()

    #Присоединение потоков к текущему, чтобы ожидать завершение измерения
    for eashT in Threads:
        eashT.join(TimeOut)

    # Проверить таймауты потоков
    for eashT in Threads:
        if eashT.is_alive():
            raise TimeOutDS18B20Error('Timeout of measure of temperature at %s'%eashT.name)

    #Сбор значений температур термометров
    for eashT in Threads:
        DS18B20list.append(eashT.T)

    def sortByT(ThermoData):
        return ThermoData[1]

    #Если заказано, сортируем список по ID термометров
    if Sort: DS18B20list.sort()
    #Если заказано отсортировать по температуре, сортируемо
    if SortByT: DS18B20list.sort(key=sortByT, reverse=True)
    #Выдача результатов
    #print(DS18B20list)
    return DS18B20list

class DS18B20:
    '''класс термометра'''
    def __init__(self, ID):
        self.ID=ID          #фабричный номер термометра вида 28-000000c57def
        self.Name=None      #Наименование (место установки) термометра
        self.T=None         #текущая температура
        self.Tpre=None      #предыдущая температура
        self.V_T=0.0        #скорость роста температуры
        self.V_Tpre=0.0     #предыдущая скорость роста температуры
        self.Ttrigger=None  #установка порога срабатывания
        self.boiling=False  #флаг закипания
        self.trigger=False  #флаг сработки по порогу

class Thermometers(threading.Thread):
    ''' Класс-поток, измеряет температуры и устанавливает флаг
        готовности температурных данных, флаг закипания,
        флаг срабатывания порога'''
    '''Событие "Получены новые данные о температурах'''
    Tmeasured=threading.Event()
    """Событие закипание"""
    boiling=threading.Event()
    """Событие превышения порога"""
    trigger=threading.Event()
    #флаг необходимости автоопределения мест установки термометров
    needAutoLocation=False

    def __init__(self):
        '''инициализация'''
        #threading.Thread.__init__(self)
        super(Thermometers, self).__init__()
        self.__Run = False      #сброс флага исполнения
        #self.CheckTlist()
        self.Tmeasured.clear()  #сброс флага завершения измерения
        self.boiling.clear()    #сброс флага закипания
        self.trigger.clear()    #сброс флага срабатывания порога
        self.Tlist=[]           #Текущие температуры
        Ts=Measure()            #сделать первое измерение
        #создание списка объектов-термометров
        #print(len(self.Tlist))
        dbLock.acquire()        #всем остальным потокам ждать!
        self.Tlist.clear()
        for T in Ts:
            objT=DS18B20(T[0])
            objT.T=T[1]
            objT.Tpre=T[1]
            if "locations" in config['LOCATIONS']:
                if T[0] in config['LOCATIONS']["locations"]:
                    objT.Name=config['LOCATIONS']["locations"][T[0]]
                    if objT.Name=='Конденсатор':
                        objT.Ttrigger=config['PARAMETERS']['Tcond']['value']
                    if objT.Name=='Дефлегматор':
                        objT.Ttrigger=config['PARAMETERS']['Tdephlock']['value']
                else:
                    self.needAutoLocation=True
            else:
                self.needAutoLocation=True
            self.Tlist.append(objT)
        dbLock.release()        #другие потоки могут читать Tlist
        #print(len(self.Tlist))

    def run(self):
        '''Запускает поток измерения температур'''
        self.__Run = True
        while self.__Run:
            # Если флаг получения температурных данных установлен,
            # сбросить его
            if self.Tmeasured.isSet():
                #сохранить предыдущие температуры и скорости изменения
                dbLock.acquire()
                for objT in self.Tlist:
                    objT.Tpre = objT.T
                    objT.V_Tpre = objT.V_T
                dbLock.release()
                self.Tmeasured.clear()
            #сбросить флаги закипания и срабатывания, если были установлены
            if self.boiling.is_set():
                self.boiling.clear()
            if self.trigger.is_set():
                self.trigger.clear()
            tBegin=time.time()  #засечь время
            Ts=Measure()        #измерить температуры
            #print(Ts)
            durationMeasure=time.time()-tBegin  #вычислить затраченное на измерение время
            app.config['Thermometers']=self.dataFromServer
            #print(app.config['Thermometers'])
            # сравнение температур и установка флага если закипание
            dbLock.acquire()    #монополизировать выполнение на время сохранения температур
            for T in Ts:
                objT=list(filter(lambda objT: objT.ID==T[0],self.Tlist))[0]
                objT.T=T[1]
                objT.V_T=(objT.T-objT.Tpre)/durationMeasure #вычислить скорость изменения температуры
                #если скорость роста температуры больше 0.4°C в секунду, значит закипание
                if objT.V_T > 0.4:
                    objT.boiling=True
                    self.boiling.set()
                else:
                    objT.boiling=False
                #если превышение порога, выбросить флаг
                if objT.Ttrigger!=None and objT.T>objT.Ttrigger:
                    objT.trigger=True
                    self.trigger.set()
                else:
                    objT.trigger=False
            dbLock.release()    #разрешить исполнение другим потокам
            self.Tmeasured.set()
            Transmit(self.dataFromServer)
            #если сброшен флаг работы, рвем цикл
            if not self.__Run:
                break

    def getTtrigger(self, name):
        '''Возвращает установку триггера заданного термометра'''
        objT=list(filter(lambda objT: objT.Name==name,self.Tlist))[0]
        return objT.Ttrigger

    def setTtrigger(self, name, Ttr):
        '''Устанавливает температуру триггера заданного термометра'''
        objT=list(filter(lambda objT: objT.Name==name,self.Tlist))[0]
        objT.Ttrigger=float(Ttr)
        pass

    def getValue(self, name):
        '''возвращает значение температуры указанного термометра'''
        objT=list(filter(lambda objT: objT.Name==name,self.Tlist))[0]
        return objT.T

    def getObjT(self, name):
        '''возвращает объект термометра по его имени'''
        objT=list(filter(lambda objT: objT.Name==name,self.Tlist))[0]
        return objT


    @property
    def values(self):
        '''Возвращает список объектов - термометров'''
        return self.Tlist

    @property
    def dataFromServer(self):
        Tlist=[]
        dbLock.acquire()
        if self.needAutoLocation:
            for Th in self.Tlist:
                Tlist.append((Th.ID,Th.T))
        else:
            for Name in config['LOCATIONS']['names']:
                objT=list(filter(lambda objT: objT.Name==Name,self.Tlist))[0]
                if objT.Ttrigger!=None:
                    Tlist.append((objT.Name,objT.T,objT.Ttrigger))
                else:
                    Tlist.append((objT.Name,objT.T))
        dbLock.release()
        return {'Thermometers':Tlist}

    def stop(self):
            self.__Run=False


def main():
    u'''Тестовая функция, работающая при запуске модуля непосредственно'''
    t=0
    tMax=0
    tMin=10
    for i in range(1, 9999999):
        timeBegin=time.time()
        DS18B20list=Measure()
        tMeasure=time.time()
        #os.system('clear')
        for DS18B20 in DS18B20list:
            print("%s\t%3.1f градC %s" % DS18B20)
            #print(DS18B20)
        print('Время измерения=%ssec' % (tMeasure-timeBegin))
        t+=(tMeasure-timeBegin)
        print('Среднее время измерения=%ssec' % (t/i))
        if (tMax<(tMeasure-timeBegin)):
              tMax=(tMeasure-timeBegin)
        print(u'(mt)Максимальная продолжительность измерения=%ssec' % tMax)
        if (tMin>(tMeasure-timeBegin)):
              tMin=(tMeasure-timeBegin)
        print(u'(mt)Минимальная продолжительность измерения=%ssec' % tMin)
        print('')

if __name__ == '__main__':
    main()
