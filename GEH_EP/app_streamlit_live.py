import streamlit as st
import pandas as pd
from modules.graph_utilities import (generate_graph_data_handler,
                                     graph_generation,
                                     data_delay)
from modules.sockets_utilities import tcp_server_streamlit

# Initializing time window
stop_value = 0

st.sidebar.subheader('Parameters')

time_window = st.sidebar.slider(
    label='Seconds to display:',
    min_value=1,
    max_value=50,
    step=1,
    value=16)

data_freq = st.sidebar.slider(
    label='Graph actualisation frequency (Hz):',
    min_value=1,
    max_value=100,
    step=2,
    value=10)

y_axis = st.sidebar.slider(
    label='y-axis modifier:',
    min_value=-1500,
    max_value=0,
    step=100,
    value=(-1200, -600))

data_freq = 1/data_freq  # Slider is clearer with the period


# Loading graph data handler

df_ecg = pd.DataFrame(columns=['ECG'], data=[0])


@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def load_graph_data_handler(df_ecg=df_ecg, time_window=time_window):
    graph_data_handler = generate_graph_data_handler(df_ecg=df_ecg,
                                                     time_window=time_window)
    return graph_data_handler


graph_data_handler = load_graph_data_handler(df_ecg=df_ecg,
                                             time_window=time_window)


# MAIN WINDOW
st.title(body='ECG Visualization')

chart = st.empty()
x, y = graph_data_handler.x_axis, graph_data_handler.y_axis
graph_generation(chart, x, y, y_axis, 1)

# to do: improve warning
st.status = st.sidebar.markdown(
    body='<span style="color: green"> Ready for stream! </span>',
    unsafe_allow_html=True)
print('Ready for stream !')

if st.sidebar.button(label='Start'):

    # Initializing threads
    print('Waiting for HP connexion...')

    thr_tcp_server_st = tcp_server_streamlit()
    thr_data_disp = data_delay()

    thr_tcp_server_st.start()
    thr_data_disp.start()

    if st.sidebar.button(label='Stop'):
        stop_value = 1
        try:
            thr_tcp_server_st.st_connexion.close()
            print('Connexion closed by stop')
        except:
            pass

    while stop_value == 0:

        print('Starting stream\n')
        while stop_value == 0:
            x, y = graph_data_handler.update_graph_data_stream(
                df_ecg=thr_data_disp.graph_data,
                time_window=time_window)
            graph_generation(chart, x, y, y_axis, 1)
