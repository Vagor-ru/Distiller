#!/bin/bash
# Скрипт разворачивания проекта Distiller
# Запуск: bash setupDistiller.sh

unzip -u Distiller.zip -d /home/pi/Distiller
python3 -m venv /home/pi/Distiller/env
cd /home/pi/Distiller
source env/bin/activate
pip install -r requirements.txt