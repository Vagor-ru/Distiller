#�������� ����� ����������� �������
sudo rm '/etc/systemd/system/distiller.service'

#�������� ����� ������� �������� � ����
sudo rm '/home/pi/.local/share/applications/distiller.desktop'

#�������� �������� distiller
rm -R '/home/pi/Distiller'

#������������
sudo reboot
