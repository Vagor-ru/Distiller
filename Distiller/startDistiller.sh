#!/bin/bash
# Скрипт запуска Distiller
# Запуск: bash startDistiller.sh

cd /home/pi/Distiller
source env/bin/activate
python3 runserver.py
