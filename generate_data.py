#!/usr/bin/python2

from numpy import random
from datetime import timedelta, datetime
import sys
import time
import requests


# Target temperatures in C
temperature = 220
pressure = 1100
humidity = 70

# Connection info
write_url = 'http://localhost:9092/write?db=printer&rp=autogen&precision=s'
measurement = 'sensor_fusion'

def temp(target, sigma):
    """
    Pick a random temperature from a normal distribution
    centered on target temperature.
    """
    return random.normal(target, sigma)

def main():
    temperature_sigma = 0
    pressure_sigma = 0
    humidity_sigma = 0
    temperature_offset = 0
    pressure_offset = 0
    humidity_offset = 0

    # Define some anomalies by changing sigma at certain times
    # list of sigma values to start at a specified iteration
    temperature_anomalies =[
        (0, 0.1, 0), # normal sigma
        (3600, 3.0, -1.5), # at one hour the temperature goes bad
        (3900, 0.1, 0), # 5 minutes later recovers
    ]
    pressure_anomalies =[
        (0, 0.1, 0), # normal sigma
        (28800, 5.0, 2.0), # at 8 hours the pressure goes bad
        (29700, 0.1, 0), # 15 minutes later recovers
    ]
    humidity_anomalies = [
        (0, 0.1, 0), # normal sigma
        (10800, 5.0, 0), # at 3 hours humidity starts to fluctuate more
        (43200, 10.0, -5.0), # at 12 hours humidity goes really bad
        (45000, 5.0, 0), # 30 minutes later recovers
        (72000, 0.1, 0), # at 20 hours goes back to normal
    ]

    # Start from 2018-10-14 00:00:00 UTC
    # This makes it easy to reason about the data later
    now = datetime(2018, 10, 14)
    second = timedelta(seconds=1)
    epoch = datetime(1970,1,1)

    # InfluxDB header
    ddl = '# DDL'
    createScript = 'CREATE DATABASE iot1'
    dml = '# DML'
    context = '# CONTEXT-DATABASE: iot1' 

    # 24 hours of temperatures once per second
    points = []
    pointsDb = []

    # Add influxDb headers
    pointsDb.append(ddl)
    pointsDb.append(createScript)
    pointsDb.append(dml)
    pointsDb.append(context)

    # 24 hours of temperatures once per second
    for i in range(60*60*24+2):
        # update sigma values
        if len(temperature_anomalies) > 0 and i == temperature_anomalies[0][0]:
            temperature_sigma = temperature_anomalies[0][1]
            temperature_offset = temperature_anomalies[0][2]
            temperature_anomalies = temperature_anomalies[1:]

        if len(pressure_anomalies) > 0 and i == pressure_anomalies[0][0]:
            pressure_sigma = pressure_anomalies[0][1]
            pressure_offset = pressure_anomalies[0][2]
            pressure_anomalies = pressure_anomalies[1:]

        if len(humidity_anomalies) > 0 and i == humidity_anomalies[0][0]:
            humidity_sigma = humidity_anomalies[0][1]
            humidity_offset = humidity_anomalies[0][2]
            humidity_anomalies = humidity_anomalies[1:]

        # generate temps
        currentTemperature = temp(temperature+temperature_offset, temperature_sigma)
        currentPressure = temp(pressure+pressure_offset, pressure_sigma)
        currentHumidity = temp(humidity+humidity_offset, humidity_sigma)
        points.append("%s temperature=%f,pressure=%f,humidity=%f %d" % (measurement, currentTemperature, currentPressure, currentHumidity, time.time() + i))
        pointsDb.append("%s temperature=%f,pressure=%f,humidity=%f %d" % (measurement, currentTemperature, currentPressure, currentHumidity, time.time() + i))
        #now += second

    # Write data to file
    printerDataFile = open("sensor_data.dat", "w")
    printerDataFile.write('\n'.join(pointsDb))
    printerDataFile.close()


    # Write data to Kapacitor
    r = requests.post(write_url, data='\n'.join(points))
    print r.status_code
    if r.status_code != 204:
        print >> sys.stderr, r.text
        return 1
    return 0

if __name__ == '__main__':
    exit(main())