# coding: utf-8
#
#  HeartyPatch Client
#
# Copyright Douglas Williams, 2018
#
# Licensed under terms of MIT License (http://opensource.org/licenses/MIT).
#

# In Python3

import socket
from pprint import pprint
import os
import sys
import signal as sys_signal
import struct

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.signal as signal
import time
from datetime import datetime

hp_host = '192.168.0.106'
hp_port = 4567
fname = 'log.csv'

class HeartyPatch_TCP_Parser:
    def __init__(self):
#        self.state = self.CESState_Init
        self.data = bytes()
        self.packet_count = 0
#        self.bad_packet_count = 0
#        self.bytes_skipped = 0
        self.total_bytes = 0
#        self.all_seq = []
#        self.all_ts = []
#        self.all_rtor = []
#        self.all_hr = []
#        self.all_ecg = []
        pass

    def add_data(self, new_data):
        self.data += new_data
        self.total_bytes += len(new_data)

    def process_packets():
        pass


soc = None
hp = None

def get_heartypatch_data(max_packets=10000, hp_host='192.168.0.106', max_seconds=5):
    global soc
    global hp

    tcp_reads = 0
    hp = HeartyPatch_TCP_Parser()

# Try connecting, if not close the conection and restart

    try:
        soc = socket.create_connection((hp_host, hp_port))
    except Exception:
        try:
            soc.close()
        except Exception:
            pass
        soc = socket.create_connection((hp_host, hp_port))

    sys.stdout.write('connected')
    sys.stdout.flush()

    
    i = 0
    pkt_last = 0
    txt = soc.recv(16*1024)  # discard any initial results

    tStart = time.time()
    while max_packets == -1 or hp.packet_count < max_packets:
        txt = soc.recv(16*1024)
        hp.add_data(txt)
#        hp.process_packets()
        i += 1
    # useful?        

        tcp_reads += 1
        if tcp_reads % 50 == 0:
            sys.stdout.write(".")
            sys.stdout.flush()

        if hp.packet_count - pkt_last >=  1000:
            pkt_last = pkt_last + 1000
            sys.stdout.write(packet_count//1000)
            sys.stdout.flush()
        if time.time() - tStart > max_seconds:
            break


def finish():
    global soc
    global hp
    global tStart
    global fname

    if soc is not None:
        soc.close()

    print('new data')
    text_file = open("output.txt", "w")
    n = text_file.write(str(hp.data))
    text_file.close()

if __name__== "__main__":
    max_packets= 1000
    max_seconds = 5 # default recording duration is 10min
    hp_host = 'heartypatch.local'

    get_heartypatch_data(max_packets=max_packets, max_seconds=max_seconds, hp_host=hp_host)
    finish()
    print('Properly Run!')