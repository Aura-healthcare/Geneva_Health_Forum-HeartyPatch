import streamlit as st
import pandas as pd
import numpy as np
from modules.graph_utilities import (generate_graph_data_handler,
                                     fig_generation)
from modules.sockets_utilities import tcp_server_streamlit
from modules.RR_detection import compute_heart_rate
from threading import Thread
import time


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
    max_value=15,
    step=1,
    value=2)

y_axis = st.sidebar.slider(
    label='y-axis modifier:',
    min_value=-1500,
    max_value=0,
    step=100,
    value=(-1200, -600))

data_freq = 1/data_freq  # Slider is clearer with the period


class data_delay(Thread):

    def __init__(self, data_freq: int = data_freq):
        Thread.__init__(self)
        self.graph_data = pd.DataFrame()
        self.data_freq = data_freq

    def run(self):
        # To DO : make it real time and delete?

        while stop_value == 0:
            try:
                self.graph_data = thr_tcp_server_st.df
                time.sleep(self.data_freq)
            except Exception:
                time.sleep(self.data_freq)


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

gqrs_value = 0
xqrs_value = 0
swt_value = 0
last_values = 20

gqrs_value_list = []
xqrs_value_list = []
swt_value_list = []

st_gqrs = st.empty()
st_xqrs = st.empty()
st_swt = st.empty()
st_gqrs_avg = st.empty()
st_xqrs_avg = st.empty()
st_swt_avg = st.empty()

st_gqrs.write('**GQRS : {} **'.format(gqrs_value))
st_xqrs.write('**XWRS : {} **'.format(xqrs_value))
st_swt.write('**SWT  : {} **'.format(swt_value))
st_gqrs_avg.write('**AVG GQRS : {} **'.format(swt_value))
st_xqrs_avg.write('**AVG XQRS : {} **'.format(swt_value))
st_swt_avg.write('**AVG SWG  : {} **'.format(swt_value))


x, y = graph_data_handler.x_axis, graph_data_handler.y_axis
chart = fig_generation(x, y, y_axis, data_freq)
chart_dispay = st.plotly_chart(figure_or_data=chart)

# to do: improve warning
st.status = st.sidebar.markdown(
    body='<span style="color: green"> Ready for stream! </span>',
    unsafe_allow_html=True)
print('Ready for stream !')


if st.sidebar.button(label='Start'):

    # Initializing threads
    print('Waiting for HP connexion')

    thr_tcp_server_st = tcp_server_streamlit()
    thr_data_delay = data_delay(data_freq=data_freq)
    compute_hr = compute_heart_rate()

    thr_tcp_server_st.start()
    thr_data_delay.start()
    print('Starting stream\n')

    if st.sidebar.button(label='Stop'):
        stop_value = 1
        try:
            thr_tcp_server_st.st_connexion.close()
            print('Connexion closed by stop')
        except Exception:
            pass

    while stop_value == 0:

        chart.data[0]['x'], chart.data[0]['y'] = \
            graph_data_handler.update_graph_data_stream(
                df_ecg=thr_data_delay.graph_data)

        chart_dispay.plotly_chart(figure_or_data=chart)
        compute_hr.compute(df_input=thr_data_delay.graph_data[-128*10:])

        try:

            gqrs_value = np.average(compute_hr.data['gqrs']['hr'][-5:])
            xqrs_value = np.average(compute_hr.data['xqrs']['hr'][-5:])
            swt_value = np.average(compute_hr.data['xqrs']['hr'][-5:])

            if gqrs_value > 0:
                gqrs_value_list.append(gqrs_value)

            if xqrs_value > 0:
                xqrs_value_list.append(xqrs_value)

            if swt_value > 0:
                swt_value_list.append(swt_value)

            st_gqrs.write('**GQRS : {} **'.format(int(round(gqrs_value, 0))))
            st_xqrs.write('**XWRS : {} **'.format(int(round(xqrs_value, 0))))
            st_swt.write('**SWT  : {} **'.format(int(round(swt_value, 0))))
            # last 20 values for average

            st_gqrs_avg.write('**AVG GQRS : {} **'.format(int(round(
                np.average(gqrs_value_list[-last_values:]), 0))))
            st_xqrs_avg.write('**AVG XWRS : {} **'.format(int(round(
                np.average(xqrs_value_list[-last_values:]), 0))))
            st_swt_avg.write('**AVG SWT   : {} **'.format(int(round(
                np.average(swt_value_list[-last_values:]), 0))))

        except Exception:
            pass

        time.sleep(data_freq)
