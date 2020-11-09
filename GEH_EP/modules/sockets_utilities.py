import socket
import sys
from threading import Thread
import pandas as pd


class tcp_client_streamlit:

    def __init__(self, host='localhost', port=12801):

        self.st_socket_client = socket.socket(socket.AF_INET,
                                              socket.SOCK_STREAM)
        self.st_socket_client.connect((host, port))

        sys.stdout.write('Connexion established\n')
        sys.stdout.flush()

    def send_to_st_client(self, data_to_send=''):
        if type(data_to_send) != bytes:
            data_to_send = data_to_send.encode()
        self.st_socket_client.send(data_to_send)


class tcp_server_streamlit(Thread):

    def __init__(self, host='localhost', port=12801):
        Thread.__init__(self)
        self.st_socket_server = socket.socket(socket.AF_INET,
                                              socket.SOCK_STREAM,
                                              )
        self.st_socket_server.bind((host, port))
        self.st_socket_server.listen(5)

        self.st_connexion, st_address = self.st_socket_server.accept()

        sys.stdout.write('Connexion established with {}\n'.format(st_address))
        sys.stdout.flush()

        self.data_received = self.st_connexion.recv(1024)
        self.df = pd.DataFrame(columns=['timestamp', 'ECG'])

    def receive_and_process(self):

        while self.data_received != b'close':

            data_decoded = self.data_received.decode()

            # Processing the data received
            # TO DO : modify timestamp for duration
            try:
                temp_list = list(map(float, data_decoded.split(',')))
                for i in range(1, len(temp_list)):
                    self.df = self.df.append({
                        'timestamp': temp_list[0]+((i-1)/128),
                        'ECG': temp_list[i]},
                                            ignore_index=True)
            except:
                print('bad data received')

            self.data_received = self.st_connexion.recv(1024)

        try:
            self.st_connexion.close()
            sys.stdout.write('Connexion closed\n')
        except:
            sys.stdout.write('Connexion already closed\n')

        sys.stdout.flush()

    def run(self):
        self.receive_and_process()


if __name__ == "__main__":

    if sys.argv[1] == '--server':
        tcp_server_st = tcp_server_streamlit()
        tcp_server_st.receive_and_process()
    elif sys.argv[1] == '--client':
        tcp_client_st = tcp_client_streamlit()
        tcp_client_st.st_socket_client.send(b'test')
    else:
        print("Valid arguments are '--server' and '--client'")
