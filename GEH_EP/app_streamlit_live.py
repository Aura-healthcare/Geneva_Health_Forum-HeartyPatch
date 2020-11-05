import streamlit as st
import pandas as pd
# import re
# import time
# from datetime import timedelta
# import seaborn as sns
# import plotly.express as px
# import numpy as np
from modules.graph_utilities import (generate_graph_data_handler,
                                     graph_generation)
from modules.tcp_script import start_stream


# Initializing time window

st.sidebar.subheader('Parameters')

time_window_slider = st.sidebar.slider(
    label='Seconds to display:',
    min_value=0,
    max_value=10,
    step=1,
    value=5)

data_frequ_slider = st.sidebar.slider(
    label='Data Frequency (Hz):',
    min_value=0,
    max_value=100,
    step=5,
    value=50)

data_freq = data_frequ_slider

# To CLEAN
time_window = round(data_frequ_slider)
st.sidebar.write('time_window:', str(time_window) + ' values')

# Loading graph data handler

df_ecg = pd.DataFrame(columns=['ECG'], data=[0])


@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def load_graph_data_handler(df_ecg=df_ecg, time_window=time_window):
    graph_data_handler = generate_graph_data_handler(df_ecg=df_ecg,
                                                     time_window=time_window)
    return graph_data_handler


# Loading data simulation function


graph_data_handler = load_graph_data_handler(df_ecg=df_ecg,
                                             time_window=time_window)

x, y = graph_data_handler.x_axis, graph_data_handler.y_axis

slider_y_axis = st.sidebar.slider(
    label='y-axis modifier:',
    min_value=-1500,
    max_value=0,
    step=100,
    value=(-1200, -600)
)

# MAIN time_window
st.title(body='ECG Visualization')

chart = st.empty()
graph_generation(chart, x, y, slider_y_axis, data_freq)


st.sidebar.subheader(body='Actions:')

if st.sidebar.button(label='Reinitialize'):

    graph_data_handler.reinitialize()
    x, y = graph_data_handler.x_axis, graph_data_handler.y_axis
    graph_generation(chart, x, y, slider_y_axis, data_freq)

if st.sidebar.button(label='Start stream'):

    stop_value = 0
    if st.sidebar.button(label='Stop stream'):
        stop_value = 1

    while stop_value == 0:

        # ITERATION

        start_stream()
