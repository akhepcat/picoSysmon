# picoSysmon

## About
a subproject of the System-Monitor project, specifically for Pi Pico devices
- currently tested on Pi Pico 2W

## Installation
This project contains submodules!

You can either:

    $ git clone --recurse-submodules https://github.com/akhepcat/picoSysmon

or

    $ git clone https://github.com/akhepcat/picoSysmon
    $ git submodule update --init --recursive


Now that you've got the repo cloned, you'll need to create a local config
file by copying the existing secrets/CONFIG.py  to secrets/CONFIG_local.py
and editing them.   CONFIG_local.py is not tracked by the git subsystem, so
you can leave it in your local repo without causing any issues.

Once you've edited your local CONFIG,  you can upload the entire directory
tree  (without the .git directories)  to your Pi Pico.  

It should run on reboot, and automatically restart itself if there are any
issues.

You can always plug it back into your computer for debugging.

Otherwise, throw it somewhere with USB-micro delivered 5v power, and enjoy
your remote sensor!

## Supported Sensors

- Raspberry PI Pico onboard temperature
- BME 680 temperature, humidity, pressure, volatile gas
- Monk Makes Plant Monitor

## Future Work

- Add additional sensors
- ??? profit ???
