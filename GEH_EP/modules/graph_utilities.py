import numpy as np
import pandas as pd
import plotly.express as px
# from graph_utilities.py import tcp_server_streamlit


class generate_graph_data_handler():

    def __init__(self, df_ecg: pd.DataFrame, time_window: int):

        self.df_graph_data = df_ecg
        self.df_graph_data_stream = df_ecg

        self.time_window = time_window
        self.starting_frame = 0
        self.ending_frame = self.starting_frame + self.time_window
        self.last_second_displayed = 0

        self.x_axis = np.arange(self.starting_frame, self.ending_frame+1)
        self.y_axis = self.df_graph_data['ECG'].\
            loc[self.starting_frame:self.ending_frame]
        # Padding for y_axsis
        temp_list = np.zeros(self.time_window + 1)
        temp_list[:len(self.y_axis)] = self.y_axis
        self.y_axis = temp_list

    def update_graph_data(self, df_ecg: pd.DataFrame, time_window: int) \
            -> [np.array, np.array]:

        self.df_graph_data = df_ecg
        self.time_window = time_window

        # If data displayed in graph reach the right
        if (self.df_graph_data.index[-1:][0] - (
                                                self.starting_frame)) >= (
                                                self.time_window):
            self.starting_frame += self.time_window
            self.ending_frame = self.starting_frame + self.time_window
            self.x_axis = np.arange(self.starting_frame,
                                    self.starting_frame + self.time_window+1)

        # Update of y_axis and padding
        self.y_axis = self.df_graph_data['ECG'].\
            loc[self.starting_frame:self.ending_frame].values
        temp_list = np.zeros(self.time_window + 1)
        temp_list[:len(self.y_axis)] = self.y_axis
        self.y_axis = temp_list

        return self.x_axis, self.y_axis

    def update_graph_data_stream(self, df_ecg: pd.DataFrame) \
            -> [np.array, np.array]:

        self.df_graph_data_stream = df_ecg
        # self.time_window = time_window

        self.last_second_displayed = self.df_graph_data_stream['timestamp']\
            .iloc[-1]
        ending_frame = self.last_second_displayed - (
            self.last_second_displayed % self.time_window) + (
            self.time_window)

        self.y_axis = self.df_graph_data_stream['ECG'][
            (self.df_graph_data_stream['timestamp'] < ending_frame) &
            (self.df_graph_data_stream['timestamp'] >= (
                ending_frame - self.time_window))]

        self.x_axis = self.df_graph_data_stream['timestamp'][
            (self.df_graph_data_stream['timestamp'] < ending_frame) & (
                self.df_graph_data_stream['timestamp'] >=
                (ending_frame - self.time_window))]

        if (ending_frame - (self.last_second_displayed) %
                self.time_window) > 0:
            if (self.last_second_displayed % 1) < 0.50:
                round_last_second_display = int(round(
                    self.last_second_displayed,
                    0)) + 1
            else:
                round_last_second_display = int(round(
                    self.last_second_displayed,
                    0))

            added_duration = np.arange(round_last_second_display,
                                       ending_frame + 1,
                                       1)
            filling_list = np.zeros(len(added_duration))
            filling_list[:] = np.nan
            added_ecg = filling_list + \
                self.df_graph_data_stream['ECG'].iloc[-1]

            self.x_axis = [*self.x_axis, *added_duration]
            self.y_axis = [*self.y_axis, *added_ecg]

        return self.x_axis, self.y_axis

    def reinitialize(self):

        self.starting_frame = 0
        self.ending_frame = self.starting_frame + self.time_window
        self.x_axis = np.arange(self.starting_frame, self.ending_frame+1)
        self.y_axis = np.zeros(self.time_window + 1)


def graph_generation(chart, x, y, slider_y_axis, data_freq):
    fig = px.line(x=x*data_freq,
                  y=y,
                  title='Live EEG',
                  range_y=slider_y_axis,
                  color_discrete_sequence=['green'],
                  render_mode='svg',
                  template='plotly_white',
                  height=600,
                  labels={'x': 'seconds', 'y': 'ECG value'})
    chart.empty()
    chart.plotly_chart(figure_or_data=fig)
