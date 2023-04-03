#!/bin/bash
# Скрипт разворачивания проекта Distiller
# Запуск: bash setupDistiller.sh

#Переименование предыдущего конфигурационного файла
mv -f "/home/pi/Distiller/configDistiller.json" "/home/pi/Distiller/preconfigDistiller.json"

#Скачивание архива программы
wget https://github.com/Vagor-ru/Distiller/blob/Distiller3/Distiller/Distiller.zip

#Распаковка архива
unzip -u "Distiller.zip" -d "/home/pi/Distiller"

#удаление установочных файлов
rm "Distiller.zip"
rm "setupDistiller.sh"

#Создание виртуального окружения
python3 -m venv "/home/pi/Distiller/env"

#Активация и наполнение виртуального окружения
cd "/home/pi/Distiller"
source "env/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt
#mv "/home/pi/Desktop/startDistiller.sh /home/pi/Distiller"

#Копирование файла автозапуска сервера
sudo cp 'distiller.service' '/etc/systemd/system/'

#Копирование файла запуска браузера в меню
sudo cp 'distiller.desktop' '/home/pi/.local/share/applications/'

#Перезагрузка
sudo reboot