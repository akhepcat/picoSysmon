try: import gc
except: print("Can't import gc")
try: import os
except: print("Can't import os")
try: import network
except: print("Can't import network")
try: import re
except: print("Can't import re")
try: import requests
except: print("Can't import requests")
try: import socket
except: print("Can't import socket")

try: from time import sleep
except: print("Can't import time")

try: from machine import ADC, Pin, Timer, freq, reset
except: print("Can't import machine")


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
                hostname: str
                ) -> None:
        # Set self vars from main first
        self.SSID = ssid
        self.PSK = psk
        self.INFLUXURL = url
        self.HOSTNAME = hostname
        self.debug = debug
        self.wlan = network.WLAN(network.STA_IF)

        if re.search(r"\{MAC\}", hostname):
            MAC = self.wlan.config('mac').hex(":")
            MAC = MAC.replace(":","")
            MAC = MAC[6:]
            print(f"updating hostname with mac: {MAC}")
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
        if self.debug: print(f"My hostname is: {self.HOSTNAME}")

        # Last, set non-user self vars
        self.temp_sensor = ADC(ADC.CORE_TEMP)	# more portable across microcontrollers

        self.ip = None
        self.webtimeouts = 0

        self.led = Pin("LED", Pin.OUT)
        self.blink = Timer()

#        gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())
#        gcthresh = gc.threshold()
#        gc.enable()
#        if self.debug: print(f"gc threshold: {gcthresh}  (-1 is disabled)")



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
                    print(f'Connected on {self.ip}')
                    return self.wlan
                sleeps += 1
                sleep(1)
            self.wlan.active(False)
            sleep(1)
            tries += 1
        # Can't get connected to the wifi after 5 attempts, so full reset
        reset()
                


    def __post_data(self, data):
        if self.debug: print("posting data to influxdb...")
        if self.debug: print(data)
        try:
            response = requests.post(self.INFLUXURL, headers=self.headers, data=data, timeout=5)
        except:
            self.webtimeouts += 1
            print(f"timeout #{self.webtimeouts} sending data to influxdb")
            return(False)
        if response.status_code == 204:
            if self.debug: print("Data posted successfully")
            # assume that a success resets things
            self.webtimeouts = 0
            ret = True
        else:
            print("Failed to post data:")
            if self.debug:
                print("Status Code:", response.status_code)
                print("Response:", response.text)
            ret = False
        response.close()
        return(ret)


    def __update_mem(self):
        if self.debug: print("updating mem info")
        free = gc.mem_free()
        used = gc.mem_alloc()
        max = used + free
        if self.debug: print(f"memory is using {used} bytes out of {max}")
        data = f"memory,host={self.HOSTNAME} totalmem={max}\n" + f"memory,host={self.HOSTNAME} usedmem={used}\n" + f"memory,host={self.HOSTNAME} freemem={free}"
        return(data)


    def __update_disk(self):
        if self.debug: print("updating disk info")
        s = os.statvfs('//')
        if self.debug: print(f"statvfs returns {s}")
        max = ( s[0]*s[2] )
        free = ( s[0]*s[3] )
        used = max - free
        if self.debug: print(f"disk is using {used} bytes out of {max}, with {free} remaining")
        data = f"disk_usage,host={self.HOSTNAME},drive=flash,mount=/ size={max}\n" + f"disk_usage,host={self.HOSTNAME},drive=flash,mount=/ free={free}"
        return(data)


    def __update_temp(self):
        if self.debug: print("updating temp info")
        # Read the raw ADC value
        adc_value = self.temp_sensor.read_u16()
        # Convert ADC value to voltage
        voltage = adc_value * (3.3 / 65535.0)
        # Temperature calculation based on sensor characteristics
        temp = 27 - (voltage - 0.706) / 0.001721
        temp = temp * 1000  # we scale in grafana
        if self.debug: print(f"Read temp: {temp}C")
        data = f"thermals,host={self.HOSTNAME},zone=cpu temp={temp}"
        return(data)


    def run(self):
        try:
            while True:
                # Wifi Setup (each time!)
                self.blink.init(freq=25, mode=Timer.PERIODIC, callback=self.__blinken)    # freq is events per second
                if self.debug: print("Connecting to wifi")
                self.__connect()
                sleep(2)		# let things stabilize
                self.blink.deinit()

                # Update influxDB
                self.blink.init(freq=10, mode=Timer.PERIODIC, callback=self.__blinken)
                temps = self.__update_temp()
                mems = self.__update_mem()
                disks = self.__update_disk()
                mydata = temps + "\n" + mems + "\n" + disks + "\n"
                self.__post_data(mydata)
                # Make sure we don't have too many web timeouts in a row
                # to work around a connect but with micropython
                if self.webtimeouts > 3:
                    reset()
                sleep(2)		# might as well rest a bit here, too
                self.blink.deinit()

                # Kill the wifi, then sleep between loops
                if self.debug: print("Deactivating wifi")
                self.wlan.disconnect()
                self.wlan.active(False)
                self.blink.init(freq=1, mode=Timer.PERIODIC, callback=self.__blinken)
                sleeps = ( 60 * 5 )
                if self.debug:
                    sleeps = 60
                if self.debug: print(f"sleeping for {sleeps} seconds")
                gc.collect()
                sleep(sleeps)
                self.blink.deinit()

        except KeyboardInterrupt:
        #    reset()
            print("I'm halting for you...")
            return(0)

