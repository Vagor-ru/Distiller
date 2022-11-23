#!/bin/bash
# Скрипт разворачивания проекта Distiller
# Запуск: bash setupDistiller.sh

#Переименование предыдущего конфигурационного файла
mv -f /home/pi/Distiller/configDistiller.json /home/pi/Distiller/preconfigDistiller.json

#Распаковка архива
unzip -u Distiller.zip -d /home/pi/Distiller


#Создание виртуального окружения
python3 -m venv /home/pi/Distiller/env

#Активация и наполнение виртуального окружения
cd /home/pi/Distiller
source env/bin/activate
pip install -r requirements.txt
mv /home/pi/Desktop/startDistiller.sh /home/pi/Distiller
rm /home/pi/Desktop/setupDistiller.sh
rm /home/pi/Desktop/Distiller.zip
