# coding: UTF-8

from parseFmt import FmtBase

class FmtAscii(FmtBase):
    def __init__(self):
        self.reinit()

        # 状態と呼び出すべき関数のテーブル
        self.key_dict = {
            'e' : self.s_empty,
            'p' : self.s_payload1,
            'q' : self.s_payload2,
        }
        
        self._first_byte = 0

    def reinit(self):
        FmtBase.reinit(self)

    def input_hex_chr(self, c):
        if (c >= 0x30 and c <= 0x39):
            c = c - 0x30
        elif (c >= 0x41 and c <= 0x46):
            c = c - 0x41 + 10
        else:
            c = None
        
        return c
        
    def s_empty(self, c):
        if c == ord(':'):
            self.reinit()
            self.state = 'p'
            self.b_complete = False

    def s_payload1(self, c):
        if self.len_read > 0 and (c == 10 or c == 13): # cr or lf
            if sum(self.payload) & 0xff == 0:
                # LRC is okay
                self.b_complete = True
                self.checksum = self.payload.pop() # remove last item
                self.len = len(self.payload) # reset the length
                
            self.state = 'e'
            return
        
        if self.len_read > 0 and c == ord('X'): # skip checksum input
            self.b_complete = True
            self.checksum = self.S_lrc(self.payload)
            self.state = 'e'
            return
        
        self._first_byte = self.input_hex_chr(c)
        # print(self._first_byte)
        
        if self._first_byte is not None:
            self.state = 'q'
        else:
            self.state = 'e'

    def s_payload2(self, c):
        c = self.input_hex_chr(c)
        if c is not None:
            c = c + (self._first_byte << 4)
            
            self.len_read = self.len_read + 1
            self.payload.append(c)
            self.state = 'p'
        else:
            self.state = 'e'

    @staticmethod
    def S_output(lst):
        lrc = FmtAscii.S_lrc(lst)
        o = ':'
        for x in lst:
            o += "%02X" % x
        o += "%02X" % lrc
        o += '\n'
        return o.encode()
        
    @staticmethod
    def S_lrc(lst):
        c = 0
        for x in lst:
            c = 0xFF&( c+x )

        c = 0x0100 - c
        return c
