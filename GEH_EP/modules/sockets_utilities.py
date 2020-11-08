import socket
import sys


def tcp_client_streamlit(host='localhost', port=12800):

    st_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    st_socket.connect((host, port))
    
    sys.stdout.write('Connexion established\n')
    sys.stdout.flush()

    data_to_send = b""

    while True:
        data_to_send = input("> ")
        data_to_send = data_to_send.encode()
        # On envoie le message
        st_socket.send(data_to_send)
        #data_received = connexion_avec_serveur.recv(1024)
        #print(data_received.decode())

    print("Closing socket")
    st_socket.close()


def tcp_server_streamlit(host='localhost', port=12800):

    st_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    st_socket.bind((host, port))
    st_socket.listen(10)

    st_connexion, infos = st_socket.accept()

    sys.stdout.write('Connexion established\n')
    sys.stdout.flush()

    data_received = b""
    while True:
        data_received = st_connexion.recv(1024)
        data_decoded = data_received.decode()
        print(data_decoded)
        try:
            print(data_decoded.split(','))
        except:
            pass

    print("Closing socket")
    st_socket.close()


if __name__ == "__main__":

    if sys.argv[1] == '--server':
        tcp_server_streamlit()
    elif sys.argv[1] == '--client':
        tcp_client_streamlit()
    else:
        print("Valid arguments are '--server' and '--client'")
