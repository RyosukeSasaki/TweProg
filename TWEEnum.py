# coding:utf-8

# Copyright (C) 2017 Mono Wireless Inc. All Rights Reserved.
# Released under MW-SLA-*J,*E (MONO WIRELESS SOFTWARE LICENSE
# AGREEMENT)

from enum import Enum

class TWEModel(Enum):
    TWELite = 0x8686
    TWELiteRED = 0xB686
    UNKNOWN = 0

TWEModelInfo = { \
    TWEModel.TWELite :   { 'name' : 'JN5164' }, \
    TWEModel.TWELiteRED :{ 'name' : 'JN5169' }, \
    TWEModel.UNKNOWN :   { 'name' :  None    } \
}

class TWEDict(Enum):
    mac_custom = 1 # mac address (list)
    mac_custom_str = 2 # string format of mac addr

    serval = 5 # serial value (int)
    serstr = 6 # serial value in HEX string (str: 0x...)

    update_mac = 9 # if update MAC, set True (bool)

    addrinfo = 100 # info from chip
    model = 101 # TWEModel
    flash_manufacturer = 102
    flash_type = 103
    chip_id = 104

    cmd = 200
    cmd_status = 201
    cmd_errstr = 202

    format_none = 1001
    format_ascii = 1002
    format_binary = 1002
        
    retry = 10001


