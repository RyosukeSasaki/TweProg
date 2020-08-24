--- tweterm.py --- TWE用ファームウェアプログラマ＆簡易ターミナル

本プログラムは pyftdi (https://github.com/eblot/pyftdi) ライブラリの
サンプルスクリプト pyterm.py に TWELITE 用のファームウェア書き込みスクリプト
を組み込んだものです。

・TWELITE 用ファームウェアの書き込み　(TWELITE R/MONOSTICK)
・シリアルポートでの動作振る舞いの確認

本ソフトウェアは、OS X のコマンドライン環境に習熟した方を対象とします。また、
動作に必要なパッケージのインストールが必要になります。

[保証・ライセンス]
本パッケージ内で、ライセンス上特別な記述のないものは、モノワイヤレスソフトウェア
使用許諾契約書を適用します。

本ソフトウェアについては、モノワイヤレス株式会社が正式にサポートを行うものではあり
ません。お問い合わせにはご回答できない場合もございます。予めご了承ください。また
不具合などのご報告に対してモノワイヤレス株式会社は、修正や改善をお約束するものでは
ありません。

# Copyright (C) 2017 Mono Wireless Inc. All Rights Reserved.
# Released under MW-SLA-*J,*E (MONO WIRELESS SOFTWARE LICENSE
# AGREEMENT)

[動作環境]
  - Mac OS X (10.11.6 El Capitan にて動作確認)
  - python3.5 以降 (3.5.1 にて動作確認)
  - libusb
  - pyserial
  - pyftdi

[パッケージのインストール]
以下では、新しく全パッケージをインストールする例をご紹介します。

  - Homebrew によるパッケージ管理環境を事前にインストールしておいて下さい。
    /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
  - python3 のインストール
    $ brew install python3
  - libusb のインストール
    $ brew install libusb
  - pyserial のインストール
    $ pip3 install pyserial
  - pyftdi のインストール
    $ pip3 install pyftdi
 
[本ソフトウェアのインストール]
本ディレクトリ（アーカイブ）を適当な場所に展開しておきます。以下のディレクトリ
に展開したものとします。
  /Users/Shared/MWSDK/Tools/tweterm
 
環境変数 PATH に上記ディレクトリを追加しておきます。
  PATH=/Users/Shared/MWSDK/Tools/tweterm:$PATH

[利用方法]
事前に FTDI 関連のドライバをアンロードしておきます。
  $ sudo kextunload -b com.apple.driver.AppleUSBFTDI
  
tweterm.py 始動時に以下のパラメータを与えます。 
  -p ftdi:///?                   : デバイス一覧を表示します。（-p 省略時動作）
  
  -p [デバイス名]                : [デバイス名]を指定します。
  　　　　　 　                    一覧で選択したデバイス名を入力します。
　　　 　            -p ftdi:///1           (他に接続デバイスがない場合)
                   -p ftdi://::MW19ZZUB/1 (FTDIシリアルにてデバイス指定)


  -b [ボーレート]                : [ボーレート]を指定します。
                   -b 115200              (115200bps)

  -F [ファームウェア]            : [ファームウェア]を書き込みます。
                   -F App_Twelite.bin     (ファイル名が App_Twelite.bin)
   
  --no-color                     : 文字のカラー出力を抑制します。
  --no-term                      : ターミナルを開きません（ファームウェアの書き込みのみ実行）
   
[操作方法]
   Ctrl+C                        : コマンド入力モードに入ります。
   
   コマンド入力は、続いて１キーを入力します。１キー入力後はモードが解除されます。
   Ctrl+C                        : ターミナルを終了します。
   Ctrl+R または r               : TWELITE をリセットします。
   Ctrl+I または i               : + + + を入力します。
   
   A                             : アスキー形式の解釈を行います
   B                             : バイナリ形式の解釈を行います（キーボード入力はアスキー形式)
   N                             : 書式の解釈をやめます。
   ※ 書式解釈中は TWELITE からの電文は解釈できた電文のみ表示し、キーボードの
     入力はエコーバックされますが、アスキー形式の電文が完成した時に TWELITE
     に送付されます。

[実行例]
実行例中では、適宜改行を挟んでおります。

         ＜最初にデバイスがリストされるかを確認します＞
$ tweterm.py -p ftdi:///?
Available interfaces:
  ftdi://ftdi:232:MW19ZZUB/1   (MONOSTICK)

Please specify the USB device

         ＜ファームウェアを書き込んでターミナルを起動します。
          書き込まない時は -F {ファイル名} は省略します＞
$ tweterm.py -p ftdi://ftdi:232:MW19ZZUB/1 -b 115200 -F ../App_Uart_Master_RED_L1101_V1-2-15.bin 
*** TWE Wrting firmware ... ../App_Uart_Master_RED_L1101_V1-2-15.bin
MODEL: TWEModel.TWELite
SER: 102eebd

 file info: 0f 03 000b
erasing sect #0..#1..#2..
0%..10%..20%..30%..40%..50%..60%..70%..80%..90%..done - 10.24 kb/s
Entering minicom mode

!INF TWE UART APP V1-02-15, SID=0x8102EEBD, LID=0x78
8102EEBD:0> 

         ＜Ctrl+Cを入力すると制御プロンプトが表示されます＞
*** r:reset i:+++ A:ASCFMT B:BINFMT x:exit>

         ＜続けて i を入力します。インタラクティブモードに入ります
           もちろん通常通り + を３回入力しても同じです＞
*** r:reset i:+++ A:ASCFMT B:BINFMT x:exit>[+ + +]
--- CONFIG/TWE UART APP V1-02-15/SID=0x8102eebd/LID=0x00 -E ---
 a: set Application ID (0x67720103) 
 i: set Device ID (121=0x79) 
... ＜省略＞ 
           
         ＜書式の解釈の例：App_UART をバイナリ形式に設定しておきます
           インタラクティブモードで m B [Enter] S と順にタイプします＞ 
--- CONFIG/TWE UART APP V1-02-15/SID=0x8102eebd/LID=0x00 -E ---
 a: set Application ID (0x67720103) 
 i: set Device ID (121=0x79) 
 c: set Channels (18) 
 x: set RF Conf (3) 
 r: set Role (0x0) 
 l: set Layer (0x1) 
 b: set UART baud (38400) 
 B: set UART option (8N1) 
 m: set UART mode (B)*
 h: set handle name [sadkasldja] 
 C: set crypt mode (0) 
 o: set option bits (0x00000000) 
---
 S: save Configuration
 R: reset to Defaults
 
!INF Write config Success
!INF RESET SYSTEM...

         ＜書式の解釈の例：以下、TWELITEはApp_UARTがバイナリ形式で動作した
           状態を想定します＞
 *** r:reset i:+++ A:ASCFMT B:BINFMT x:exit>
         ＜B (大文字) を入力します＞
[FMT: console ASCII, serial BINARY]
         ＜この状態では入出力は書式形式となります。キーボードの入力はアスキー形式、
           TWELITE からの電文はバイナリ形式として解釈します＞
         
         ＜TWELITE からの電文を受け取る簡易な方法は TWELITE をリセットします。
           Ctrl+C を入力後、r を入力します＞
*** r:reset i:+++ A:ASCFMT B:BINFMT x:exit>[RESET TWE]
[dbf1677201030001020f008102eebd0000]
         ＜[db...] が TWELITE からの電文です＞

         ＜TWELITE に電文を送る場合はアスキー書式で入力します＞
:7800112233AABBCCDDX[dba18001]
         ＜ここでは ペイロードが 0x7800112233AABBCCDD のデータをバイナリ
         　形式で TWELITE に送付しています。TWELITE からの 0xDBA18001
           の応答が戻りました。＞

         ＜Ctrl+C を２回連続で入力すると終了します＞
*** r:reset i:+++ A:ASCFMT B:BINFMT x:exit>[
[EXIT]
Bye.