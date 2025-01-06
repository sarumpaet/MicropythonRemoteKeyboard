# RP Pico/Micropython remote keyboard
https://github.com/sarumpaet/MicropythonRemoteKeyboard

## About

This is a poor man's **KVM over IP**.
It is so poor that it misses the "V" and "M" (there's no video nor mouse support).
On the upside, it doesn't only do IP but even Wifi!
So call it **K over Wifi** if you want.
Which perfectly describes it! ***Keyboard over Wifi***.

Why, you ask?

There are other solutions that allow you to remote control a PC, including video transmission, mouse, etc., but those are a tad expensive and a bit of a hassle to set up.

Instead, this project assumes that you have remote hands, but also assumes that those hands have their hands full with connecting the remote keyboard hardware, and using some smartphone based video chat software for transmitting the screen contents to you.

You can even set up the USB stick (configuring network parameters is all that's necessary) and then mail in a small envelope.

Once plugged into the PC, the stick will...
1. connect to Wifi
2. TCP connect to an IP of your choice that runs the keyboard events emitter software
3. send events received as USB HID keyboard events to the PC it is connected to physically.

You can even control the UEFI/BIOS this way.²

No VPN needed, no bulky KVM solution needed, total cost <10€.

## Hardware

This thing uses RP2040 hardware combined with an ESP running the ESP-AT firmware connected to the UART lines of the RP2040.
You can get this hardware prebuild as a Raspberry Pi Pico lookalike, branded as "Pico W-2023" (which is slightly misleading as the real Pico W uses the CYW43 chip for wifi connectivity).
Note that the Pico W-2023 often ships with the ESP-AT firmware not yet flashed onto the ESP.
You have to flash `Serial_port_transmission.uf2` onto the RP2040 then reset with the ESP boot button pressed then flash the ESP with a 1MBit ESP-AT firmware.

It should be simple to port this to the real Pico W as well.

## Installation and Usage

1. Install MicroPython onto the Pico/RP2040.
2. Install `mpremote` on your PC.
3. `mpremote mip install usb-device-keyboard`
4. Install the remote keyboard into MicroPython: `mpremote cp keyboard.py :main.py`
5. Configure Wifi and server settings: `mpremote edit main.py`
6. Connect the stick to the PC you want to control
7. Launch the keyboard event server: `python event_server.py`
8. As long as the mouse is in the event server window, any keypresses are sent to the remote.

There are a few buttons in the software for common key combinations.
The red button will send Magic SysRq to reboot.

The event server software must be reachable for TCP inbound connections originating from the stick.
As an easy solution, you can configure the stick to connect to some host you control that has a public IP, then connect to that from the machine running the event server using `ssh -R 0.0.0.0:PORT:127.0.0.1:PORT publichost` or similar.

## Troubleshooting

* Remote stick blinks 10 times: ESP could not get initialized (missing ESP-AT firmware or broken).
* Remote stick blinks 6 times: PC did not initialize stick as keyboard (power only cable?).
* Remote stick blinks 4 times: ESP could not connect to Wifi (wrong credentials?).
* Remote stick blinks 2 times: Could not connect to event server (server not yet started or missing connectivity).
* Remote stick blinks rapidly: All fine, connected to event server.

## Caveats

* This is barely more than a proof of concept. You have been warned.
* There is no connection security/encryption. People might listen to any keypresses transmitted, or forge keypresses. Only connect the stick when needed, and don't enter passwords over the remote.
* ²There seems to be a minor bug in the MicroPython HID code - the keyboard endpoint seems to have protocol set to NONE by default so some BIOSes don't recognize the stick. Patch hid.py to fix.
