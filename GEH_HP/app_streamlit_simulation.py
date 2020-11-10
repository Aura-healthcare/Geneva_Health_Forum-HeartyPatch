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
from modules.data_simulation import data_simulation
import datetime

## TO DO
## RENAME time_window to "number of steps"


# loading simuluation data

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def load_example_ecg_data():
    df_ecg = pd.read_csv('data/simulation/df_simulation.csv')
    return df_ecg


checkbox_simulation = st.sidebar.checkbox(label='Simulation data', value=True)


df_ecg_simulation = load_example_ecg_data()

if checkbox_simulation is True:
    df_ecg = df_ecg_simulation
    simulation_step = st.sidebar.slider(
        label='Select batch size for actualisation:',
        min_value=0,
        max_value=30,
        step=1,
        value=10)

    n_data = 3207
    sequence_duraration = 60

else:
    pass
    # Add realtime use

data_freq = n_data/sequence_duraration
st.sidebar.write('Data period :', str(round(1/data_freq*1000, 2)) + ' ms')
st.sidebar.write('Graph actualisation freq :',
                 str(round(simulation_step * 1000 / data_freq, 2)) + ' ms')

# Initializing time window

st.sidebar.subheader('Parameters')

time_window_slider = st.sidebar.slider(
    label='Seconds to display:',
    min_value=0,
    max_value=10,
    step=1,
    value=5)


time_window = round(time_window_slider * data_freq)
timer_offset = simulation_step / data_freq

# st.write('simulation_step', simulation_step)
# st.write('Data period', round(1/data_freq,3))
# st.write('time_window:',time_window)
# st.write('timer_offset:',timer_offset)
#

# Loading graph data handler


@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def load_graph_data_handler(df_ecg=df_ecg, time_window=time_window):
    graph_data_handler = generate_graph_data_handler(df_ecg=df_ecg,
                                                     time_window=time_window)
    return graph_data_handler


# Loading data simulation function

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def load_data_simulation(df_ecg=df_ecg,
                         time_window=time_window,
                         step=simulation_step):
    simulation = data_simulation(df_ecg=df_ecg,
                                 time_window=time_window,
                                 step=step)
    return simulation


simulation = load_data_simulation(df_ecg, time_window, step=simulation_step)


# Initialisation of the data


if checkbox_simulation is True:
    df_ecg = simulation.df_simulation_data

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
graph_generation(chart, x, y, slider_y_axis, 1/data_freq)


st.sidebar.subheader(body='Actions:')

if st.sidebar.button(label='Reinitialize'):

    graph_data_handler.reinitialize()
    simulation.reinitialize()
    x, y = graph_data_handler.x_axis, graph_data_handler.y_axis
    graph_generation(chart, x, y, slider_y_axis, 1/data_freq)

if st.sidebar.button(label='Start'):

    stop_value = 0
    if st.sidebar.button(label='Stop'):
        stop_value = 1

    timer = datetime.datetime.today() + (
        datetime.timedelta(seconds=timer_offset))

    while stop_value == 0:

        simulation()
        x, y = graph_data_handler.update_graph_data(
            df_ecg=simulation.df_simulation_data,
            time_window=time_window)

        while (timer - (
               datetime.datetime.today())) >= (
               datetime.timedelta(seconds=0)):
            pass

        timer += datetime.timedelta(seconds=timer_offset)
        graph_generation(chart, x, y, slider_y_axis, 1/data_freq)
