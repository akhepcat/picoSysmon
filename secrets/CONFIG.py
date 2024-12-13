""" These are the variables that you should set for your site """

SSID = ""
PSK = ""
COUNTRY = "XX"  # XX is worldwide, otherwise use your countries 2-char code
INFLUXURL = ""  # the full url for posting to your InfluxDB;  if you don't use a token, you must supply the user auth here
TOKEN = ""      # empty, string or None, but for influx v2, this is your API token; code will add it to the Headers if supplied
HOSTNAME = "mypico2w-{MAC}"   # regular hostname, or template with the mac address using the format "host-{MAC}"  where {MAC} will be automatically replaced inline

BME680_SDA = 0      # gpio pin number for BME680 data;  0 disables
BME680_SCL = 0      # gpio pin number for BME680 clock; 0 disables

# This prints a lot of debugging info to the console if true
DEBUG = True
