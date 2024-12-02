#!/bin/python3
import sys
try:
    import secrets.CONFIG as CONFIG
except:
    print("Can't import module secrets.CONFIG")
    exit(1)

try:
    from picoSysmon.picoSysmon import  picoSysmon
except:
    print("Can't import module picoSysmon")
    exit(1)

if __name__  == "__main__":
    sysmon = picoSysmon(CONFIG.DEBUG, CONFIG.SSID, CONFIG.PSK, CONFIG.COUNTRY, CONFIG.INFLUXURL, CONFIG.TOKEN, CONFIG.HOSTNAME)
    sysmon.run()
    exit(0)

