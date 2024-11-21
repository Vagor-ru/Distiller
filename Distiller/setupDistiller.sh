#!/bin/bash
# Скрипт разворачивания проекта Distiller, команды в терминале
#Скачивание: 
#wget -O '/home/pi/Downloads/setupDistiller.sh' 'https://github.com/Vagor-ru/Distiller/blob/Top_PID/Distiller/setupDistiller.sh'
# Запуск: sudo bash '/home/pi/Downloads/setupDistiller.sh'

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

#Скачивание архива программы
#sudo wget -O '/home/pi/Downloads/Distiller.zip' 'https://github.com/Vagor-ru/Distiller/raw/Top_PID/Distiller/Distiller.zip'
sudo wget -O '/home/pi/Downloads/Distiller.zip' 'https://github.com/Vagor-ru/Distiller/archive/refs/heads/Top_PID.zip'


#Распаковка архива
#unzip -u "/home/pi/Downloads/Distiller.zip" -d "/home/pi/Distiller"
unzip '/home/pi/Downloads/Distiller.zip' -d '/home/pi/'
mv '/home/pi/Distiller-master/Distiller/' '/home/pi/'
rm -R '/home/pi/Distiller-master/'

#переход в рабочий каталог
cd "/home/pi/Distiller"

#Обновление pip
pip install --upgrade pip

#создание виртуальной среды venv (env - название виртуального каталога)
python -m venv env
#активация виртуальной среды
source env/bin/activate
#деактивация виртуальной среды
#deactivate

#Установка в виртуальное окружение необходимых пакетов
pip install -r requirements.txt

#Копирование файла автозапуска сервера
sudo cp 'distiller.service' '/etc/systemd/system/'
#Разрешение запуска службы
sudo systemctl enable distiller

#Копирование файла запуска браузера в меню
sudo cp 'distiller.desktop' '/home/pi/.local/share/applications/'
#Копирование пункта удаление
sudo cp 'delDistiller.desktop' '/home/pi/.local/share/applications/'

#Перезагрузка
sudo reboot