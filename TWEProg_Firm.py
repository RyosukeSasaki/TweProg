# coding:utf-8

# Copyright (C) 2017 Mono Wireless Inc. All Rights Reserved.
# Released under MW-SLA-*J,*E (MONO WIRELESS SOFTWARE LICENSE
# AGREEMENT)

import sys
# from pyftdi.ftdi import Ftdi
#from time import sleep, time
import time
from os import SEEK_END, SEEK_SET
from flashutils import JennicProtocol
from TWELogger import TWELogger

class TWEProg_Firm(TWELogger):
    def __init__(self, bl):
        self.fd = None
        self.wdata = None
        self.data = None
        self.fhead = None
        self.size = None

        if None is not None: self.bl = JennicProtocol()
        if bl is not None: self.bl = bl

        TWELogger.__init__(self)

    def debug_print(self, s):
        self.print_debug(s, False)

    def debug_println(self, s):
        self.print_debug(s, True)

    def check_model(self):
        self.bl.read_chipid()
        self.debug_println("chipid = %x" % self.bl.chipid)

        if self.fhead is None:
            return None
        elif (    self.flash_size == 0x04
              and self.ram_size == 0x03
              and self.chip_type == 0x0008):  # JN5164
            return 'JN5164'
        else:
            return 'UNKNOWN'

    def open_file(self, filename):
        self.fd = open(filename, 'rb')

        # read bin size
        self.fd.seek(0, SEEK_END)
        self.size = self.fd.tell() - 4

        # the first four bytes are arch in compile.
        self.fd.seek(0, SEEK_SET)
        self.fhead = self.fd .read(4)

        self.flash_size = self.fhead[0]
        self.ram_size = self.fhead[1]
        self.chip_type = self.fhead[2] << 8 | self.fhead[3]

        self.debug_println("FILEINFO: %02x %02x %04x" %
              (self.flash_size, self.ram_size, self.chip_type))

        # set it at start point
        self.fd.seek(4, SEEK_SET)
        self.wdata = self.fd.read(self.size)

        self.fd.close()
        #del self.fd
        self.fd = None

    """ program flash content"""
    def write(self, verify=False):
        # start reading the file, 0x80 seems to be the only blocksize
        # working for the jennic bootloader with certain flashtypes
        block, i, start = 0x80, 0, time.time()
        data = self.wdata[0:block] # self.fd.read(block)
        addr = 0x0000

        # erase flash
        self.bl.erase_flash_full()

        while len(data) != 0:
            self.bl.write_flash(addr, data)

            if verify:
                vrfy = self.bl.read_flash(addr, len(data))

                if data != vrfy:
                    msg = "verify error at %04x" % addr
                    self.debug_println(msg)
                    raise Exception(msg)

            addr += len(data)
            data = self.wdata[addr:addr+block]

            if addr > (self.size / 10.*i):
                self.debug_print("%i%%.." % (i * 10))
                i += 1

        kb, sec = self.size / 1000., (time.time() - start)
        self.debug_println("done - %0.2f kb/s" % (kb / sec))
