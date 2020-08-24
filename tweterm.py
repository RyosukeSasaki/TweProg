#!/usr/bin/env python3

"""Pure python simple serial terminal
"""

# Copyright (c) 2010-2016, Emmanuel Blot <emmanuel.blot@free.fr>
# Copyright (c) 2016, Emmanuel Bouaziz <ebouaziz@free.fr>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the Neotion nor the names of its contributors may
#       be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL NEOTION BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Copyright (C) 2017 Mono Wireless Inc. All Rights Reserved.
# Released under MW-SLA-*J,*E (MONO WIRELESS SOFTWARE LICENSE
# AGREEMENT)

import os
import sys
import time
import threading

from _thread import interrupt_main
from argparse import ArgumentParser
from pyftdi import serialext
from pyftdi.ftdi import Ftdi
from pyftdi.misc import to_bool, to_int
from sys import modules, platform, stdin, stdout, stderr
from term import getkey
from traceback import format_exc
import TWELogger
if platform != 'win32':
    import termios
    
from TWEProg import TWEProg
from TWEEnum import TWEDict
from TWELogger import TWELogger
from parseFmt_Ascii import FmtAscii
from parseFmt_Binary import FmtBinary


class MiniTerm(TWELogger):
    """A mini serial terminal to demonstrate pyserial extensions"""

    def __init__(self, device, baudrate=115200, logfile=None, debug=False, twefirm=None, no_color=False, no_term=False):
        self._termstates = []
        if platform != 'win32' and stdout.isatty():
            self._termstates = [(fd, termios.tcgetattr(fd)) for fd in
                                (stdin.fileno(), stdout.fileno(),
                                 stderr.fileno())]

        self._device = device
        self._baudrate = baudrate
        self._logfile = logfile
        self._port = self._open_port(self._device, self._baudrate,
                                     self._logfile, debug)
        self._resume = False
        self._debug = debug
        self._twefirm = twefirm
        self._twecmd = False
        self._tweformat = TWEDict.format_none
        self._twefmt_console = FmtAscii()
        self._twefmt_serail = None
        self._no_term = no_term
        
        TWELogger.__init__(self, no_color=no_color)

        if twefirm is not '':
            self._port.udev.set_baudrate(38400)
            self.tweprogram(twefirm)

    def __del__(self):
        try:
            self._cleanup()
        except Exception:
            pass

    def tweprogram(self, twefirm):
        from con_pyftdi import PyFtdiBootloader
        
        bl = PyFtdiBootloader(ftdi_obj=self._port.udev, baud_fast=True)
        prog = TWEProg(bl)
        
        self.screen_string_blue()
        self.screen_print("*** TWE Wrting firmware ... %s" % twefirm)   
        minfo = prog.get_info()
        self.screen_print("MODEL: %s" % minfo[TWEDict.model])
        madr = minfo[TWEDict.mac_custom]
        self.screen_print("SER: %x%02x%02x%02x" % (madr[4] & 0xF, madr[5], madr[6], madr[7]))

        if twefirm is not None:
            prog.firm_prog(twefirm, verify=False)
    
        self.screen_string_black()
        
        bl.baud_set(self._baudrate, True)
        bl.dev_reset() 
        
    def run(self, fullmode=False, reset=None, select=None):
        """Switch to a pure serial terminal application"""
        if self._no_term:
            return
        
        if select is not None:
            selmode = to_bool(select)
            self._port.setRTS(selmode)
        if reset is not None:
            hwreset = to_bool(reset)
            self._port.setDTR(hwreset)
            time.sleep(0.200)
            self._port.setDTR(not hwreset)
            time.sleep(0.100)
        # wait forever, although Windows is stupid and does not signal Ctrl+C,
        # so wait use a 1/2-second timeout that gives some time to check for a
        # Ctrl+C break then polls again...
        self.screen_string_blue()
        self.screen_print('Entering minicom mode')
        self.screen_string_black()
        
        stdout.flush()
        self._port.timeout = 0.5
        self._resume = True
        # start the reader (target to host direction) within a dedicated thread
        r = threading.Thread(target=self._reader)
        r.setDaemon(1)
        r.start()
        # start the writer (host to target direction)
        self._writer(fullmode)

    def _reader(self):
        """Loop forever, processing received serial data in terminal mode"""
        try:
            # Try to read as many bytes as possible at once, and use a short
            # timeout to avoid blocking for more data
            self._port.timeout = 0.050
            while self._resume:
                data = self._port.read(4096)
                
                if data:
                    if self._tweformat == TWEDict.format_none:
                        try:
                            stdout.write(data.decode('utf8'))
                        except UnicodeDecodeError:
                            pass
                        stdout.flush()
                    else:
                        if self._twefmt_serail is not None:
                            for x in data:
                                self._twefmt_serail.process(x)
                                if self._twefmt_serail.is_comp():
                                    # data has arrived and correct format
                                    self.screen_string_blue()
                                    self.screen_print("[%s]" % bytes(self._twefmt_serail.get_payload()).hex())
                                    self.screen_string_black()
                                    self._twefmt_serail.reinit()
        except KeyboardInterrupt:
            return
        except Exception as e:
            print("Exception: %s" % e)
            if self._debug:
                print(format_exc())
            interrupt_main()

    def _writer(self, fullmode=False):
        """Loop and copy console->serial until EOF character is found"""
        while self._resume:
            try:
                keybytes = getkey(fullmode)
 
                if keybytes is None:
                    continue
                
                c = keybytes[0]
                
                if platform == 'win32':
                    if c == 0x3:
                        raise KeyboardInterrupt()
                
                if self._twecmd:
                    if (fullmode and c == 0x1) or c == 0x18 or c == ord('x'):  # Ctrl+A, X, 'x' to exit
                        self._cleanup()
                        return
                    elif c == ord('c'): # type Ctrl+C
                        self._port.write(b'\x03')
                    elif c == ord('l') or c == 12:
                        self.screen_clear()
                    elif c == 0x12 or c == ord('r'):  # Ctrl+R
                        # reset TWELITE thru FTDI bitbang
                        self.screen_print("[RESET TWE]")
                        self._port.udev.set_bitmode(0xFB, 0x20)
                        self._port.udev.set_bitmode(0xFF, 0x20)
                    elif c == 0x9 or c == ord('i'): # Ctrl+I
                        # just press '+' three times for interactive mode.
                        self.screen_print("[+ + +]")
                        stdout.flush()
                        self._port.write(b'+')
                        time.sleep(0.5)
                        self._port.write(b'+')
                        time.sleep(0.5)
                        self._port.write(b'+')
                    elif c == ord('A'): # input ASCII format, output ASCII format
                        # ASCII format analysis
                        self.screen_print("[FMT: console ASCII, serial ASCII]")
                        self._twefmt_serail = FmtAscii()
                        self._tweformat = TWEDict.format_ascii
                    elif c == ord('B'): # input ASCII format, outout BINARY format
                        # BINARY format analysis
                        self.screen_print("[FMT: console ASCII, serial BINARY]")
                        self._twefmt_serail = FmtBinary()
                        self._tweformat = TWEDict.format_binary
                    elif c == ord('N'): # format none
                        self.screen_print("[FMT: none]")
                        self._tweformat = TWEDict.format_none
                    else:
                        self.screen_print("[Canceled]")
                        
                    self.screen_string_black() 
                    stdout.flush()
                    self._twecmd = False
                elif self._tweformat != TWEDict.format_none:
                    # console input should be handled as ASCII format
                    self._twefmt_console.process(c)
                    
                    print(chr(c), end='') # echo back
                    stdout.flush()
                    
                    # when format is complete, send it to serial
                    if self._twefmt_console.is_comp():
                        if self._twefmt_serail is not None:
                            self._port.write(self._twefmt_serail.S_output(self._twefmt_console.get_payload()))
                        self._twefmt_console.reinit() # clean it anyway
                else:
                    self._port.write(keybytes)
                    
            except KeyboardInterrupt:
                if self._twecmd:
                    self.screen_print("[Exit]")
                    self.screen_string_black()
                    self._cleanup()
                    return
                else:
                    self._twecmd = True
                    self.screen_string_red()
                    self.screen_print("*** r:reset i:+++ A:ASCFMT B:BINFMT x:exit>", end='')
                    stdout.flush()
                    continue

    def _cleanup(self):
        """Cleanup resource before exiting"""
        self._resume = False
        if self._port:
            # wait till the other thread completes
            time.sleep(0.5)
            try:
                rem = self._port.in_waiting()
            except Exception:
                # maybe a bug in underlying wrapper...
                rem = 0
            # consumes all the received bytes
            for _ in range(rem):
                self._port.read()
            self._port.close()
            self._port = None
            print('Bye.')
        for fd, att in self._termstates:
            termios.tcsetattr(fd, termios.TCSANOW, att)

    @staticmethod
    def _open_port(device, baudrate, logfile=False, debug=False):
        """Open the serial communication port"""
        # the following import enables serial protocol extensions
        try:
            if logfile:
                port = serialext.serial_for_url(device, do_not_open=True)
                basecls = port.__class__
                from pyftdi.serialext.logger import SerialLogger
                cls = type('Spy%s' % basecls.__name__,
                           (SerialLogger, basecls), {})
                port = cls(device, baudrate=baudrate,
                           timeout=0, logfile=logfile)
            else:
                port = serialext.serial_for_url(device,
                                                baudrate=baudrate,
                                                timeout=0,
                                                do_not_open=True)
            port.open()
            if not port.is_open:
                raise IOError('Cannot open port "%s"' % device)
            if debug:
                print("Using serial backend '%s'" % port.BACKEND)
            return port
        except IOError as ex:
            # SerialException derives from IOError
            raise


def main():
    """Main routine"""
    debug = False 
    try:
        argparser = ArgumentParser(description=modules[__name__].__doc__)
        argparser.add_argument('-p', '--device', default='ftdi:///?',
                               help="serial port device name "
                                    "(list available ports with 'ftdi:///?')")
        argparser.add_argument(
            '-b', '--baudrate', dest='baudrate',
            help='serial port baudrate', default='115200')
        argparser.add_argument(
            '-r', '--reset', dest='reset',
            help='HW reset on DTR line', default=None)
        argparser.add_argument(
            '-s', '--select', dest='select',
            help='Mode selection on RTS line', default=None)
        argparser.add_argument(
            '-o', '--logfile', dest='logfile',
            help='path to the log file')
        if os.name in ('posix', ):
            argparser.add_argument(
                '-f', '--fullmode', dest='fullmode', action='store_true',
                help='use full terminal mode, exit with [Ctrl]+A')
        argparser.add_argument(
            '-d', '--debug', dest='debug', action='store_true',
            help='enable debug mode')
        argparser.add_argument(
            '--no-color', dest='no_color', action='store_true', default=False,
            help='disable screen color mode.')
        argparser.add_argument(
            '-F', '--twefirm', dest='twefirm', default='',
            help='write TWE firmware before start.')
        argparser.add_argument(
            '--no-term', dest='no_term', action='store_true', default=False,
            help='write TWE firmware and exit program.')
        args = argparser.parse_args()
        debug = args.debug

        miniterm = MiniTerm(device=args.device,
                            baudrate=to_int(args.baudrate),
                            logfile=args.logfile,
                            debug=args.debug,
                            twefirm=args.twefirm,
                            no_color=args.no_color,
                            no_term=args.no_term)
        miniterm.run(os.name in ('posix', ) and args.fullmode or False,
                     args.reset, args.select)
    except Exception as e:
        TWELogger.screen_string_black()
        print('\nError: %s' % e)
        if debug:
            print(format_exc())
        exit(1)
    except KeyboardInterrupt:
        exit(2)


if __name__ == '__main__':
    main()
