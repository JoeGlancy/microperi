# -*- coding: utf-8 -*-
"""
microperi.py
Part of MicroPeri https://github.com/JoeGlancy/microperi

See LICENSE file for copyright and license details

MicroPeri is a library for using the BBC micro:bit with MicroPython as an
external peripheral device or sensor, using an API which closely replicates
the micro:bit's MicroPython API.
"""
import time
import ast
from serial.tools.list_ports import comports as list_serial_ports
from serial import Serial


__all__ = ['microbit']


def find_microbit():
    """
    Finds the port to which the device is connected.
    """
    ports = list_serial_ports()
    for port in ports:
        if "VID:PID=0D28:0204" in port[2].upper():
            return port[0]
    return None


def get_connection():
    """
    Returns an object representing a serial connection to a BBC micro:bit
    attached to the host computer.

    Otherwise, raises IOError.
    """
    port = find_microbit()
    if port is None:
        raise IOError('Could not find micro:bit.')
    serial = Serial(port, 115200, timeout=1, parity='N')
    serial.write(b'\x04')  # Send CTRL-D for soft reset.
    time.sleep(0.1)
    serial.write(b'\x03')  # Send CTRL-C to break out of potential loop.
    time.sleep(0.1)
    serial.read_until(b'\r\n>')  # Flush buffer until prompt.
    time.sleep(0.1)
    serial.write(b'\x01')  # Go into raw mode.
    time.sleep(0.1)
    serial.read_until(b'\r\n>OK')  # Flush buffer until raw mode prompt.
    time.sleep(0.1)
    serial.write('import microbit'.encode('utf-8') + b'\x04')
    serial.read_until(b'\x04>')  # Flush buffer until prompt.
    time.sleep(0.1)
    return serial


def close_connection(serial):
    """
    Attempts to re-set the BBC micro:bit to a good state.

    Closes the serial connection if it's open already.

    Otherwise, do nothing.
    """
    if serial.is_open:
        serial.write(b'\x02')  # Send CTRL-B to get out of raw mode.
        time.sleep(0.1)
        serial.write(b'\x04')  # Finally, send CTRL-D for soft reset.
        time.sleep(0.1)
        serial.close()


def execute(command, serial):
    """
    Sends the command using the serial connection to a micro:bit and returns
    the result.

    Returns the stdout and stderr output from the micro:bit.
    """
    # Write the actual command and send CTRL-D to evaluate.
    serial.write(command.encode('utf-8') + b'\x04')
    result = bytearray()
    while not result.endswith(b'\x04>'):  # Read until prompt.
        time.sleep(0.1)
        result.extend(serial.read_all())
    out, err = result[2:-2].split(b'\x04', 1)  # Split stdout, stderr
    return out, err


class Shim:
    """
    A class that is a shim and makes child shims.

    This allows us to make a shim around the microbit module running on the
    BBC micro:bit.

    Far too many shims (although it makes the code very very shimple).
    """

    def __init__(self, name=None, connection=None):
        self.name = name
        self.connection = connection

    def open(self):
        if self.connection is None:
            self.connection = get_connection()
        if not self.connection.is_open:
            self.connection = get_connection()

    def close(self):
        close_connection(self.connection)

    def __call__(self, *args, **kwargs):
        # Positional args
        clean_args = []
        for arg in args:
            if isinstance(arg, str):
                clean_args.append('"{}"'.format(arg))
            elif isinstance(arg, Shim):
                clean_args.append(arg.name)
            else:
                clean_args.append(str(arg))
        arg_string = ', '.join(clean_args)
        # Named args
        clean_kwargs = []
        for k, v in kwargs.items():
            if isinstance(v, str):
                clean_kwargs.append('{}="{}"'.format(k, v))
            else:
                clean_kwargs.append('{}={}'.format(k, v))
        kwarg_string = ', '.join(clean_kwargs)
        complete_args = ', '.join([arg_string, kwarg_string])
        command = "print({}({}))".format(self.name, complete_args)
        print(command)
        out, err = execute(command, self.connection)
        if err:
            raise IOError(err)
        return ast.literal_eval(out.decode('utf-8'))

    def __getattr__(self, attr_name):
        return Shim('{}.{}'.format(self.name, attr_name), self.connection)

    def __enter__(self):
        self.open()

    def __exit__(self):
        self.close()


microbit = Shim('microbit')
