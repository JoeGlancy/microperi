# microperi.py
# Part of MicroPeri https://github.com/c0d3st0rm/microperi
#
# See LICENSE file for copyright and license details

# MicroPeri is a library for using the BBC micro:bit with MicroPython as an
# external peripheral device or sensor, using an API which closely replicates
# the micro:bit's MicroPython API.

import sys

if __name__ == "__main__":
    # this shouldn't be run as a file
    print("Use me as a module:\n    from microperi import Microbit" % (name))
    sys.exit(1)

import os
import pickle
# make sure we import from our local serial package
os.sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import serial
import utils
from time import sleep as delaysecs

from logging import debug, info, warning, basicConfig, INFO, DEBUG, WARNING

basicConfig(level=INFO)

class _microbit_connection:
    """
    Class which handles the sending and receiving of data to and from the
    micro:bit over the serial connection.
    """
    conn = None

    def __init__(self, port=None, reraise_exceptions=False):
        """
        Constructor. Attempts to find the micro:bit, and raises an Exception
        if one can't be found. If one is found, but there is an error connecting
        to it, depending on the error (and platform), microperi may output a
        message to stderr, and then raise an exception.
        """
        if not isinstance(port, str):
            port = self.guess_port()
            if port is None:
                raise Exception("Could not find micro:bit!")
        try:
            self.conn = serial.Serial(port, 115200, timeout=1)
        except serial.SerialException as e:
            if e.errno == 13:
                # possible invalid priviledges for the current user?
                print("\nmicro:bit located, but permission to connect to it was denied.", file=sys.stderr)
                if sys.platform.startswith("linux"):
                    import pwd
                    print("Perhaps your user account does not have sufficient privileges to open the serial connection? Try running the command:", file=sys.stderr)
                    print("    sudo usermod -a -G dialout %s" % (pwd.getpwuid(os.getuid()).pw_name), file=sys.stderr)
                    print("Then log out, log back in, and see if that works.\n", file=sys.stderr)
                else:
                    print("")
                if reraise_exceptions:
                    raise e
                sys.exit(1)
            elif e.errno == 16:
                # device busy
                print("\nmicro:bit located, but it seems to be busy. This can happen if another program is attempting to communicate with it at the same time (do you have an open serial connection to it?).", file=sys.stderr)
                print("Wait up to 20 seconds, then try again. If that doesn't work, attempt a hard-reset of the device by pressing the reset button on the back of the board. If that doesn't work, then try a reboot.\n", file=sys.stderr)
                if reraise_exceptions:
                    raise e
                sys.exit(1)
            else:
                print("\nAn error occurred while trying to connect to the micro:bit:\n    %s" % (str(e)))
                if reraise_exceptions:
                    raise e
                sys.exit(1)
        #info("Connected to micro:bit, port: %s" % (self.conn.port))
        # perform a soft reset to make sure that we have a clean environment
        self.soft_reset()
        delaysecs(0.1)
        self.flush_input()

    def handle_potential_invalid_data(self, data):
        """
        Routine which looks for the "Traceback" string at the start of every
        line of output, in case an exception was raised by the micro:bit.
        """
        lines = data.replace("\r", "").strip().split("\n")
        if len(lines) <= 0:
            return
        for x in range(len(lines) - 1):
            if lines[x].startswith("Traceback"):
                # look for the exception raised. this is going to be on the very
                # last line.
                name = lines[-1].split(" ")[0][:-1]
                msg = lines[-1][len(name)+2:]
                warning("the micro:bit raised an exception (%s: %s) with the following traceback:\n[TRACEBACK START]\n%s\n[TRACEBACK END]" % (name, msg, "\n".join(lines[x:])))
                raise Exception("[the micro:bit raised the following exception] %s: %s" % (name, msg))

    def guess_port(self):
        """
        Returns the address of the first available connected micro:bit, or None
        if none were found.
        """
        devices = utils.connected_microbits()
        if len(devices) <= 0:
            return None
        return devices[0]

    def write(self, data, lognotes=""):
        """
        Writes a string of data plus a carriage return ("\r") to the serial
        connection, after encoding it.
        """
        debug(" Sending: " + str(data + "\r") + lognotes)
        self.conn.write(str(data + "\r").encode())

    def readlines(self, strip=True, decode=True, look_for_exceptions=True, flush_after_input=True, until_sequence=b">>> "):
        """
        Continuously reads data from the serial connection until a ">>>" is
        encountered.
        """
        debug(" Received (command echo line, ignoring): " + str(self.conn.readline()))
        data = self.conn.read_until(until_sequence)
        if flush_after_input:
            self.flush_input()
        try:
            dataStr = data.decode()
            debug(" Received (decoded): " + str(dataStr))
            if decode:
                if strip:
                    dataStr = dataStr.replace(until_sequence.decode(), "").strip()
                    if look_for_exceptions:
                        self.handle_potential_invalid_data(dataStr)
                return dataStr
            return data
        except UnicodeDecodeError:
            # Random data received, try again to read.
            self.readlines(strip, decode, look_for_exceptions)

    def execute(self, command, strip=True, decode=True, look_for_exceptions=True, timeout=None, flush_after_input=True):
        """
        Executes the specified command, and returns the result. `strip`
        specifies whether to strip the whole of the output, or just the
        carriage return at the very end.
        """
        backup_timeout = self.conn.timeout
        if timeout is not None:
            self.conn.timeout = timeout
        self.flush_input()
        self.write(command)
        data = self.readlines(strip, decode, look_for_exceptions, flush_after_input)
        self.conn.timeout = backup_timeout
        return data

    def soft_reset(self, do_post_reset=True):
        self.write("\x04", lognotes="(ctrl+c)") # ctrl+c (KeyboardInterrupt)
        self.write("")
        self.flush_input()
        self.write("\x03", lognotes="(ctrl+d)") # ctrl+d (EOF; soft reset)
        if do_post_reset:
            self.post_reset()

    def post_reset(self):
        """
        Function executed after a device reset is called.
        """
        self.execute("")
        self.flush_input()

    def flush_input(self):
        """
        Routine to manually flush the serial input buffer.
        """
        n = self.conn.inWaiting()
        while n > 0:
            self.conn.read(n)
            n = self.conn.inWaiting()

def _determine_variable_type(s):
    """ Function that attempts to guess what kind of variable was specified in s, and returns the appropriate representation of it. """
    if s.startswith("'") and s.endswith("'"):
        # string
        return s[1:-1]
    elif s.isdigit():
        # integer
        return int(s)
    else:
        # float?
        # TODO refine
        try:
            return float(s)
        except:
            pass
        raise Exception("*** FIXME: do something here ***")

class _shim_class:
    """ Wrapper for classes. """
    __dict__ = None

    def __init__(self):
        self.__dict__ = {}

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return self.__dict__[attr]
        raise AttributeError("Shim class has no attribute '%s'" % (attr))

    def _set_attr(self, attr, val):
        self.__dict__[attr] = val

class _shim_function:
    _conn = None
    _path = None

    def __init__(self, conn, path):
        self._conn = conn
        self._path = path

    def call(self, *args, **kwargs):
        """ Wrapper for a function call. """
        # assemble the function string
        # TODO replace info with something else (not an array)?
        s = self._path + "("
        arg_count = len(args) + len(kwargs)

        for arg in args:
            arg = repr(arg)
            s = s + arg
            arg_count -= 1
            if arg_count > 0:
                s = s + ","

        for key in kwargs.keys():
            val = kwargs[key]
            val = repr(val)
            s = s + "%s=%s" % (key, val)
            arg_count -= 1
            if arg_count > 0:
                s = s + ","

        s = s + ")"
        return self._conn.execute(s)

class _microbit_wrapper:
    """ Overall micro:bit wrapper. """
    _conn = None
    _cache_path = None
    _module_list = ["microbit"]
    _members = {}

    def __init__(self):
        self._conn = _microbit_connection()
        home = os.getenv("HOME")
        if home is None:
            raise OSError("Error: could not get home environment variable!")
        self._cache_path= home + "/.microperi_cache"
        self._load_ubit_module_cache()

    def _scan_member_of(self, module_to_process, member_to_process):
        """\
        Scan a member of a module (or a member of a member - this routine is recursive).
        NOTES:
         - members with members themselves are encapsulated in the _shim_class class.
        """
        # assemble a string which represents the "path" to the current
        # member/module which we're processing (e.g: "microbit.display")
        my_path = module_to_process
        if member_to_process is not None:
            my_path = my_path + "." + member_to_process

        debug("processing %s" % (my_path))
        members = self._conn.execute("dir(%s)" % (my_path))[2:-2].split("', '")
        me = _shim_class()

        debug("got members: " + str(members))

        for member in members:
            member = member.strip()
            if len(member) <= 0:
                continue
            debug("processing member " + member)
            info = self._conn.execute("repr(%s.%s)" % (my_path, member))[1:-1]

            member_str = my_path + member

            if info.startswith("<") and info.endswith(">"):
                # this member is a class or function
                s = info[1:-1]
                if s == "function" or s == "bound_method":
                    # function
                    debug("  %s is a function" % (member_str))
                    # add a function wrapper class, then point its member
                    # function to the attribute
                    shim_func = _shim_function(self._conn, member_str)
                    me._set_attr("_shim_function_" + member, shim_func)
                    me._set_attr(member, me.__getattr__("_shim_function_" + member).call)
                else:
                    # assume class
                    debug("  %s is a class" % (member_str))
                    new_member = self._scan_member_of(my_path, member)
                    me._set_attr(member, new_member)
            elif (info.startswith('"') and info.endswith('"')) or \
                (info.startswith("'") and info.endswith("'")):
                debug("  %s is a function" % (member_str))
                me._set_attr(member, str(info[1:-1]))
            elif info.isnumeric():
                # assume integer
                debug("  %s is an integer" % (member_str))
                me._set_attr(member, int(info))
            else:
                # huh?
                # TODO raise exception?
                debug("unrecognised member type (member path: %s). value: %s" % (my_path, info))

        return me

    def _scan_modules(self, micropython_commit_hash):
        self._conn.execute("\x04") # ctrl+c
        self._conn.flush_input()

        cache = {"ver": micropython_commit_hash}

        # FIXME: the below string outputs after a short delay. stderr is
        # nonblocking - this delay should be nonexistent (without the
        # sys.stderr.flush() call, it doesn't output at all until the very end
        # of the function).
        print("Please wait while microperi indexes the micro:bit . . . ", end="", file=sys.stderr)
        sys.stderr.flush()

        for module in self._module_list:
            # try to import the module
            try:
                self._conn.execute("import " + module)
            except:
                # error importing module - assume it doesn't exist
                warning("warning: module %s could not be imported. skipping . . ." % (module))
                continue

            self._conn.flush_input()
            debug("processing module " + module + "")
            cache[module] = self._scan_member_of(module, None)

        try:
            f = open(self._cache_path, "wb")
            pickle.dump(cache, f, protocol=4)
            f.close()
        except BaseException as e:
            print("")
            raise e

        self._members = cache

        print("done!", file=sys.stderr)

    def _load_ubit_module_cache(self):
        # get the commit hash for this build
        self._conn.flush_input()
        self._conn.soft_reset(do_post_reset=False)
        lines = "".join(self._conn.readlines())

        index = lines.find("MicroPython v")

        if index < 0:
            raise Exception("Error: could not determine MicroPython build version")

        index += 13
        # locate the commit hash for this build, used to cache the module map
        # TODO: find a more efficient way of doing this
        # expected format: N.N-N-hash
        while lines[index].isnumeric(): # first N
            index += 1
        index += 1 # "."
        while lines[index].isnumeric(): # second N
            index += 1
        index += 1 # "-"
        while lines[index].isnumeric(): # third N
            index += 1
        index += 1 # "-"
        sindex = lines[index:].find(" ")

        if sindex < 0:
            raise Exception("Error: could not determine MicroPython build version")

        micropython_commit_hash = lines[index:index + sindex]

        try:
            debug(" attemting to load cache from file")
            f = open(self._cache_path, "rb")
            cache = pickle.load(f)
            f.close()
            if "ver" in cache:
                cache_ver = cache["ver"]
                print("cache ver: " + cache_ver)
                if cache_ver == micropython_commit_hash:
                    # use this cache
                    self._members = cache
                    return
        except BaseException as e:
            print("err: " + str(e))
            pass

        debug("failed to load cache from file. reverting to scanning")
        # error. scan the micro:bit manually
        self._scan_modules(micropython_commit_hash)

    def __getattr__(self, attr):
        if attr in self._members:
            return self._members[attr]
        raise AttributeError("Shim class has no attribute '%s'" % (attr))

Microbit = _microbit_wrapper
