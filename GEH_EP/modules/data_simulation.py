import pandas as pd


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
