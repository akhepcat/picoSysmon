#!/bin/python3
from sys import exit

try:
    from BME680 import bme680
except:
    print("Can't import module bme680")
    pass

try: 
    from pmon.pmon import PlantMonitor
except:
    print("Can't import modules PlantMonitor from pmon")
    pass

try:
    from secrets import CONFIG
except:
    print("Can't import CONFIG")
    exit(1)

try:
    from picoSysmon.picoSysmon import picoSysmon
except:
    print("Can't import module picoSysmon")
    exit(1)

if __name__  == "__main__":
    if (CONFIG.SSID == "") or (CONFIG.SSID is None):
        print("ERROR: SSID not defined in secrets.CONFIG")
        exit(1)

    if (CONFIG.PSK == "") or (CONFIG.PSK is None):
        print("ERROR: WIFI PSK not defined in secrets.CONFIG")
        exit(1)

    if (CONFIG.COUNTRY == "") or (CONFIG.COUNTRY is None):
        print("ERROR: WIFI COUNTRY not defined in secrets.CONFIG")
        exit(1)

    if (CONFIG.INFLUXURL == "") or (CONFIG.INFLUXURL is None):
        print("ERROR: INFLUXURL not defined in secrets.CONFIG")
        exit(1)

    if (CONFIG.HOSTNAME == "") or (CONFIG.HOSTNAME is None):
        print("WARN: HOSTNAME not defined in secrets.CONFIG, using default 'pico2w'")
        CONFIG.HOSTNAME = "pico2w"

    sysmon = picoSysmon(CONFIG.DEBUG, CONFIG.SSID, CONFIG.PSK, CONFIG.COUNTRY, CONFIG.INFLUXURL, CONFIG.TOKEN, CONFIG.HOSTNAME, CONFIG.BME680_SDA, CONFIG.BME680_SCL, CONFIG.PLANTS, CONFIG.LOGFILE )
    sysmon.run()
    exit(0)
