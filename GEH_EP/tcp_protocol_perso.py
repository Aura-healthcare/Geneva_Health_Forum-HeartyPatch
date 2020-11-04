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

    # Packet Validation
    CESState_Init = 0
    CESState_SOF1_Found = 1
    CESState_SOF2_Found = 2
    CESState_PktLen_Found = 3

    # CES CMD IF Packet Format
    CES_CMDIF_PKT_START_1 = 0x0A
    CES_CMDIF_PKT_START_2 = 0xFA
    CES_CMDIF_PKT_STOP = 0x0B

    # CES CMD IF Packet Indices
    CES_CMDIF_IND_LEN = 2
    CES_CMDIF_IND_LEN_MSB = 3
    CES_CMDIF_IND_PKTTYPE = 4
    CES_CMDIF_PKT_OVERHEAD = 5
    CES_CMDIF_PKT_DATA = CES_CMDIF_PKT_OVERHEAD


    ces_pkt_seq_bytes   = 4  # Buffer for Sequence ID
    ces_pkt_ts_bytes   = 8  # Buffer for Timestamp
    ces_pkt_rtor_bytes = 4  # R-R Interval Buffer
    ces_pkt_ecg_bytes  = 4  # Field(s) to hold ECG data

    # Used to be 3
    Expected_Type = 3

    min_packet_size = 19

    def __init__(self):
        self.state = self.CESState_Init
        self.data = bytes()
        self.packet_count = 0
        self.bad_packet_count = 0
        self.bytes_skipped = 0
        self.total_bytes = 0
        self.all_seq = []
        self.all_ts = []
        self.all_rtor = []
        self.all_hr = []
        self.all_ecg = []
        self.df = pd.DataFrame(columns =['EEG'])
        pass

    def add_data(self, new_data):
        self.data += new_data
        self.total_bytes += len(new_data)

    def process_packets(self):
        while len(self.data) >= self.min_packet_size:
            if self.state == self.CESState_Init:
                if self.data[0] == self.CES_CMDIF_PKT_START_1:
                    self.state = self.CESState_SOF1_Found
                else:
                    self.data = self.data[1:]    # skip to next byte
                    self.bytes_skipped += 1
                    continue
            elif self.state == self.CESState_SOF1_Found:
                if self.data[1] == self.CES_CMDIF_PKT_START_2:
                    self.state = self.CESState_SOF2_Found
                else:
                    self.state = self.CESState_Init
                    self.data = self.data[1:]    # start from beginning
                    self.bytes_skipped += 1
                    continue
            elif self.state == self.CESState_SOF2_Found:
                # sanity check header for expected values
                
                #pkt_len = (256 * (self.data[self.CES_CMDIF_IND_LEN_MSB])) + self.data[self.CES_CMDIF_IND_LEN]
                pkt_len = (256 * (self.data[self.CES_CMDIF_IND_LEN_MSB])) + self.data[self.CES_CMDIF_IND_LEN]
                # Make sure we have a full packet
                if len(self.data) < (self.CES_CMDIF_PKT_OVERHEAD + pkt_len + 2):
                    print('break')
                    break

                if (self.data[self.CES_CMDIF_IND_PKTTYPE]  != self.Expected_Type
                    or self.data[self.CES_CMDIF_PKT_OVERHEAD+pkt_len+1] != self.CES_CMDIF_PKT_STOP):
                    
                    print('unexpected_type')
                    if True:
                    #      print('pkt_len', pkt_len)
                    #      print(self.data[self.CES_CMDIF_IND_PKTTYPE], self.Expected_Type)
                    #      print(self.data[self.CES_CMDIF_IND_PKTTYPE] != self.Expected_Type)
                    #
                    #      for j in range(0, self.CES_CMDIF_PKT_OVERHEAD):
                    #          print format(ord(self.data[j]),'02x'),
                    #      print

    #                        for j in range(self.CES_CMDIF_PKT_OVERHEAD, self.CES_CMDIF_PKT_OVERHEAD+pkt_len):
    #                            print format(ord(self.data[j]),'02x'),
    #                        print
    #
    #                        for j in range(self.CES_CMDIF_PKT_OVERHEAD+pkt_len, self.CES_CMDIF_PKT_OVERHEAD+pkt_len+2):
    #                            print format(ord(self.data[j]),'02x'),
    #                        print
    #                        print self.CES_CMDIF_PKT_STOP,
    #                        print ord(self.data[self.CES_CMDIF_PKT_OVERHEAD+pkt_len+2]) != self.CES_CMDIF_PKT_STOP
    #                        print
                        pass

                # unexpected packet format
                    self.state = self.CESState_Init
                    self.data = self.data[1:]    # start from beginning
                    self.bytes_skipped += 1
                    self.bad_packet_count += 1
                    continue
                        # Parse Payload
                payload = self.data[self.CES_CMDIF_PKT_OVERHEAD:self.CES_CMDIF_PKT_OVERHEAD+pkt_len+1]

                ptr = 0
                # Process Sequence ID
                seq_id = struct.unpack('<I', payload[ptr:ptr+4])[0]
                self.all_seq.append(seq_id)
                ptr += self.ces_pkt_seq_bytes

                # Process Timestamp
                ts_s = struct.unpack('<I', payload[ptr:ptr+4])[0]
                ts_us = struct.unpack('<I', payload[ptr+4:ptr+8])[0]
                timestamp = ts_s + ts_us/1000000.0
                self.all_ts.append(timestamp)
                ptr += self.ces_pkt_ts_bytes

                # Process R-R Interval
                rtor = struct.unpack('<I', payload[ptr:ptr+4])[0]
                self.all_rtor.append(rtor)
                if rtor == 0:
                    self.all_hr.append(0)
                else:
                    self.all_hr.append(60000.0/rtor)

                ptr += self.ces_pkt_rtor_bytes


                assert ptr == 16
                assert pkt_len == (16 + 8 * 4)
                # Process Sequence ID
                while ptr < pkt_len:
                    ecg = struct.unpack('<i', payload[ptr:ptr+4])[0] / 1000.0
                    self.all_ecg.append(ecg)
                    self.df = self.df.append({'EEG':ecg}, ignore_index=True)
                    sys.stdout.write(ecg)
                    sys.stdout.flush()
                    ptr += self.ces_pkt_ecg_bytes

                self.packet_count += 1                    
                self.state = self.CESState_Init
                self.data = self.data[self.CES_CMDIF_PKT_OVERHEAD+pkt_len+2:]    # start from beginning
                
                
            

soc = None
hp = None
tStart = None

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
       hp.process_packets()
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



    ptr = fname.rfind('.')
    fname_ecg =  fname[:ptr] + '_ecg' + fname[ptr:]

    np.savetxt(fname_ecg, hp.all_ecg, header='ECG')

    text_file = open("output.txt", "w")
    n = text_file.write(str(hp.data))
    text_file.close()

    hp.df.to_csv('df.csv')


if __name__== "__main__":
    max_packets= 10000
    max_seconds = 25 # default recording duration is 10min
    hp_host = 'heartypatch.local'

    get_heartypatch_data(max_packets=max_packets, max_seconds=max_seconds, hp_host=hp_host)
    finish()
    print('Properly Run!')