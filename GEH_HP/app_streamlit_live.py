import streamlit as st
import pandas as pd
import numpy as np
from modules.graph_utilities import (generate_graph_data_handler,
                                     fig_generation,
                                     generation_hr_graph)
from modules.RR_detection import compute_heart_rate
from modules.hrv_analysis import generate_psd_plot_hamilton
from threading import Thread
import time
from PIL import Image
import datetime
from modules.tcp_script_integrated import HeartyPatch_TCP_Parser


heartypach_frequency = 128


# Initializing time window
stop_value = 0

st.sidebar.header('Parameters')

st.sidebar.subheader('Stream')

minutes_to_stream = st.sidebar.slider(
    label='Minutes to stream:',
    min_value=1,
    max_value=20,
    step=1,
    value=1)

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
    value=5)

y_axis = st.sidebar.slider(
    label='y-axis modifier:',
    min_value=-1500,
    max_value=0,
    step=100,
    value=(-1500, 0))

# hr_delay = st.sidebar.slider(
#     label='Beat detection displayed:',
#     min_value=0,
#     max_value=30,
#     step=1,
#     value=10)
    
st.sidebar.subheader('HR calculation')

hr_delay = st.sidebar.slider(
    label='Historic to compute (seconds) :',
    min_value=1,
    max_value=50,
    step=1,
    value=10)

data_freq = 1/data_freq  # Slider is clearer with the period
hr_delay = int(hr_delay)


class data_delay(Thread):

    def __init__(self, data_freq: int = data_freq):
        Thread.__init__(self)
        self.graph_data = pd.DataFrame()
        self.data_freq = data_freq

    def run(self):
        # To DO : make it real time and delete?

        while stop_value == 0:
            try:
                self.graph_data = hp.df
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

xqrs_value = 0
swt_value = 0
hamilton_value = 0


# st_xqrs = st.empty()
# st_swt = st.empty()
# st_hamilton = st.empty()
# st_xqrs_avg = st.empty()
# st_swt_avg = st.empty()
# st_hamilton_avg = st.empty()

# st_xqrs.write('**XWRS : {} **'.format(xqrs_value))
# st_swt.write('**SWT  : {} **'.format(swt_value))
# st_hamilton.write('**Hamilton  : {} **'.format(swt_value))
# st_xqrs_avg.write('**AVG XQRS : {} **'.format(swt_value))
# st_swt_avg.write('**AVG SWG  : {} **'.format(swt_value))
# st_hamilton_avg.write('**AVG Hamilton  : {} **'.format(swt_value))


st_xqrs_tags = []
st_swt_tags = []
st_hamilton_tags = []

x, y = graph_data_handler.x_axis, graph_data_handler.y_axis

if st.sidebar.button(label='Start'):

    chart = fig_generation(x, y, y_axis, data_freq, hr_delay)
    chart_dispay = st.plotly_chart(figure_or_data=chart)
    chart_hr = st.empty()

    starting_timestamp = datetime.datetime.today()
    # Two minutes of wait for better result
    trigger_timestamp = starting_timestamp + datetime.timedelta(seconds=60*2)

    st.sidebar.markdown(
        body='<span style="color: blue"> XQRS </span>',
        unsafe_allow_html=True)

    st.sidebar.markdown(
        body='<span style="color: red"> SWT </span>',
        unsafe_allow_html=True)

    st.sidebar.markdown(
        body='<span style="color: black"> Hamilton </span>',
        unsafe_allow_html=True)

    # Initializing threads
    print('Waiting for HP connexion')

    hp = HeartyPatch_TCP_Parser(max_seconds=minutes_to_stream*60)
    hp.start()
    df_hr = pd.DataFrame(columns=['timestamp', 'xqrs', 'swt', 'hamilton'])

    time.sleep(3)
    thr_data_delay = data_delay(data_freq=data_freq)
    compute_hr = compute_heart_rate()
    compute_hr_plot = compute_heart_rate()

    thr_data_delay.start()
    print('Starting stream\n')

    while thr_data_delay.is_alive():

        spot_df = thr_data_delay.graph_data

        chart.data[0]['x'], chart.data[0]['y'] = \
            graph_data_handler.update_graph_data_stream(
                df_ecg=spot_df)

        compute_hr.compute(df_input=spot_df[
            -heartypach_frequency*hr_delay:])

        try:
            for name_count in range(3):
                for i in range(hr_delay):
                    chart.layout.shapes[i + name_count*hr_delay].x0 = \
                        chart.data[0]['x'][0]
                    chart.layout.shapes[i + name_count*hr_delay].x1 = \
                        chart.data[0]['x'][0]

            if trigger_timestamp-datetime.datetime.today() < (
                    datetime.timedelta(seconds=0)):

                # Compute on last two minutes
                compute_hr_plot.compute(df_input=hp.df[120*128])
                generate_psd_plot_hamilton(data=compute_hr_plot.data,
                                           sampling_frequency=(
                                               heartypach_frequency))
                image = Image.open('data/records/PSD - lomb.png')
                st.image(image,
                         caption='Duration of recording : {}'.format(
                             str(trigger_timestamp-starting_timestamp)),
                         use_column_width=True)

                trigger_timestamp += datetime.timedelta(seconds=60)
                print('PSD graph generated')

            # Compute HR and generate related graph

            xqrs_value = compute_hr.data['xqrs']['hr'][-1]
            swt_value = compute_hr.data['swt']['hr'][-1]
            hamilton_value = compute_hr.data['hamilton']['hr'][-1]

            df_hr = df_hr.append({'timestamp': spot_df['timestamp'].\
                                 values[-1],
                                  'xqrs': xqrs_value,
                                  'swt': swt_value,
                                  'hamilton': hamilton_value},
                                 ignore_index=True)


            start_frame = chart.data[0]['x'][0]
            end_frame = chart.data[0]['x'][-1]
            chart_hr.plotly_chart(figure_or_data=generation_hr_graph(
                df_hr[df_hr['timestamp'] >= start_frame],
                start_frame=start_frame,
                end_frame=end_frame))


            # Update of ticks of heartbeats

            st_xqrs_tags = np.array(compute_hr.data['xqrs']['qrs'][-hr_delay:])
            st_swt_tags = np.array(compute_hr.data['swt']['qrs'][-hr_delay:])
            st_hamilton_tags = np.array(compute_hr.data['hamilton']['qrs'][-hr_delay:])

            tags_list = [st_xqrs_tags,
                         st_swt_tags,
                         st_hamilton_tags]

            for name_count in range(len(tags_list)):
                for i in range(hr_delay):
                    try:
                        if tags_list[name_count][i] > chart.data[0]['x'][0]:
                            chart.layout.shapes[i + name_count*hr_delay]\
                                .x0 = tags_list[name_count][i]
                            chart.layout.shapes[i + name_count*hr_delay]\
                                .x1 = tags_list[name_count][i]
                    except Exception:
                        print('bad beat marker generation at {}:{}'.format(
                            name_count, i))

        except Exception:
            print('Error')

        chart_dispay.plotly_chart(figure_or_data=chart)
