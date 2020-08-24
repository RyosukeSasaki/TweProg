# coding: UTF-8

# Copyright (C) 2017 Mono Wireless Inc. All Rights Reserved.
# Released under MW-SLA-*J,*E (MONO WIRELESS SOFTWARE LICENSE
# AGREEMENT)

from parseFmt import FmtBase

# バイナリ書式を解読する
class FmtBinary(FmtBase):
    def __init__(self):
        self.reinit()

        # 状態と呼び出すべき関数のテーブル
        self.key_dict = {
            'e' : self.s_empty,
            'h' : self.s_head,
            'L' : self.s_len1,
            'l' : self.s_len2,
            'p' : self.s_payload,
            'x' : self.s_xor
        }

    def reinit(self):
        FmtBase.reinit(self)
        self.xor_read = 0
        self.xor_calc = 0

    def s_empty(self, c):
        if c == 0xA5:
            self.reinit()
            self.state = 'h'
            self.b_complete = False

    def s_head(self, c):
        if c == 0x5A: self.state = 'L'

    def s_len1(self, c):
        self.len = ((c&0x7F)<<8)
        self.state = 'l'

    def s_len2(self, c):
        self.len += c
        self.state = 'p'

    def s_payload(self, c):
        self.len_read = self.len_read + 1
        self.payload.append(c)
        if self.len_read == self.len:
            self.state = 'x'

    def s_xor(self, c):
        self.checksum = self.S_calc_xor(self.payload) 
        if c == self.checksum:
            self.b_complete = True
            self.state = 'e'
        
    @staticmethod
    def S_output(l_payload):
        l = 0x8000 + len(l_payload)
        o = [ 0xa5, 0x5a ]
        o += [ (l & 0xFF00) >> 8, l & 0xff ] 
        o += l_payload
        o += [FmtBinary.S_calc_xor(l_payload)]
        # print(o)
        return bytes(o)
    
    @staticmethod
    def S_calc_xor(lst):
        xor_calc = 0
        for x in lst: 
            xor_calc ^= x
        return xor_calc
        
