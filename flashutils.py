# coding:utf-8

# Copyright (c) 2011
# Telecooperation Office (TecO), Universitaet Karlsruhe (TH), Germany.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
# 3. Neither the name of the Universitaet Karlsruhe (TH) nor the names
#    of its contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Author(s): Philipp Scholl <scholl@teco.edu>

# Copyright (C) 2017 Mono Wireless Inc. All Rights Reserved.
# Released under MW-SLA-*J,*E (MONO WIRELESS SOFTWARE LICENSE
# AGREEMENT)

import sys

class JennicProtocol:

    MAX_TIMEOUT_ERASESECT = 1
    MAX_TIMEOUT_ERASEFULL = 2

    def __init__(self, existing_obj=None):
        if existing_obj is not None:
            return

        self.mac_region = range(0x00000030, 0x00000038)
        self.lic_region = range(0x00000038, 0x00000048)
        self.mac = None
        self.lic = None
        self.chipid = 0x00000000
        self.isverbose = None
        self.preferedblocksize = None
        self.select_flash()


    def select_flash(self):
        self.identify_flash()
        if not self.flash_jennicid in (0x00, 0x01, 0x02, 0x03, 0x08):
            print("unsupported flash type")
            sys.exit(1)
        status = self.talk(0x2C, 0x2D, data=[self.flash_jennicid])[0]
        if not status == 0:
            print("could not select detected flash type was: %d" % status)
            sys.exit(1)

    def identify_flash(self):
        flash = self.talk(0x25, 0x26)
        self.flash_status = flash[0]
        self.flash_manufacturer = flash[1]
        self.flash_type = flash[2]
        # self.flash_status       = 0
        # self.flash_manufacturer = 0x12
        # self.flash_type         = 0x12

        if not self.flash_status == 0:
            print("flash status != 0")
            sys.exit(0)

        if self.flash_manufacturer == 0x10 and self.flash_type == 0x10:
            self.flash_manufacturer = "ST"
            self.flash_type = "M25P10-A"
            self.flash_jennicid = 0x00
        elif self.flash_manufacturer == 0xBF and self.flash_type == 0x49:
            self.flash_manufacturer = "SST"
            self.flash_type = "25VF010A"
            self.flash_jennicid = 0x01
        elif self.flash_manufacturer == 0x1f and (self.flash_type == 0x60\
             or self.flash_type == 0x65):
            self.flash_manufacturer = "Atmel"
            self.flash_type = "25F512"
            self.flash_jennicid = 0x02
        elif self.flash_manufacturer == 0x12 and self.flash_type == 0x12:
            self.flash_manufacturer = "ST"
            self.flash_type = "M25P40"
            self.flash_jennicid = 0x03
        elif self.flash_manufacturer == 0xCC and self.flash_type == 0xEE:
            self.flash_manufacturer = "JN516x"
            self.flash_type = "Internal Flash"
            self.flash_jennicid = 0x08
        else:
            self.flash_manufacturer = "unknown"
            self.flash_type = "unknown"
            self.flash_jennicid = 0xFF

    def crc(self, arr, ln):
        """ calculates the crc
        """
        crc = 0
        for i in range(0, ln):
            crc ^= arr[i]
        return crc

    def set_mac(self, s):
        self.mac = []

        for i in range(0, len(s), 2):
            if s[i:i + 2] != "0x":
                self.mac.append(int(s[i:i + 2], 16))

        if not len(self.mac) == 8:
            print("mac must be 8 byte long")
            sys.exit(1)

    def set_license(self, s):
        self.lic = []

        if self.flash_jennicid == 0x08:
            for i in range(0, len(s), 2):
                if s[i:i + 2] != "0x":
                    self.lic.append(int(s[i:i + 2], 16))

            if not len(self.lic) == 8:
                print("license must be 8 byte long")
                sys.exit(1)
        else:
            for i in range(0, len(s), 2):
                if s[i:i + 2] != "0x":
                    self.lic.append(int(s[i:i + 2], 16))

            if not len(self.lic) == len(self.lic_region):
                print("license must be %i byte long" % len(self.lic_region))
                sys.exit(1)


    def erase_flash(self, sect=None):
        """ read mac and license key prior to erasing
        """
        if self.flash_jennicid == 0x08:
            pass
        else:
            # preserve MAC and Lic information on the flash area.
            if not self.mac:
                self.mac = self.read_mac()
            if not self.lic:
                self.lic = self.read_license()

        # ToCos: Erase specified sector(s) to speed up firmware program
        #   or to keep contents on some sectors.
        #   e.g.
        #     sect==None -> erase sector #0
        #     sect==[0,1,7] -> erase sector #0,1,7
        if sect == None: sect = [0]

        print("erasing sect ", end='')
        for b in sect:
            print("#%d.." % b, end='')
            if not self.talk(0x0D, 0x0E, None, None, [b], max_tim=self.MAX_TIMEOUT_ERASESECT)[0] == 0:
                print("erasing did not work")
                sys.exit(1)
        print('')

    def erase_flash_full(self):
        """ read mac and license key prior to erasing
        """
        if self.flash_jennicid == 0x08:
            pass
        else:
            # preserve MAC and Lic information on the flash area.
            if not self.mac:
                self.mac = self.read_mac()
            if not self.lic:
                self.lic = self.read_license()

        if not self.talk(0x07, 0x08 , max_tim=self.MAX_TIMEOUT_ERASEFULL)[0] == 0:
            print("erasing did not work")
            sys.exit(1)

    def read_chipid(self):
        cid = self.talk(0x32, 0x33)
        self.chipid = cid[4] | (cid[3] << 8) | (cid[2] << 16) | (cid[1] << 24)
        return cid[0]

    def read_mac(self):
        if self.flash_jennicid == 0x08:
            # for JN516x
            return self.read_ram(0x01001570, 8)
        else:
            return self.read_flash(self.mac_region[0], len(self.mac_region))

    def read_custom(self):
        if self.flash_jennicid == 0x08:
            # for JN516x
            return self.read_ram(0x01001578, 8)
        else:
            pass

    def read_mac_factory(self):
        if self.flash_jennicid == 0x08:
            # for JN516x
            return self.read_ram(0x01001580, 8)
        else:
            pass

    def read_license(self):
        if not self.flash_jennicid == 0x08:
            return self.read_flash(self.lic_region[0], len(self.lic_region))

    def write_license(self):
        if not self.flash_jennicid == 0x08:
            self.write_flash(self.lic_region[0], self.lic)

    def write_mac(self):
        if self.flash_jennicid == 0x08:
            pass
        else:
            self.write_flash(self.mac_region[0], self.mac)

    def write_flash(self, addr, lst):
        status = self.talk(0x09, 0x0A, addr, data=lst)

        if status[0] != 0:
            raise Exception("writing failed for addr %i status=%i len=%i" % (addr, status[0], len(status)))

    def read_flash(self, addr, ln):
        """ reads len bytes starting at address addr from flash memory.
        """
        return self.talk(0x0B, 0x0C, addr, ln)[1:]  # strip command status

    def write_ram(self, addr, lst):
        status = self.talk(0x1D, 0x1E, addr, data=lst)

        if status[0] != 0:
            raise Exception("writing RAM failed for addr %i status=%i len=%i" % (addr, status[0], len(status)))

    def read_ram(self, addr, ln):
        """ reads len bytes starting at address addr from ram.
        """
        return self.talk(0x1F, 0x20, addr, ln)[1:]  # strip command status

    def run(self, addr):
        ret = self.talk(0x21, 0x22, addr)
        err = False
        if ret == [] or ret[0] != 0:
            err = True
        if err: raise Exception("Run %08x Error!" % addr)

    def soft_reset(self, baud):
        """ software rest
        """
        from time import sleep

        self.talk(0x2C,0x2D,data=[0x08,0,0,0,0]) # select flash (again)
        self.talk(0x14,0x94) # ack?
        self.talk(0x0D, None, 0x0200104C, data=[0,0,0,2]) # reset command

        raise Exception('may not work...')

    def change_baud(self, baud):
        """ change baud rate request
        """
        from time import sleep

        div = int(1000000/baud + .5)
        if baud == 115200: div = 9

        self.talk(0x27,0x28,data=[div])

        sleep(0.3)

        # need reopen the serial port
        #self.ser.close()
        #self.ser.open()
        self.baud_set(baud)

    """
      serial ポートから \n が来るまで読み出す。
      戻り値：str (iso-8859-1)
    """
    def readline(self, timeout=None):
        import time
        d = b''
        ts = time.monotonic()
        if timeout is None: timeout = 1

        while True:
            c = self.read(1)
            d += c

            if c == b'\n':
                break
            elif c == b'':
                time.sleep(0.01)

            # timeout check
            if time.monotonic() - ts > timeout:
                break
            else:
                pass

        return d.decode('latin1')

    def finish(self):
        pass
