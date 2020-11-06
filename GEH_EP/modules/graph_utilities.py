import numpy as np
import pandas as pd
import plotly.express as px


class generate_graph_data_handler():

    def __init__(self, df_ecg: pd.DataFrame, time_window: int):

        self.df_graph_data = df_ecg
        self.df_graph_data_stream = df_ecg
        self.time_window = time_window
        self.starting_frame = 0
        self.ending_frame = self.starting_frame + self.time_window
        self.x_axis = np.arange(self.starting_frame, self.ending_frame+1)

        self.y_axis = self.df_graph_data['ECG'].\
            loc[self.starting_frame:self.ending_frame]
        # Padding for
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

    def update_graph_data_stream(self, df_ecg: pd.DataFrame, stream_count: int) \
            -> [np.array, np.array]:

        self.df_graph_data_stream = df_ecg
        self.stream_count = stream_count

        # Update of y_axis and padding
        # self.y_axis = self.df_graph_data['ECG'].\
        #    loc[self.starting_frame:self.ending_frame].values

        temp_list = np.zeros(self.time_window + 1)
        for i in range(self.time_window + 1):
            temp_list[i] = df_ecg['ECG'].loc[int(round(stream_count / self.time_window, 0))]
        self.df_graph_data_stream = self.df_graph_data_stream.append({'ECG': temp_list}, ignore_index=True)
        
        # If data displayed in graph reach the right
        if (self.df_graph_data_stream.index[-1:][0] - (
                                                self.starting_frame)) >= (
                                                self.time_window):
            self.starting_frame += self.time_window
            self.ending_frame = self.starting_frame + self.time_window
            self.x_axis = np.arange(self.starting_frame,
                                    self.starting_frame + self.time_window+1)

        # Update of y_axis and padding
            print(self.x_axis)
            self.y_axis = self.df_graph_data_stream['ECG'].\
            loc[self.starting_frame:self.ending_frame].values
            #temp_list = np.zeros(self.time_window + 1)
            print(self.y_axis)
            #temp_list[:len(self.y_axis)] = self.y_axis
            #self.y_axis = temp_list

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
