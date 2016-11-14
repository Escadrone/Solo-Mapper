#!/bin/sh
# launcher.sh
# navigate to home directory,then update logs files with logrotate, then navigate  to this directory, then execute python script, then back home

cd /
sudo /etc/cron.daily/logrotate
cd home/pi/Solo-Mapper
sleep 2
sudo python SoloMapper.py
cd /
