#Удаление файла автозапуска сервера
sudo rm '/etc/systemd/system/distiller.service'

#Удаление файла запуска браузера в меню
sudo rm '/home/pi/.local/share/applications/distiller.desktop'

#Удаление каталога distiller
rm -R '/home/pi/Distiller'

#Перезагрузка
sudo reboot
