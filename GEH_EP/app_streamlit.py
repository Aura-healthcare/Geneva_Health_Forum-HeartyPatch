import streamlit as st
import pandas as pd
# import re
import time
# from datetime import timedelta
# import seaborn as sns
import plotly.express as px
# import numpy as np
from modules.graph_utilities import generate_graph_data_handler
from modules.data_simulation import data_simulation


# loading simuluation data

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def load_example_ecg_data():
    df_ecg = pd.read_csv('data/Simulation/df_simualation.csv')
    return df_ecg


checkbox_simulation = st.sidebar.checkbox(label='Simulation data', value=True)


df_ecg_simulation = load_example_ecg_data()

if checkbox_simulation is True:
    df_ecg = df_ecg_simulation

else:
    pass
    # Add realtime use


# Initializing time window

st.sidebar.subheader(body='Parameters')

time_window_slider = st.sidebar.slider(
    label='Seconds to display:',
    min_value=0,
    max_value=10,
    step=1,
    value=3)


time_window = time_window_slider * 60

# Loading graph data handler


@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def load_graph_data_handler(df_ecg=df_ecg, time_window=time_window):
    graph_data_handler = generate_graph_data_handler(df_ecg=df_ecg,
                                                     time_window=time_window)
    return graph_data_handler


# Loading data simulation function

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def load_data_simulation(df_ecg=df_ecg, time_window=time_window, step=15):
    simulation = data_simulation(df_ecg=df_ecg,
                                 time_window=time_window,
                                 step=step)
    return simulation


simulation = load_data_simulation(df_ecg, time_window, step=15)


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
    value=(-1500, 0)
)


# MAIN time_window
st.title(body='ECG Visualization')
time_ratio = 60/3207

fig = px.line(x=x*time_ratio,
              y=y,
              title='Live EEG',
              range_y=slider_y_axis,
              color_discrete_sequence=['green'],
              render_mode='svg',
              template='plotly_white',
              height=600,
              labels={'x': 'seconds', 'y': 'ECG value'})

chart = st.plotly_chart(figure_or_data=fig)

st.sidebar.subheader(body='Actions:')

if st.sidebar.button(label='reinitialize'):
    pass

iterations = 50

def update_graph(duration=60):
    tStart = time.time()
    if time.time() - tStart > duration:
        break
    else:


if st.sidebar.button(label='Run !'):

    stop_value = 0
    if st.sidebar.button(label='stop'):
        stop_value = 1

    for i in range(iterations):
        
        chart.empty()
  
        if stop_value == 0:
            simulation()


        x, y = graph_data_handler.update_graph_data(
            df_ecg=simulation.df_simulation_data,
            time_window=time_window)
        fig = px.line(x=x*time_ratio,
                    y=y,
                    title='Live EEG',
                    range_y=slider_y_axis,
                    color_discrete_sequence=['green'],
                    render_mode='svg',
                    template='plotly_white',
                    height=600,
                    labels={'x': 'seconds', 'y': 'ECG value'})
        chart.plotly_chart(figure_or_data=fig)

        time.sleep(time_ratio*simulation.step)
