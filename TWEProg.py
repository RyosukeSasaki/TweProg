# coding:utf-8

# Copyright (C) 2017 Mono Wireless Inc. All Rights Reserved.
# Released under MW-SLA-*J,*E (MONO WIRELESS SOFTWARE LICENSE
# AGREEMENT)

from TWEEnum import TWEModel, TWEDict
from TWEProg_Firm import TWEProg_Firm
from flashutils import JennicProtocol

class TWEProg_Common():
    def __init__(self):
        pass

    def raise_an_error(self, msg=""):
        raise Exception(msg.encode("utf-8"))

class TWEProg(TWEProg_Common):
    def __init__(self, bl):
        if None is not None: self.bl = JennicProtocol()
        self.bl = bl
        self.rd = {}

    def open(self, comport, baud):
        pass

    def close(self):
        pass

    def identify_model(self):
        cid = self.bl.chipid & 0x0000FFFF
        e = None

        try:
            e = TWEModel(cid)
        except KeyError:
            e = TWEModel.UNKNOWN
        return e

    def get_info(self):
        self.rd = {}
        self.rd[TWEDict.flash_manufacturer] = self.bl.flash_manufacturer
        self.rd[TWEDict.flash_type] = self.bl.flash_type

        self.bl.read_chipid()
        self.rd[TWEDict.chip_id] = self.bl.chipid
        self.rd[TWEDict.model] = self.identify_model()

        self.rd[TWEDict.mac_custom] = list(self.bl.read_mac())

        return self.rd

    def firm_prog(self, firmfile, verify=False):
        fp = TWEProg_Firm(self.bl)
        fp.open_file(firmfile)

        fp.write(verify=verify)

    """ bootloader コマンドによるリセット """
    def reset_twe(self):
        self.bl.soft_reset()

