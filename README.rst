NOTE: This is the dev branch.
=============================

===============================
MicroPeri for the BBC micro:bit
===============================
MicroPeri is a quick and easy to use Python 3 library for turning the BBC Microbit into an external peripheral device or sensor for a normal Windows, Mac or Linux computer using MicroPython.

With it, you can quickly for example read accelerator values, button presses or even write to the LED matrix using the same API as is used with MicroPython.

Installation
============
1. You must first make sure you have a blank MicroPython .hex file loaded onto your Microbit. You can create one `here <https://www.microbit.co.uk/app/#create:xyelfe>`_.
2. If using Windows, you must have the ARM mbed USB serial driver installed. It can be downloaded from the `mbed site <https://developer.mbed.org/handbook/Windows-serial-configuration>`_.
3. Either install the library with (soon):

    # pip3 install microperi

Or just use it as a portable module with *zero* install. As long as the `microperi` directory is in the same one as your scripts which use it, you can use `import microperi` just as normal.

You also no longer need the Python 3 pyserial (serial) module installed on your system, as it comes bundled along with microperi (see `microperi/_portable_serial/LICENSE.txt <https://github.com/JoeGlancy/microperi/blob/master/microperi/_portable_serial/LICENSE.txt>`_ for the pyserial copyright notice).

Notes:
======
- Some functions and parts of the current micro:bit MicroPython API are not yet implemented - see the `issues page <https://github.com/JoeGlancy/microperi/issues>`_ for more information.
- If on Linux, you will need superuser priviledges to open the serial port, or your user needs to be in the `dialout` group.

Usage
=====
(outdated)
.. code-block:: python

    import microperi
    # try to find the micro:bit automatically
    device = microperi.Microbit()
    microbit = device.microbit
    microbit.display.scroll("Hello world")
    while True:
        # is button A currently being pressed?
        if microbit.button_a.is_pressed():
            print("Button A is pressed")
        else:
            print("Button A is not pressed")
        microbit.sleep(500)
