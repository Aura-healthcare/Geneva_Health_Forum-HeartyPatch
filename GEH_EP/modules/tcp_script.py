# coding: utf-8
#
#  HeartyPatch Client
#
# Copyright Douglas Williams, 2018
#
# Licensed under terms of MIT License (http://opensource.org/licenses/MIT).
#

# Adaptation from https://github.com/patchinc/heartypatch/blob/master/
# python/heartypatch_downloader_protocol3.py

import socket
import sys
import signal as sys_signal
import struct
import pandas as pd
import scipy.signal as signal
import datetime
from sockets_utilities import tcp_client_streamlit


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
        self.df = pd.DataFrame(columns=['timestamp', 'ECG'])
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
                        or self.data[self.CES_CMDIF_PKT_OVERHEAD+pkt_len+1]
                        != self.CES_CMDIF_PKT_STOP):

                    print('unexpected_type')

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

                retrieved_data = 1

                # Process Sequence ID
                while ptr < pkt_len:
                    ecg = struct.unpack('<i', payload[ptr:ptr+4])[0] / 1000.0
                    self.all_ecg.append(ecg)
                    retrieved_data += 1
                    self.df = self.df.append({'timestamp': self.all_ts[-1],
                                              'ECG': ecg}, ignore_index=True)
                    ptr += self.ces_pkt_ecg_bytes

                self.packet_count += 1
                self.state = self.CESState_Init
                # start from beginning
                self.data = self.data[self.CES_CMDIF_PKT_OVERHEAD+pkt_len+2:]


class connect_hearty_patch:

    def __init__(self, hp_host='heartypatch.local', hp_port=4567):

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


def get_heartypatch_data(
        max_packets=10000,
        hp_host='heartypatch.local',
        max_seconds=5):

    global tStart

    tcp_reads = 0

    i = 0
    pkt_last = 0

    txt = connexion.sock.recv(16*1024)  # discard any initial results
    tStart = datetime.datetime.today()

    while max_packets == -1 or hp.packet_count < max_packets:

        txt = connexion.sock.recv(16*1024)
        hp.add_data(txt)
        hp.process_packets()

        # what to send to streamlit
        data_to_send = str(hp.all_ts[-1]) + ',' + str(hp.all_ecg[-8:])[1:-1]
        tcp_client_st.send_to_st_client(data_to_send=data_to_send)
        i += 1

        tcp_reads += 1
        if tcp_reads % 50 == 0:
            sys.stdout.write(".")
            sys.stdout.flush()

        if hp.packet_count - pkt_last >= 1000:
            pkt_last = pkt_last + 1000
            sys.stdout.write(str(hp.packet_count//1000))
            sys.stdout.flush()

        if datetime.datetime.today() - tStart > (
           datetime.timedelta(seconds=max_seconds)):
            break


def finish():

    tcp_client_st.send_to_st_client(data_to_send=b'close')

    if connexion.sock is not None:
        connexion.sock.close()

    if tcp_client_st.st_socket_client is not None:
        tcp_client_st.st_socket_client.close()

    hp.df.to_csv('data/results/df - {}.csv'.format(
        tStart.strftime('%Y-%m-%d - %H-%M-%S')),
        index=False)


def signal_handler(signal, frame):

    print('Interrupted by Ctrl+C!')
    finish()
    sys.exit(0)
    print('\nProperly Run!')


if __name__ == "__main__":

    # parameters

    max_packets = -1
    max_seconds = 5
    hp_host = 'heartypatch.local'

    # sys argv

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
            hp_host = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '-p':
            hp_port = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] in ['-h', '--help']:
            help()
        else:
            print('Unknown argument' + str(sys.argv[i]))
            break

    # Class initialisation and start of streaming
    connexion = connect_hearty_patch()
    tcp_client_st = tcp_client_streamlit()
    hp = HeartyPatch_TCP_Parser()

    sys_signal.signal(sys_signal.SIGINT, signal_handler)

    get_heartypatch_data(max_packets=max_packets,
                         max_seconds=max_seconds,
                         hp_host=hp_host)
    finish()
