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
# from pprint import pprint
# import os
import sys
import signal as sys_signal
import struct

import numpy as np
import pandas as pd
# import matplotlib.pyplot as plt
import scipy.signal as signal
import time
import datetime
from graph_utilities import generate_graph_data_handler
from sockets_utilities import tcp_client_streamlit


max_packets = 10000
max_seconds = 5  # default recording duration is 10min
# hp_host = 'heartypatch.local'
hp_port = 4567

df_ecg = pd.DataFrame(columns=['ECG'], data=[0])
time_window = 5
graph_data_handler = generate_graph_data_handler(df_ecg=df_ecg,
                                                 time_window=time_window)


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

    ces_pkt_seq_bytes = 4  # Buffer for Sequence ID
    ces_pkt_ts_bytes = 8  # Buffer for Timestamp
    ces_pkt_rtor_bytes = 4  # R-R Interval Buffer
    ces_pkt_ecg_bytes = 4  # Field(s) to hold ECG data

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
        self.df = pd.DataFrame(columns=['ECG'])
        self.df_ecg = pd.DataFrame(columns=['ECG'], data=[0])
        self.time_window = 5

        self.df['duration'] = 0
        # Remove?
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

                pkt_len = (256 * (self.data[self.CES_CMDIF_IND_LEN_MSB])) + (
                    self.data[self.CES_CMDIF_IND_LEN])

                # Make sure we have a full packet
                if len(self.data) < (self.CES_CMDIF_PKT_OVERHEAD +
                                     pkt_len + 2):
                    print('break')
                    break

                if (self.data[self.CES_CMDIF_IND_PKTTYPE] != self.Expected_Type
                    or self.data[self.CES_CMDIF_PKT_OVERHEAD+pkt_len+1] != self.CES_CMDIF_PKT_STOP):

                    print('unexpected_type')
#                    if True:
#                          print('pkt_len', pkt_len)
#                          print(self.data[self.CES_CMDIF_IND_PKTTYPE], self.Expected_Type)
#                          print(self.data[self.CES_CMDIF_IND_PKTTYPE] != self.Expected_Type)
#
#                          for j in range(0, self.CES_CMDIF_PKT_OVERHEAD):
#                              print format(ord(self.data[j]),'02x'),
#                          print
#
#                            for j in range(self.CES_CMDIF_PKT_OVERHEAD, self.CES_CMDIF_PKT_OVERHEAD+pkt_len):
#                                print format(ord(self.data[j]),'02x'),
#                            print
#
#                            for j in range(self.CES_CMDIF_PKT_OVERHEAD+pkt_len, self.CES_CMDIF_PKT_OVERHEAD+pkt_len+2):
#                                print format(ord(self.data[j]),'02x'),
#                            print
#                            print self.CES_CMDIF_PKT_STOP,
#                            print ord(self.data[self.CES_CMDIF_PKT_OVERHEAD+pkt_len+2]) != self.CES_CMDIF_PKT_STOP
#                            print
#                        pass

                # Unexpected packet format
                    self.state = self.CESState_Init
                    self.data = self.data[1:]    # start from beginning
                    self.bytes_skipped += 1
                    self.bad_packet_count += 1
                    continue

                # Parse Payload
                payload = self.data[self.CES_CMDIF_PKT_OVERHEAD:
                                    self.CES_CMDIF_PKT_OVERHEAD+pkt_len+1]

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

                # to modify
                retrieved_data = 1

                # Process Sequence ID
                while ptr < pkt_len:
                    ecg = struct.unpack('<i', payload[ptr:ptr+4])[0] / 1000.0
                    self.all_ecg.append(ecg)
                    retrieved_data += 1
                    # Sort outside of loop for better efficency
                    # self.df = self.df.append({'ECG': ecg)}, ignore_index=True)
                    # graph_data_handler.update_graph_data(self.df,
                    # self.time_window)
                    ptr += self.ces_pkt_ecg_bytes

                self.packet_count += 1
                self.state = self.CESState_Init
                # start from beginning
                self.data = self.data[self.CES_CMDIF_PKT_OVERHEAD+pkt_len+2:]


hp = HeartyPatch_TCP_Parser()
timer = None


class connect_hearty_patch:

    def __init__(self, hp_host='heartypatch.local', hp_port=4567):

        print('attempting connexion')

        self.hp_host = hp_host
        self.hp_port = hp_port

        # Try connecting, if not close the conection and restart

        try:
            self.sock = socket.create_connection((self.hp_host, self.hp_port))
            print('Socket created\n')
        except Exception:
            print('Second attempt of connexion...\n')
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = socket.create_connection((self.hp_host, self.hp_port))
            print('Socket created after attempt\n')

        def close_socket(self):
            self.sock.close()


connexion = connect_hearty_patch()
socket_test = connexion.sock
#streamlit_connexion = tcp_server_streamlit()


def get_heartypatch_data(
        max_packets=10000,
        hp_host='heartypatch.local',
        max_seconds=5,
        timer = datetime.datetime.today() + (
        datetime.timedelta(seconds=max_seconds))):

    global soc
    global hp

    tcp_reads = 0
    # hp = HeartyPatch_TCP_Parser()

# Try connecting, if not close the conection and restart

#    try:
#        soc = socket.create_connection((hp_host, hp_port))
#    except Exception:
#        try:
#            soc.close()
#        except Exception:
#            pass
#        soc = socket.create_connection((hp_host, hp_port))
#    print('point A')
    soc = socket_test
#    print(soc)

    sys.stdout.write('Connexion successful \n')
    sys.stdout.flush()

    i = 0
    pkt_last = 0
    txt = soc.recv(16*1024)  # discard any initial results

#    timer = datetime.datetime.today() + (
#        datetime.timedelta(seconds=max_seconds))
    
    retrieved_data_before = len(hp.all_ecg)

    while (timer - (datetime.datetime.today())) >= (
            datetime.timedelta(seconds=0)) and (
            max_packets == -1 or hp.packet_count < max_packets):

    # while  timer - datetime.datetime.today()  >=0 and (max_packets == -1 or hp.packet_count < max_packets):
        txt = soc.recv(16*1024)
        hp.add_data(txt)
        hp.process_packets()
        tcp_client_st.send_to_st_client(data_to_send=str(hp.all_ts[-1:]))


        # Insert here Data Link with streamlit
        i += 1

    # useful?

        tcp_reads += 1
        if tcp_reads % 50 == 0:
            sys.stdout.write(".")
            sys.stdout.flush()

        if hp.packet_count - pkt_last >= 1000:
            pkt_last = pkt_last + 1000
            sys.stdout.write(str(hp.packet_count//1000))
            sys.stdout.flush()

    retrieved_data_length = len(hp.all_ecg)  - retrieved_data_before
    data = hp.all_ecg[-retrieved_data_length:] 

    try:
        start_time_index = hp.df['duration'].iloc[-1]
    except:
        start_time_index = 0

    duration = start_time_index +  np.arange(0, len(data) , 1)/len(data)
   
    temp_df = pd.DataFrame({'ECG': data,
                            'duration': duration
                            })
    hp.df = pd.concat([hp.df, temp_df], ignore_index=True)


def finish():
    # global soc
    # global hp
    # global timer
    # global fname


    tcp_client_st.send_to_st_client(data_to_send=b'close')

    if soc is not None:
        soc.close()

    if tcp_client_st is not None:
        tcp_client_st.close()

    ptr = fname.rfind('.')
    fname_ecg = fname[:ptr] + '_ecg' + fname[ptr:]

    np.savetxt(fname_ecg, hp.all_ecg, header='ECG')

    text_file = open("output.txt", "w")
    n = text_file.write(str(hp.data))
    text_file.close()

    hp.df.to_csv('df.csv', index=False)

def signal_handler(signal, frame):
    global soc
    print('Interrupted by Ctrl+C!')
#    finish()
    sys.exit(0)


if __name__== "__main__":

    max_packets = 10000
    max_seconds = 5  # default recording duration is 10min
    fname = 'log.csv'
    hp_host = 'heartypatch.local'
    #hp_host = '192.168.137.148'

    df_ecg = pd.DataFrame(columns=['ECG'], data=[0])
    time_window = 5

    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '-f' and i < len(sys.argv)-1:
            fname = sys.argv[i+1]
            i += 2
        elif sys.argv[i] == '-s' and i < len(sys.argv)-1:
            max_packets = int(sys.argv[i+1])
            max_seconds = -1
            i += 2
        elif sys.argv[i] == '-m' and i < len(sys.argv)-1:
            max_seconds = int(sys.argv[i+1])*60
            max_packets = -1
            i += 2
        elif sys.argv[i] == '-i' and i < len(sys.argv)-1:
            try:
                foo = int(sys.argv[i+1])
                hp_host = '192.168.43.'+sys.argv[i+1]
            except Exception:
                hp_host = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] in '-p':
            show_plot = True
            i += 1
        elif sys.argv[i] in ['-h', '--help']:
            help()
        else:
            print('Unknown argument' + str(sys.argv[i]))
            help()


    hp = HeartyPatch_TCP_Parser()
    tcp_client_st = tcp_client_streamlit()

    sys_signal.signal(sys_signal.SIGINT, signal_handler)
    get_heartypatch_data(max_packets=max_packets,
                        max_seconds=max_seconds,
                        hp_host=hp_host)
    finish()

    print('Properly Run!')
