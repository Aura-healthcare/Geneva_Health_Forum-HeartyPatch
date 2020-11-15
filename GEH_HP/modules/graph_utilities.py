import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


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
                  title='Real Time EEG Display',
                  range_y=slider_y_axis,
                  color_discrete_sequence=['green'],
                  render_mode='svg',
                  template='plotly_white',
                  height=800,
                  labels={'x': 'Seconds', 'y': 'ECG'})
    chart.empty()
    chart.plotly_chart(figure_or_data=fig)


def fig_generation(x, y, y_axis, data_freq, hr_displayed):

    graph_colors = {'ch_gqrs': 'violet',
                    'ch_xqrs': 'blue',
                    'ch_swt': 'red',
                    'ch_hamitlon': 'black'
                    }

    tick_size = 10
    y_axis_start_hr = y_axis[1] - 100

    graph_y_axis = {'ch_gqrs': [y_axis_start_hr + tick_size * 3,
                                y_axis_start_hr + tick_size * 4],
                    'ch_xqrs': [y_axis_start_hr + tick_size * 2,
                                y_axis_start_hr + tick_size * 3],
                    'ch_swt': [y_axis_start_hr + tick_size * 1,
                               y_axis_start_hr + tick_size * 2],
                    'ch_hamitlon': [y_axis_start_hr,
                                    y_axis_start_hr + tick_size * 1]
                    }

    fig = px.line(x=x,
                  y=y,
                  title='Real time EEG',
                  range_y=y_axis,
                  color_discrete_sequence=['green'],
                  render_mode='svg',
                  template='plotly_white',
                  height=600,
                  labels={'x': 'Seconds', 'y': 'Real Time ECG'})
    for name in ['ch_xqrs', 'ch_swt', 'ch_hamitlon']:
        for i in range(hr_displayed):
            fig.add_shape(type='line',
                          yref="y",
                          xref="x",
                          x0=0,
                          x1=0,
                          y0=graph_y_axis[name][0],
                          y1=graph_y_axis[name][1],
                          line=dict(color=graph_colors[name], width=10),
                          name='{}_{}'.format(name, i))

    return fig


def generation_hr_graph(df_hr, start_frame, end_frame):

    fig = go.Figure()

    fig.add_trace(go.Scatter(x=df_hr['timestamp'],
                             y=df_hr['xqrs'],
                             mode='lines',
                             name='xqrs'))
    fig.add_trace(go.Scatter(x=df_hr['timestamp'],
                             y=df_hr['swt'],
                             mode='lines',
                             name='swt'))
    fig.add_trace(go.Scatter(x=df_hr['timestamp'],
                             y=df_hr['hamilton'],
                             mode='lines',
                             name='hamilton'))
    fig.update_layout(xaxis=dict(range=[int(round(start_frame, 0)),
                                 int(round(end_frame, 0))]),
                      yaxis=dict(range=[40, 140]),
                      template='plotly_white',
                      title='Real Time Heart Rate',
                      xaxis_title='Seconds',
                      yaxis_title='Heart Rate (bpm)')

    return fig


def generation_hf_lf_graph(df_hf_lf, start_frame, end_frame):

    fig = go.Figure()

    fig.add_trace(go.Scatter(x=df_hf_lf['timestamp'],
                             y=df_hf_lf['hf'],
                             mode='lines',
                             name='% HF'))
    fig.add_trace(go.Scatter(x=df_hf_lf['timestamp'],
                             y=df_hf_lf['lf'],
                             mode='lines',
                             name='% LF'))

    fig.update_layout(xaxis=dict(range=[int(round(start_frame, 0)),
                                 int(round(end_frame, 0))]),
                      yaxis=dict(range=[0, 100]),
                      template='plotly_white',
                      title='Real Time HF/LF ratio',
                      xaxis_title='Seconds',
                      yaxis_title='Proportion (%)'
                      )

    return fig
