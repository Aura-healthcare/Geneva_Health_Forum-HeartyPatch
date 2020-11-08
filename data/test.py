import socket
import sys

hp_host = 'heartypatch.local'
hp_port = 4567


try:
    soc = socket.create_connection((hp_host, hp_port))
except Exception:
    try:
        soc.close()
    except Exception:
        pass
    soc = socket.create_connection((hp_host, hp_port))

sys.stdout.write('Connexion successful')
sys.stdout.flush()