import streamlit as st
import pandas as pd
import numpy as np
from modules.graph_utilities import (generate_graph_data_handler,
                                     fig_generation)
from modules.sockets_utilities import tcp_server_streamlit
from modules.RR_detection import compute_heart_rate
from threading import Thread
import time


heartypach_frequency = 128

# Initializing time window
stop_value = 0

st.sidebar.header('Parameters')

st.sidebar.subheader('Graph')

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

st.sidebar.subheader('HR calculation')

hr_delay = st.sidebar.slider(
    label='Historic to compute (seconds) :',
    min_value=1,
    max_value=50,
    step=1,
    value=10)

hr_smoothing = st.sidebar.slider(
    label='HR smoothing (n last HR over the period):',
    min_value=1,
    max_value=10,
    step=1,
    value=3)

hr_count_for_average = st.sidebar.slider(
    label='HR average (n last HR):',
    min_value=1,
    max_value=30,
    step=1,
    value=10)

data_freq = 1/data_freq  # Slider is clearer with the period
hr_delay = int(hr_delay)
hr_smoothing = int(hr_smoothing)
hr_count_for_average = int(hr_count_for_average)


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
hamilton_value = 0

gqrs_value_list = []
xqrs_value_list = []
swt_value_list = []
hamilton_value_list = []

st_gqrs = st.empty()
st_xqrs = st.empty()
st_swt = st.empty()
st_hamilton = st.empty()
st_gqrs_avg = st.empty()
st_xqrs_avg = st.empty()
st_swt_avg = st.empty()
st_hamilton_avg = st.empty()

st_gqrs.write('**GQRS : {} **'.format(gqrs_value))
st_xqrs.write('**XWRS : {} **'.format(xqrs_value))
st_swt.write('**SWT  : {} **'.format(swt_value))
st_hamilton.write('**Hamilton  : {} **'.format(swt_value))
st_gqrs_avg.write('**AVG GQRS : {} **'.format(swt_value))
st_xqrs_avg.write('**AVG XQRS : {} **'.format(swt_value))
st_swt_avg.write('**AVG SWG  : {} **'.format(swt_value))
st_hamilton_avg.write('**AVG Hamilton  : {} **'.format(swt_value))


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
        compute_hr.compute(df_input=thr_data_delay.graph_data[
            -heartypach_frequency*hr_delay:])

        try:

            gqrs_value = np.average(compute_hr.data
                                    ['gqrs']['hr'][-hr_smoothing:])
            xqrs_value = np.average(compute_hr.data
                                    ['xqrs']['hr'][-hr_smoothing:])
            swt_value = np.average(compute_hr.data
                                   ['xqrs']['hr'][-hr_smoothing:])
            hamilton_value = np.average(compute_hr.data
                                        ['hamilton']['hr'][-hr_smoothing:])

            if gqrs_value > 0:
                gqrs_value_list.append(gqrs_value)

            if xqrs_value > 0:
                xqrs_value_list.append(xqrs_value)

            if swt_value > 0:
                swt_value_list.append(swt_value)

            if hamilton_value > 0:
                hamilton_value_list.append(hamilton_value)

            st_gqrs.write('**GQRS : {} **'.format(
                int(round(gqrs_value, 0))))
            st_xqrs.write('**XWRS : {} **'.format(
                int(round(xqrs_value, 0))))
            st_swt.write('**SWT  : {} **'.format(
                int(round(swt_value, 0))))
            st_hamilton.write('**Hamilton  : {} **'.format(
                int(round(hamilton_value, 0))))

            # last 20 values for average

            st_gqrs_avg.write('**AVG GQRS : {} **'.format(int(round(
                np.average(gqrs_value_list[-hr_count_for_average:]), 0))))
            st_xqrs_avg.write('**AVG XWRS : {} **'.format(int(round(
                np.average(xqrs_value_list[-hr_count_for_average:]), 0))))
            st_swt_avg.write('**AVG SWT   : {} **'.format(int(round(
                np.average(swt_value_list[-hr_count_for_average:]), 0))))
            st_hamilton_avg.write('**AVG Hamitlon   : {} **'.format(int(round(
                np.average(hamilton_value_list[-hr_count_for_average:]), 0))))

        except Exception:
            pass

        time.sleep(data_freq)