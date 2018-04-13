"""
$Id: DS18B20.py, 2017/09/21
Copyright (c) 2017 C-Bell (VAGor).
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
if not os.path.isdir('/sys/bus/w1'):
    #Генерить исключение.
    raise NoOneWireError('No 1-wire bus')
    print("Включите поддержку 1-Wire в  конфигурации Raspberry!")
    exit()

#Каталог, отражающий устройства на шине 1-wire
base_dir = '/sys/bus/w1/devices/'

#Читает и возвращает значение температуры с указанного термометра
def read_temp_raw(device_folder):
    '''Читает и возвращает текущее значение температуры'''
    device_file = device_folder + '/w1_slave'
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    equals_pos = lines[1].find('t=')
    temp_string = lines[1][equals_pos+2:]
    temp_c = float(temp_string) / 1000.0
    return (os.path.basename(device_folder),
            round(temp_c, 1),
            datetime.datetime.now())
#--------------------

class T(threading.Thread):
    u'''Класс для получения температуры от одного цифрового термометра'''
    def __init__(self, device_folder):
        '''Инициализация класса'''
        threading.Thread.__init__(self)
        self._device_folder = device_folder
        #self.name = device_folder
        self._T = None
    def run(self):
        u'''Функция, вызываемая при старте потока'''
        self._T = read_temp_raw(self._device_folder)
    @property
    def T(self):
        u"""Возвращает текущее значение температуры"""
        return self._T
    @property
    def name(self):
        u'''Возвращает название папки термометра'''
        return self._device_folder
    
#Возвращает кортеж из списка кортежей названий термометров с температурами
#и временем измерения
def Measure(Sort=False, SortByT=False, TimeOut=None):
    u'''Функция Measure() ищет все цифровые термометры DS18B20 на шине 1-wire
    читает значения измеренных ими температур и возвращает в виде кортежа
    (список кортежей (ID термометра, температура), момент времени измерения)'''
    device_folders = glob.glob(base_dir + '28*')
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
        if eashT.isAlive():
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
    return DS18B20list

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
