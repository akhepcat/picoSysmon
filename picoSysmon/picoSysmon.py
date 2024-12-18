# Python Standard
import gc
import os
import re
import requests
import socket
from sys import exit
from time import sleep, mktime, gmtime

# MicroPython specific
try: import network
except: print("Can't import network")
try: from machine import ADC, Pin, Timer, freq, reset, mem32, I2C
except: print("Can't import machine")

# Other libraries
try: from BME680 import bme680
except: print("Can't import bme680")


class picoSysmon:
    """ This is the meat and the potatoes.

        picoSysmon is a tiny implementation of the sysmon project to monitor server data

        It currently supports CPU temp, storage space, and memory use.

        Other trackable items may appear in the future
     """

    def __init__(self, 
                debug: bool, 
                ssid: str, 
                psk: str, 
                country: str, 
                url: str, 
                token: str, 
                hostname: str,
                bmesda: int,
                bmescl: int,
                logfile: str
                ) -> None:
        # Set self vars from main first
        self.SSID = ssid
        self.PSK = psk
        self.INFLUXURL = url
        self.HOSTNAME = hostname
        self.wlan = network.WLAN(network.STA_IF)
        self.startup = self.__now()
        self.tempcache = 0
        self.prescache = 0
        self.debug = debug
        self._logfile = logfile
        if (int(bmesda)):
            self.bmesda = int(bmesda)
        else:
            self.bmesda = 0
        if (bmescl):
            self.bmescl = int(bmescl)
        else:
            self.bmescl = 0

        # Always debug when the USB serial console is detected (this is not quite working)
#        if self.__usbDetect():
#            self.__logprt("Console debugging detected and enabled")
#            self.debug = 1

        if re.search(r"\{MAC\}", hostname):
            MAC = self.wlan.config('mac').hex(":")
            MAC = MAC.replace(":","")
            MAC = MAC[6:]
            self.__logprt(f"updating hostname with mac: {MAC}")
            self.HOSTNAME = self.HOSTNAME.replace("{MAC}", MAC)

        if (token is None) or (token == ""):
            self.headers = {
                "Content-Type": "application/octet-stream",
            }
        else:
            self.headers = {
                "Authorization": f"{token}",
                "Content-Type": "application/octet-stream",
            }

        # Now set global vars
        # configure the network data appropriately the first time
        network.country(country)
        network.hostname(self.HOSTNAME)
        self.__logprt(f"My hostname is: {self.HOSTNAME}")

        # Last, set non-user self vars
        self.temp_sensor = ADC(ADC.CORE_TEMP)    # more portable across microcontrollers

        self.ip = None
        self.webtimeouts = 0

        self.led = Pin("LED", Pin.OUT)
        self.blink = Timer()


    def __now(self):
        return( mktime(gmtime()) )

    def __logprt(self, line: str):
        if self.debug:
            print(str(self.__now()) + ': ' + line)
        if self._logfile:
            lfile = open(self._logfile, "a")
            lfile.write(str(self.__now()) + ': ' + line + '\n')
            lfile.flush()
            lfile.close()


    def __usbDetect(self):
        USBCTRL_REGS_BASE = 0x50110000
        SIE_STATUS_REG = USBCTRL_REGS_BASE + 0x50
        SIE_CONNECTED  = 1 << 16
        SIE_SUSPENDED  = 1 << 4
        usbConnected   = (mem32[SIE_STATUS_REG] & (SIE_CONNECTED | SIE_SUSPENDED))
        self.__logprt(f"usbConnected = {usbConnected}")
        if ((usbConnected | SIE_CONNECTED) == SIE_CONNECTED ) or ((usbConnected | SIE_SUSPENDED) == SIE_SUSPENDED):
            return(True)
        else:
            # no usb detected
            return(False)


    def __blinken(self,timer):
        self.led.toggle()


    def __connect(self):
        tries = 0
        # Connect to the WLAN
        while tries < 5:
            sleeps = 0
            self.wlan.active(True)
            self.wlan.connect(self.SSID, self.PSK)
            while sleeps < 5:
                if self.wlan.isconnected() == True:
                    self.ip = self.wlan.ifconfig()[0]
                    self.__logprt(f'Connected on {self.ip}')
                    return self.wlan
                sleeps += 1
                sleep(1)
            self.wlan.active(False)
            sleep(1)
            tries += 1
        # Can't get connected to the wifi after 5 attempts, so full reset
        reset()
                


    def __post_data(self, data):
        self.__logprt(f"posting data to influxdb...\n{data}")
        try:
            response = requests.post(self.INFLUXURL, headers=self.headers, data=data, timeout=5)
        except:
            self.webtimeouts += 1
            self.__logprt(f"timeout #{self.webtimeouts} sending data to influxdb")
            return(False)
        if response.status_code == 204:
            self.__logprt("Data posted successfully")
            # assume that a success resets things
            self.webtimeouts = 0
            ret = True
        else:
            self.__logprt(f"Failed to post data! http status Code is {response.status_code}")
            self.__logprt("Response text was:\n{response.text}")
            ret = False
        response.close()
        return(ret)


    def __update_mem(self):
        self.__logprt("updating mem info")
        free = gc.mem_free()
        used = gc.mem_alloc()
        max = used + free
        self.__logprt(f"memory is using {used} bytes out of {max}")
        data = f"memory,host={self.HOSTNAME} totalmem={max}\n" + f"memory,host={self.HOSTNAME} usedmem={used}\n" + f"memory,host={self.HOSTNAME} freemem={free}"
        return(data)


    def __update_disk(self):
        self.__logprt("updating disk info")
        s = os.statvfs('//')
        self.__logprt(f"statvfs returns {s}")
        max = ( s[0]*s[2] )
        free = ( s[0]*s[3] )
        used = max - free
        self.__logprt(f"disk is using {used} bytes out of {max}, with {free} remaining")
        data = f"disk_usage,host={self.HOSTNAME},drive=flash,mount=/ size={max}\n" + f"disk_usage,host={self.HOSTNAME},drive=flash,mount=/ free={free}"
        return(data)


    def __update_temp(self):
        self.__logprt("updating temp info")
        # Read the raw ADC value
        adc_value = self.temp_sensor.read_u16()
        # Convert ADC value to voltage
        voltage = adc_value * (3.3 / 65535.0)
        # Temperature calculation based on sensor characteristics
        temp = 27 - (voltage - 0.706) / 0.001721
        temp = temp * 1000  # we scale in grafana
        self.__logprt(f"Read temp: {temp}C")
        data = f"thermals,host={self.HOSTNAME},zone=cpu temp={temp}"
        return(data)


    def __update_uptime(self):
        self.__logprt("updating uptime info")
        self.uptime = self.__now() - self.startup
        self.__logprt(f"uptime: {self.uptime} seconds")
        data = f"system,host={self.HOSTNAME} uptime={self.uptime}"
        return(data)


    def __update_sensors(self):
        minpress = 630    # set this for your minimum expected, with a margin
        if (self.bmesda > 0):
            self.__logprt("updating sensor info")
            try:
                bme = bme680.BME680_I2C( I2C(id=0, scl=Pin(self.bmescl), sda=Pin(self.bmesda) ), debug=False )
            except:
                return("")

            if bme.detected is False:
                return("")

#            temp = bme.temperature
#            if temp is None:
#                self.__logprt("BME680: oh, we got none temp value")
#                return("")
            for _ in range(3):              # take 3 measurements for stability, and use the last one
                temp=bme.temperature
                humid=bme.humidity
                press=bme.pressure
                voc=bme.gas
                sleep(1)

            # roll these to 2 decimal places
            temp = round((temp / 5 * 9) + 32, 2)  # Convert to Fahrenheit
            humid = round(humid, 2)               # percent
            press = round(press, 2)               # hPa
            voc = round(voc, 2)                   # inverse VOC concentration of ethanol, CO, etc.: high resistance=low concentration

            if press < minpress:    # this would be lower than "human comfortable" but if you're putting this on a high-altitude baloon, it might be too high
                self.__logprt(f"press returned invalid: {press}")
            self.__logprt(f"temp: {temp}  humidity: {humid}  press: {press}  voc: {voc}")
            data = f"environmental,host={self.HOSTNAME} temp={temp}\n" + f"environmental,host={self.HOSTNAME} humid={humid}\n" + f"environmental,host={self.HOSTNAME} voc={voc}\n" + f"environmental,host={self.HOSTNAME} press={press}"
            return(data)
        else:
            return("")


    def run(self):
        try:
            while True:
                # Wifi Setup (each time!)
                self.blink.init(freq=25, mode=Timer.PERIODIC, callback=self.__blinken)    # freq is events per second
                self.__logprt("Connecting to wifi")
                self.__connect()
                sleep(2)     # let things stabilize
                self.blink.deinit()

                # Update influxDB
                self.blink.init(freq=10, mode=Timer.PERIODIC, callback=self.__blinken)
                temps = self.__update_temp()
                mems = self.__update_mem()
                disks = self.__update_disk()
                uptime = self.__update_uptime()
                sensors = self.__update_sensors()
                mydata = temps + "\n" + mems + "\n" + disks + "\n" + uptime + '\n'
                if (self.bmesda > 0 ):
                    mydata = mydata + sensors + '\n'
                self.__post_data(mydata)
                # Make sure we don't have too many web timeouts in a row
                # to work around a connect but with micropython
                if self.webtimeouts > 3:
                    reset()
                sleep(2)    # might as well rest a bit here, too
                self.blink.deinit()

                # Kill the wifi, then sleep between loops
                self.__logprt("Deactivating wifi")
                self.wlan.disconnect()
                self.wlan.active(False)
                self.blink.init(freq=1, mode=Timer.PERIODIC, callback=self.__blinken)
                sleeps = ( 60 * 5 )
                if self.debug:
                    sleeps = 60
                self.__logprt(f"sleeping for {sleeps} seconds")
                gc.collect()
                sleep(sleeps)
                self.blink.deinit()

        except KeyboardInterrupt:
            if (self.__usbDetect()):
                # This should quit back to Thonny
                self.__logprt("I'm halting for you...")
                exit(0)
            else:
                # This shouldn't occur, but just returns back to main()
                return(0)

