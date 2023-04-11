#!/bin/bash
# Скрипт запуска Distiller
# Запуск: bash '/home/pi/Distiller/startDistiller.sh'

cd '/home/pi/Distiller'
source env/bin/activate
python runserver.py
