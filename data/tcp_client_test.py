import pandas as pd
import socket

hote = "localhost"
port = 12800

connexion_avec_serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connexion_avec_serveur.connect((hote, port))
print("Connexion établie avec le serveur sur le port {}".format(port))

msg_a_envoyer = b""

class data_simulation:

    def __init__(self, df_ecg: pd.DataFrame, time_window: int, step: int):

        self.df_full_simulation_data = df_ecg
        self.time_window = time_window
        self.step = step

        self.starting_frame = 0
        self.ending_frame = self.starting_frame

        self.df_simulation_data = self.df_full_simulation_data.loc[
            self.starting_frame:self.starting_frame]

    def __call__(self):
        self.ending_frame += self.step
        self.df_simulation_data = self.df_full_simulation_data.loc[
            self.starting_frame:self.ending_frame]

    def reinitialize(self):
        self.starting_frame = 0
        self.ending_frame = self.starting_frame
        self.df_simulation_data = self.df_full_simulation_data.loc[
            self.starting_frame:self.starting_frame+1]


df_ecg = pd.read_csv('data/simulation/df_simulation.csv')
time_window = 1
step = 1

simulation = data_simulation(df_ecg = df_ecg,
                             time_window=time_window,
                             step=step)


simulation()
simulation()
simulation()
simulation()
print(simulation.ending_frame)


msg_a_envoyer = b""
while msg_a_envoyer != b"fin":
    msg_a_envoyer = input("> ")
    if msg_a_envoyer == 'simulation':
        simulation()
        msg_a_envoyer = str(simulation.df_simulation_data.shape[0])
    # Peut planter si vous tapez des caractères spéciaux
    msg_a_envoyer = msg_a_envoyer.encode()
    # On envoie le message
    connexion_avec_serveur.send(msg_a_envoyer)
    msg_recu = connexion_avec_serveur.recv(1024)
    print(msg_recu.decode()) # Là encore, peut planter s'il y a des accents

print("Fermeture de la connexion")
connexion_avec_serveur.close()