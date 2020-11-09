import streamlit as st
import pandas as pd
from modules.graph_utilities import (generate_graph_data_handler,
                                     graph_generation)
from modules.sockets_utilities import tcp_server_streamlit
from threading import Thread
import time
import plotly.express as px


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

if st.sidebar.button(label='Start'):

    chart = st.empty()
    graph_generation(chart, x, y, slider_y_axis, data_freq)


    class data_display(Thread):

        def __init__(self):
            Thread.__init__(self)
            self.graph_data = pd.DataFrame()

        def run(self):
            i = 0
            while i < 20:
                try:
                    self.graph_data = tcp_server_st.df
                    # print(i, self.graph_data.shape)
                    time.sleep(1)
                except:
                    time.sleep(1)
                i += 1



    print('ok for stream')

    tcp_server_st = tcp_server_streamlit()
    data_disp = data_display()

    # plotting_thr = plotting()
    print('Ready for stream')

    tcp_server_st.start()
    data_disp.start()
    # plotting_thr.start()


    # tcp_server_st.join()
    # data_disp.join()
    # plotting_thr.join()

    iteration = 0
    limit = 500
    while True:
        iteration += 1
        print('iteration: ', iteration)
        x = data_disp.graph_data[-limit:].index.values
        y = data_disp.graph_data[-limit:]['ECG'].values
        graph_generation(chart, x, y, slider_y_axis, 1)
        time.sleep(1)

    print('over')
