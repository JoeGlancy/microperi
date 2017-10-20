# utils.py
# Part of MicroPeri https://github.com/c0d3st0rm/microperi
#
# See LICENSE file for copyright and license details

import os
import sys
from time import sleep
os.sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import microperi
from serial.tools.list_ports import comports as list_serial_ports

def connected_microbits():
    """
    Based on code from https://github.com/ntoll/microrepl
    Returns a list of connected micro:bit port addresses (format is system
    dependent).
    """
    ports = list_serial_ports()
    platform = sys.platform
    results = []
    if platform.startswith("linux"):
        for port in ports:
            if "VID:PID=0D28:0204" in port[2].upper():
                results.append(port[0])
    elif platform.startswith("darwin"):
        for port in ports:
            if "VID:PID=0D28:0204" in port[2].upper():
                results.append(port[0])
    elif platform.startswith("win"):
        for port in ports:
            if "VID:PID=0D28:0204" in port[2].upper():
                results.append(port[0])
    return results

def identify_microbit(instance):
    """
    This routine will flash the micro:bit's display once (to visualy aid
    identifying it if multiple devices are connected to the system), and return
    its path as a string (/dev/ttyACMX on Linux systems, COMX on Windows, etc).
    `instance` must be an instance of "microperi.Microbit".
    The "flash" itself is essentially:
     - turn the LEDs (on the display) on
     - wait a second
     - turn the LEDs off
    """
    if not isinstance(instance, microperi.Microbit):
        return
    instance.display.show(instance.Image("99999:99999:99999:99999:99999"))
    sleep(1)
    instance.display.show(instance.Image("00000:00000:00000:00000:00000"))
    return instance._ubit_conn.conn.port
