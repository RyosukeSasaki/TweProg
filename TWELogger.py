import sys
import datetime

# Copyright (C) 2017 Mono Wireless Inc. All Rights Reserved.
# Released under MW-SLA-*J,*E (MONO WIRELESS SOFTWARE LICENSE
# AGREEMENT)

TWELogger_fd_log = None
TWELogger_fd_err = None

class TWELogger():
    def __init__(self, no_color=False):
        self._color = not no_color

    def open_logfiles(self):
        global TWELogger_fd_log, TWELogger_fd_err
        if TWELogger_fd_log is not None: return True

        fbase = datetime.datetime.now().strftime("log/%Y%m%d")
        #print (fbase+'_main.txt')

        try:
            TWELogger_fd_log = open(fbase+'_main.txt', 'a')
            TWELogger_fd_err = open(fbase+'_dbg.txt', 'a')
            return True
        except:
            pass

        return False

    def print_log(self, msg, lb=True):
        global TWELogger_fd_log

        for f in (sys.stdout, TWELogger_fd_log, TWELogger_fd_err):
            if f is not None:
                print(msg, file=f, end=('','\n')[lb])
                f.flush()

    def print_error(self, msg, lb=True):
        global TWELogger_fd_err

        for f in (sys.stderr, TWELogger_fd_err):
            if f is not None:
                if f == sys.stderr:
                    # 長い行は表示しない
                    _m = None
                    if msg.__class__ is not str:
                        _m = str(msg)
                    else:
                        _m = msg    
                    if len(_m) > 64:
                        _m = _m[0:64]+".."
                    print(_m, file=f, end=('','\n')[lb])
                else:
                    print(msg, file=f, end=('','\n')[lb])
                    
                f.flush()

    def print_debug(self, msg, lb=True):
        self.print_error(msg,lb)

    @staticmethod
    def screen_clear():
        print('\033[2J\033[1;1H', end='', file=sys.stderr)
        sys.stderr.flush()

    def screen_string_red(self):
        if self._color:
            print("\033[31m", end='', file=sys.stderr)
            sys.stderr.flush()

    def screen_string_blue(self):
        if self._color:
            print("\033[36m", end='', file=sys.stderr)
            sys.stderr.flush()

    def screen_string_gray(self):
        if self._color:
            print("\033[37m", end='', file=sys.stderr)
            sys.stderr.flush()

    @staticmethod
    def screen_string_black():
        print("\033[0m", end='', file=sys.stderr)
        sys.stderr.flush()

    def screen_print(self, *args, **kwds):
        print(*args, file=sys.stderr, **kwds)
        sys.stderr.flush()

        