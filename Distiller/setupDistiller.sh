#!/bin/bash
# Скрипт разворачивания проекта Distiller
# Запуск: bash setupDistiller.sh

#Настройка конфигурации raspberry pi
#отключить оверскан у дисплея
sudo raspi-config nonint do_overscan 1
#разрешение экрана 800х600 60Гц 4:3
#sudo raspi-config nonint do_resolution 6 0
#разрешить VNC
sudo raspi-config nonint do_vnc 0
#разрешить I2C
sudo raspi-config nonint do_i2c 0
#разрешить 1-wire
sudo raspi-config nonint do_onewire 0
#

#Переименование предыдущего конфигурационного файла
mv -f "/home/pi/Distiller/configDistiller.json" "/home/pi/Distiller/preconfigDistiller.json"

#Скачивание архива программы
wget -O '/home/pi/Downloads/Distiller.zip' 'https://github.com/Vagor-ru/Distiller/raw/master/Distiller/Distiller.zip'

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