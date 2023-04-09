#!/usr/bin/env python
#coding=utf8
"""
$Id: DS18B20mt.py, 2017/01/23
Copyright (c) 2017 C-Bell (VAGor). 
Чтение значений температур с цифровых термометров DS18B20
по шине 1-wire, подключенной к GPIO4 одноплатного компьютера
Raspberry PI

Условия:
- к GPIO4 подключена шина 1-wire с  резистором 4,7 kOm,
  второй вывод резистора подключен к выводу 3,3V
- в конфигураторе Raspberry PI должна быть включена шина 1-wire
  (установлены и запущены модули w1-gpio и w1-therm)

Использование:
import DS18B20
(DS18B20list, tMeasure)=DS18B20.Measure()
где DS18B20list - список кортежей (ID термометра, значение температуры)
    tMeasure    - момент фиксации показаний термометров

Особенности:
используется модуль threading для запуска измерения температуры
всеми цифровыми термометрами DS18B20 в разных потоках, 
что в большинстве случаев сокращает до минимума время опроса термометров
"""


import os       #Модуль функций для работы с операционной системой
import sys      #Модуль доступа к некоторым системным переменным и функциям
import glob     #находит все пути, совпадающие с заданным шаблоном 
import time     #Модуль для работы со временем
import threading    #Модуль для работы с потоками

#os.system('modprobe w1-gpio')
#os.system('modprobe w1-therm')

#Класс исключения отсутствия наличия шины 1-wire
class NoOneWireError(Exception):
    pass

#Класс исключения при отсутствии цифровых термометров на шине 1-wire
class NoDS18B20Error(Exception):
    pass

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
    return (os.path.basename(device_folder), temp_c)

class T(threading.Thread):
    '''Класс для получения температуры от одного цифрового термометра'''
    def __init__(self, device_folder):
        '''Инициализация класса'''
        threading.Thread.__init__(self)
        self._device_folder = device_folder
        self._T = None
    def run(self):
        '''Функция, вызываемая при старте потока'''
        self._T = read_temp_raw(self._device_folder)
    @property
    def T(self):
        """Возвращает текущее значение температуры"""
        return self._T
    
#Возвращает кортеж из списка кортежей названий термометров с температурами
#и временем измерения
def Measure():
    '''Функция Measure() ищет все цифровые термометры DS18B20 на шине 1-wire
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
        eashT.join()

    #Сбор значений температур термометров
    for eashT in Threads:
        DS18B20list.append(eashT.T)

    #Выдача результатов
    return (DS18B20list, time.time())

def main():
    t=0
    tMax=0
    for i in range(1, sys.maxsize):
        timeBegin=time.time()
        (DS18B20list, tMeasure)=Measure()
        os.system('clear')
        for DS18B20 in DS18B20list:
            print(u"%s\t%3.1f градC" % DS18B20)
        print(u'Время измерения=%ssec' % (tMeasure-timeBegin))
        t+=(tMeasure-timeBegin)
        print(u'Среднее время измерения=%ssec' % (t/i))
        if (tMax<(tMeasure-timeBegin)):
              tMax=(tMeasure-timeBegin)
        print(u'(mt)Максимальная продолжительность измерения=%ssec' % tMax)
        print('')

if __name__ == '__main__':
    main()

        
