#!/bin/bash
sudo dpkg -i telegraf_1.8.1-1_amd64.deb
sudo dpkg -i influxdb_1.6.3_amd64.deb
sudo dpkg -i chronograf_1.6.2_amd64.deb
sudo dpkg -i kapacitor_1.5.1_amd64.deb
#start kapacitor daemon
sudo kapacitord &
kapacitor define sensor_fusion -tick sensor_fusion.tick
#generate day's worth of data
chmod +x ./generate_data.py
./generate_data.py
#insert data into influx database
mycurrentdir=$(pwd)
datafile="$mycurrentdir/sensor_data.dat"
echo $datafile
influx -import -path=$datafile -precision=s

