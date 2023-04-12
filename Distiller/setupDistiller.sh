#!/bin/bash
# Скрипт разворачивания проекта Distiller, команды в терминале
#Скачивание: 
#wget -O '/home/pi/Downloads/setupDistiller.sh' 'https://github.com/Vagor-ru/Distiller/raw/master/Distiller/setupDistiller.sh'
# Запуск: sudo bash '/home/pi/Downloads/setupDistiller.sh'
#можно и так:
# curl 'https://github.com/Vagor-ru/Distiller/raw/master/Distiller/setupDistiller.sh' | bash

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

#Distiller доработан для python3.9
#установка pyenv (это не нужно):
#curl https://pyenv.run | bash
#настройка pyenv:
#файл ~/.bashrc:
#echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
#echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
#echo 'eval "$(pyenv init -)"' >> ~/.bashrc
#файл ~/.profile:
#echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.profile
#echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.profile
#echo 'eval "$(pyenv init -)"' >> ~/.profile
#зависимости:
#sudo apt update; sudo apt install build-essential libssl-dev zlib1g-dev \
#libbz2-dev libreadline-dev libsqlite3-dev curl \
#libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

#---------------------------------------------нужно закрыть терминальное окно, команды ниже уже во вновь открытом окне

#установка python 3.8.7:
#pyenv install 3.8.7
#назначить глобальной эту версию: (нужно ли?)
#pyenv global 3.8.7

#Переименование предыдущего конфигурационного файла
#mv -f "/home/pi/Distiller/configDistiller.json" "/home/pi/Distiller/preconfigDistiller.json"

#Скачивание архива программы
sudo wget -O '/home/pi/Downloads/Distiller.zip' 'https://github.com/Vagor-ru/Distiller/raw/master/Distiller/Distiller.zip'

#Распаковка архива
unzip -u "/home/pi/Downloads/Distiller.zip" -d "/home/pi/Distiller"

#переход в рабочий каталог
cd "/home/pi/Distiller"

#создание локальной версии питона посредством pyenv (не нужно):
#pyenv local 3.8.7

#удаление установочных файлов
#rm "/home/pi/Downloads/Distiller.zip"
#rm "setupDistiller.sh"

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

#Перезагрузка
sudo reboot