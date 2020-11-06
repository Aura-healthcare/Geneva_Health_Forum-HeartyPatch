import streamlit as st
import pandas as pd
import socket
# import re
import time
import datetime
# import seaborn as sns
# import plotly.express as px
# import numpy as np
from modules.graph_utilities import (generate_graph_data_handler,
                                     graph_generation)
#from modules.tcp_script import start_stream, connect_hearty_patch
from modules.tcp_script import HeartyPatch_TCP_Parser, connect_hearty_patch, get_heartypatch_data


# Initializing time window

st.sidebar.subheader('Parameters')

time_window_slider = st.sidebar.slider(
    label='Seconds to display:',
    min_value=0,
    max_value=10,
    step=1,
    value=2)

data_frequ_slider = st.sidebar.slider(
    label='Data Frequency (Hz):',
    min_value=0,
    max_value=100,
    step=5,
    value=1)

simulation_step = st.sidebar.slider(
    label='Graph values by seconds:',
    min_value=0,
    max_value=30,
    step=1,
    value=20)


data_freq = 1/data_frequ_slider
# To CLEAN

time_window = round(time_window_slider / data_freq)
st.sidebar.write('time_window:', str(time_window) + ' values')
st.sidebar.write('data_freq:', str(1/data_freq))
st.sidebar.write('Graph actualisation freq :',
                 str(round(simulation_step * 1000 / data_freq, 2)) + ' ms')
# Loading graph data handler

df_ecg = pd.DataFrame(columns=['ECG'], data=[0])


@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def load_graph_data_handler(df_ecg=df_ecg, time_window=time_window):
    graph_data_handler = generate_graph_data_handler(df_ecg=df_ecg,
                                                     time_window=time_window)
    return graph_data_handler


print('time_window*simulation_step : {}'.format(time_window*simulation_step))
# Loading data simulation function


graph_data_handler = load_graph_data_handler(df_ecg=df_ecg,
                                             time_window=time_window*simulation_step)

x, y = graph_data_handler.x_axis, graph_data_handler.y_axis

slider_y_axis = st.sidebar.slider(
    label='y-axis modifier:',
    min_value=-1500,
    max_value=0,
    step=100,
    value = (-1200, -100)
    # value=(-600, -800)
)

# MAIN time_window
st.title(body='ECG Visualization')

chart = st.empty()
graph_generation(chart, x/(simulation_step), y, slider_y_axis, data_freq)


st.sidebar.subheader(body='Actions:')

if st.sidebar.button(label='Reinitialize'):

    graph_data_handler.reinitialize()
    x, y = graph_data_handler.x_axis, graph_data_handler.y_axis
    graph_generation(chart, x/(simulation_step), y, slider_y_axis, data_freq)


# Parameters

max_packets= 10000
max_seconds = data_freq

#max_seconds = 1 # default recording duration is 10min
hp_host = 'heartypatch.local'
df_ecg = pd.DataFrame(columns=['ECG'], data=[0])

hp = HeartyPatch_TCP_Parser()
connexion = connect_hearty_patch()
timer_offset = data_freq
print('Ready for stream !')

if st.sidebar.button(label='Start stream'):

    socket_test = connexion.sock

    stop_value = 0
    if st.sidebar.button(label='Stop stream'):
        stop_value = 1

    timer = datetime.datetime.today() + (
    datetime.timedelta(seconds=timer_offset))

    while stop_value == 0:

        while (timer - (
            datetime.datetime.today())) >= (
            datetime.timedelta(seconds=0)):
            df_stream, stream_count = get_heartypatch_data(max_packets=max_packets, max_seconds=max_seconds, hp_host=hp_host, timer=timer)
            stream_freq = 1 / (stream_count * data_freq)
            print('Sample retrieved : {}'.format(stream_count))
            print('df_stream shape : {}'.format(df_stream.shape))
            #print(format(df_stream))
        x, y = graph_data_handler.update_graph_data_stream(
            df_ecg=df_stream,
            time_window=time_window)
 
        graph_generation(chart, x, y, slider_y_axis, 1)

        timer += datetime.timedelta(seconds=timer_offset)

    # ssocket_test.close()

        # break
