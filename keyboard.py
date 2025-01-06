ssid = 'YOURSSID'
password = 'YOURPASSWORD'
remote_name = 'Remote1'

server_name = 'EVENTSERVERNAME'  # that thing must accept inbound connections to event_source.py
server_port = '9999'  # event server port

# Micropython Remote Keyboard
# https://github.com/sarumpaet/MicropythonRemoteKeyboard

# based on MicroPython USB Keyboard example
# * Make sure `usb-device-keyboard` is installed via: mpremote mip install usb-device-keyboard
# * Run the example via: mpremote run keyboard.py
# * mpremote will exit with an error after the previous step, because when the
#   example runs the existing USB device disconnects and then re-enumerates with
#   the keyboard interface present. At this point, the example is running.
# USB Keyboard example: MIT license; Copyright (c) 2024 Angus Gratton
import usb.device
from usb.device.keyboard import KeyboardInterface, KeyCode, LEDCode
from machine import UART, Pin
import time, utime

esp_uart = UART(0, 115200)

def esp_sendCMD(cmd,ack,timeout=2000):
    esp_uart.write(cmd+'\r\n')
    i_t = utime.ticks_ms()
    while (utime.ticks_ms() - i_t) < timeout:
        s_get = esp_uart.read()
        if(s_get != None):
            s_get=s_get.decode()
            print(s_get)
            if(s_get.find(ack) >= 0):
                return True
            if(s_get.find("\nERROR") >= 0):
                return False
    return False

def esp_connect_wifi():
    esp_uart.write('+++')
    time.sleep(1)
    if(esp_uart.any() > 0):
        esp_uart.read()
    esp_sendCMD("AT", "OK")
    if not esp_sendCMD("AT+CWMODE=3", "OK"):
        return -10
    if not esp_sendCMD(f"AT+CWJAP=\"{ssid}\",\"{password}\"", "OK", 20000):
        return -4
    esp_sendCMD("AT+CIFSR","OK")
    return 1

def esp_connect_tcp():
    if not esp_sendCMD(f"AT+CIPSTART=\"TCP\",\"{server_name}\",{server_port}", "OK", 10000):
        return -2
    esp_sendCMD("AT+CIPMODE=1", "OK")
    esp_sendCMD("AT+CIPSEND", ">")
    esp_uart.write(f"remote_keyboard {remote_name} connected!\r\n")
    return 1

def error_blink(count, msg):
    print(msg)
    for _ in range(count):
        Pin.board.LED(1)
        time.sleep(0.3)
        Pin.board.LED(0)
        time.sleep(0.3)
    time.sleep(1)

FIXUP_MAP = {
  224: KeyCode.LEFT_CTRL,
  225: KeyCode.LEFT_SHIFT,
  226: KeyCode.LEFT_ALT,
  227: KeyCode.LEFT_UI,
  228: KeyCode.RIGHT_CTRL,
  229: KeyCode.RIGHT_SHIFT,
  230: KeyCode.RIGHT_ALT,
  231: KeyCode.RIGHT_UI,
}

def keyboard_loop():
    Pin.board.LED.init(Pin.OUT, value=0)

    # Register the keyboard interface and re-enumerate
    k = KeyboardInterface()
    usb.device.get().init(k, builtin_driver=True)

    print("Entering keyboard loop...")

    keys = []  # Keys held down, reuse the same list object
    prev_keys = [None]  # Previous keys, starts with a dummy value so first
    # iteration will always send
    in_buffer = []
    connect_status = -100
    while True:
        if connect_status <= -4:
            connect_status = esp_connect_wifi()
            if connect_status == 1:
                connect_status = -2
        if connect_status == -2:
            connect_status = esp_connect_tcp()
        if connect_status < 0:
            error_blink(-connect_status, f"Could not connect: {-connect_status}")
            time.sleep_ms(1000)
            continue
        # TODO monitor Wifi and TCP connection

        if k.is_open():
            while (i_s := esp_uart.read()) is not None:
                Pin.board.LED(1)
                for i in i_s:
                    in_buffer.append(i)
            if 0 in in_buffer:
                keys.clear()
                while (c := in_buffer.pop(0)) != 0:
                    if c in FIXUP_MAP:
                        c = FIXUP_MAP[c]
                    keys.append(c)
            else:
                Pin.board.LED(0)

            if keys != prev_keys:
                print(keys)
                k.send_keys(keys)
                prev_keys.clear()
                prev_keys.extend(keys)
        else:
            error_blink(6, "PC not connected")

        # This simple example scans each input in an infinite loop, but a more
        # complex implementation would probably use a timer or similar.
        time.sleep_ms(1)

keyboard_loop()
