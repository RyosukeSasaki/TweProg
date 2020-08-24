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
 
from flashutils import JennicProtocol
from struct import pack
from time import sleep
import time

from pyftdi.ftdi import Ftdi

""" USB バスからシリアル番号を探す """
def find_devno_by_serial(vid, pid, serial):
    import usb.core
    idev = -1

    # find our device
    dev = usb.core.find(idVendor=vid, idProduct=pid, find_all=True)
    if dev is not None:
        for d in dev:
            if d.serial_number == serial:
                idev = d.address
                break

    return idev

class PyFtdiBootloader(JennicProtocol):
    AUTO_PROG_MODE = True
    VENDOR_ID = 0x0403
    PRODICT_ID = 0x6001

    def __init__(self, pid=0x6001, devno=1, flag=None, baud_fast=True, ftdi_obj=None):
        self.DEFAULT_TIMEOUT = 1 # 100 for debug
        self.MAX_TIMEOUT =  3 # 100 fpr debug
        self.MAX_TIMEOUT_ERASEFULL = 8
        self.MAX_TIMEOUT_ERASESECT = 2
        self.BAUD_DEFAULT = 38400
        
        self.b_ftdi_obj = False        
        self.devno = 1
        self.pid = pid
        self.isopen = False
        self.baud_fast = baud_fast

        if ftdi_obj is not None:
            self.ser = ftdi_obj
            self.b_ftdi_obj = True
            self.isopen = True
        else:
            if pid == None: pid = self.PRODICT_ID
            self.devno = None
            if devno.__class__ == int:
                self.devno = devno
            elif devno.__class__ == str:
                pass
                #self.devno = find_devno_by_serial(self.VENDOR_ID, pid, devno)
            else:
                self.devno = 1
    
            self.pid = pid
            self.isopen = False
            self.baud_fast = baud_fast
    
            self.ser = Ftdi()
            self.open(baud=self.BAUD_DEFAULT)

        self.dev_prog()

        self.baud_default_to_fast()

        JennicProtocol.__init__(self)

    def open(self, baud=None):
        if self.b_ftdi_obj:
            if baud is not None:
                self.ser.set_baudrate(baud)
            return self.isopen
        
        if self.ser is not None:
            if self.isopen: self.close()

        if self.ser is None:
            self.ser = Ftdi()

        self.isopen = False
        try:
            self.ser.open(vendor=self.VENDOR_ID, product=self.pid, interface=self.devno)
            self.isopen = True
        except:
            pass

        if baud is None:
            baud = self.self.BAUD_DEFAULT

        self.ser.set_baudrate(baud)

        return self.isopen

    def close(self, destruct=False):
        if self.b_ftdi_obj:
            pass
        else:
            try:
                if self.ser is not None:
                    self.ser.close()
            except:
                pass

            if destruct:
                try:
                    if self.ser is not None:
                        del self.ser
                except:
                    pass
    
                self.ser = None
    
            self.isopen = False

    def baud_set(self, baud, reopen=False):
        if reopen:
            self.close()
            self.open(baud)
        else:
            self.ser.set_baudrate(baud)

    def baud_default(self):
        self.bause_set(self.BAUD_DEFAULT)

    def baud_default_to_fast(self):
        if self.baud_fast:
            self.change_baud(1000000)

    def __del__(self):
        self.close()

    """
        TWE をリセットする
    """
    def dev_reset(self):
        # RESET
        self.ser.set_bitmode(0xFB, 0x20)
        sleep(0.05)
        self.ser.set_bitmode(0xFF, 0x20)

    """
        TWE をプログラムモードに設定する
    """
    def dev_prog(self):
        # FIRMWARE PROGRAM'.',
        self.ser.set_bitmode(0xF3, 0x20)
        sleep(0.05)
        self.ser.set_bitmode(0xF7, 0x20)
        sleep(0.2)
        self.ser.set_bitmode(0xFF, 0x20)
        sleep(0.05)

    """
        シリアルポートに書き出す
        data: byte列を入力
    """
    def write(self, data):
        self.ser.write_data(data)

    """
        シリアルポートから読み出す
        timeout: タイムアウト秒 (float)
        raise_error: タイムアウト時に例外を発生させる
        例外: TypeError タイムアウト
    """
    def read(self, size, timeout=None, raise_error=True):
        d = b''
        ts = time.monotonic()

        if timeout is None: timeout = self.DEFAULT_TIMEOUT

        while True:
            d += self.ser.read_data(size-len(d))
            if len(d) >= size:
                break
            else:
                # timeout check
                if time.monotonic() - ts > timeout:
                    if raise_error: raise TypeError()
                    break
                else:
                    sleep(.01)

        return d

    """
      serial ポートから \n が来るまで読み出す。
      戻り値：str (iso-8859-1)
    """
    def readline(self, timeout=None):
        d = b''
        ts = time.monotonic()
        if timeout is None: timeout = 1

        while True:
            c = self.ser.read_data(1)
            d += c

            if c == b'\n':
                break
            elif c == b'':
                sleep(0.01)

            # timeout check
            if time.monotonic() - ts > timeout:
                break
            else:
                pass

        return d.decode('iso-8859-1')

    """
        JN51XX のシリアルプロトコル
    """
    def talk(self, typ, anstype, addr=None, mlen=None, data=None, max_tim=None):
        length = 3

        if addr != None: length += 4
        if mlen != None: length += 2
        if data != None: length += len(data)

        msg = pack('<BB', length - 1, typ)
        if addr != None: msg += pack('<I', addr)
        if mlen != None: msg += pack('<H', mlen)
        if data != None:
            if data.__class__ == str:
                msg += data.encode()
            else:
                # msg += pack('<%is' % len(data), "".join(map(chr, data)))
                msg += bytes(data)

        msg += pack('<B', self.crc(msg, len(msg)))

        if anstype == None:
            self.write(msg)
            return []

        try:
            #self.ser.timeout = self.DEFAULT_TIMEOUT
            self.write(msg)
            n = self.read(1)
            ans = b''
            if(len(n) == 1): n = n[0]
            else: raise TypeError()
            while len(ans) < n:  # TODO: problematic
                ans += self.read(n)

        except TypeError:  # thrown when self.ser.read() gets nothing
            timeout = self.MAX_TIMEOUT
            if max_tim != None:
                timeout = max_tim

            n = self.read(1, timeout)
            ans = b''
            if(len(n) == 1): n = n[0]
            else: raise TypeError()
            while len(ans) < n:  # TODO: problematic
                ans += self.read(n)

        return ans[1:-1]

