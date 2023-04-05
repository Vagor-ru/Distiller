#!/bin/bash
# Скрипт разворачивания проекта Distiller
# Запуск: bash setupDistiller.sh

#Переименование предыдущего конфигурационного файла
mv -f "/home/pi/Distiller/configDistiller.json" "/home/pi/Distiller/preconfigDistiller.json"

#Скачивание архива программы
wget -O '/home/pi/Downloads/Distiller.zip' 'https://github.com/Vagor-ru/Distiller/blob/Distiller3/Distiller/Distiller.zip?raw=true'

#Распаковка архива
unzip -u "/home/pi/Downloads/Distiller.zip" -d "/home/pi/Distiller"

#удаление установочных файлов
#rm "/home/pi/Downloads/Distiller.zip"
#rm "setupDistiller.sh"

#Создание виртуального окружения
python3 -m venv "/home/pi/Distiller/env"

#Активация и наполнение виртуального окружения
cd "/home/pi/Distiller"
source "env/bin/activate"

#Обновление pip
pip install --upgrade pip

#Установка в виртуальное окружение необходимых пакетов
pip install -r requirements.txt
#mv "/home/pi/Desktop/startDistiller.sh /home/pi/Distiller"

#Копирование файла автозапуска сервера
sudo cp 'distiller.service' '/etc/systemd/system/'
#Разрешение запуска службы
sudo systemctl enable distiller

#Копирование файла запуска браузера в меню
sudo cp 'distiller.desktop' '/home/pi/.local/share/applications/'

#Перезагрузка
sudo reboot