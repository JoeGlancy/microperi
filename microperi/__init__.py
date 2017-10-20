# __init__.py
# Part of MicroPeri https://github.com/c0d3st0rm/microperi
#
# See LICENSE file for copyright and license details

__name__ = "microperi"
__microperi_version__ = [0, 1, 0] # major, minor, patch
__microperi_version_str__ = "v%d.%d.%d" % \
    (__microperi_version__[0], __microperi_version__[1], __microperi_version__[2])

from microperi.microperi import Microbit
import microperi.utils as utils
