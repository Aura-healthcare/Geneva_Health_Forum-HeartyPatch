import streamlit as st
import pandas as pd
import numpy as np
from modules.graph_utilities import (generate_graph_data_handler,
                                     fig_generation,
                                     generation_hr_graph,
                                     generation_hf_lf_graph)
from modules.RR_detection import compute_heart_rate
from modules.hrv_analysis import generate_psd_plot_hamilton, compute_hf_lf
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
    value=4)

y_axis = st.sidebar.slider(
    label='y-axis modifier:',
    min_value=-1500,
    max_value=0,
    step=100,
    value=(-1500, 0))

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

st_xqrs_tags = []
st_swt_tags = []
st_hamilton_tags = []

hf_value = 0
df_value = 0

x, y = graph_data_handler.x_axis, graph_data_handler.y_axis

if st.sidebar.button(label='Start'):

    starting_timestamp = datetime.datetime.today()
    # Two minutes of wait for better result
    trigger_timestamp = starting_timestamp + datetime.timedelta(seconds=60*2)

    # st.sidebar.subheader(body='Legend')

    # st.sidebar.markdown(
    #     body='<span style="color: blue"> XQRS </span>',
    #     unsafe_allow_html=True)

    # st.sidebar.markdown(
    #     body='<span style="color: red"> SWT </span>',
    #     unsafe_allow_html=True)

    # st.sidebar.markdown(
    #     body='<span style="color: black"> Hamilton </span>',
    #     unsafe_allow_html=True)

    # Initializing threads
    print('Waiting for HP connexion')

    hp = HeartyPatch_TCP_Parser(max_seconds=minutes_to_stream*60)
    hp.start()

    time.sleep(5)  # Delay for beginning of data acqusition and hr computations

    thr_data_delay = data_delay(data_freq=data_freq)
    thr_data_delay.start()

    df_hr = pd.DataFrame(columns=['timestamp', 'xqrs', 'swt', 'hamilton'])
    df_hf_lf = pd.DataFrame(columns=['timestamp', 'hf', 'lf'])

    chart = fig_generation(x, y, y_axis, data_freq, hr_delay)
    chart_dispay = st.plotly_chart(figure_or_data=chart)
    chart_hr = st.empty()
    chart_hf_lf = st.empty()
 
    compute_hr = compute_heart_rate()
    compute_hr_plot = compute_heart_rate()
    print('Starting stream\n')

    while hp.is_alive():

        spot_df = thr_data_delay.graph_data

        chart.data[0]['x'], chart.data[0]['y'] = \
            graph_data_handler.update_graph_data_stream(
                df_ecg=spot_df)

        compute_hr.compute(df_input=spot_df[
            -heartypach_frequency*hr_delay:])

        # Remove heart beats ticks
        for name_count in range(3):
            for i in range(hr_delay):
                chart.layout.shapes[i + name_count*hr_delay].x0 = \
                    chart.data[0]['x'][0]
                chart.layout.shapes[i + name_count*hr_delay].x1 = \
                    chart.data[0]['x'][0]

        # Every minute after two minutes of data acquisition, make psd plot
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
        try:
            xqrs_value = compute_hr.data['xqrs']['hr'][-1]
            swt_value = compute_hr.data['swt']['hr'][-1]
            hamilton_value = compute_hr.data['hamilton']['hr'][-1]

            df_hr = df_hr.append({'timestamp': spot_df['timestamp'].  # \
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

        except Exception:
            print('Cannot compute hr_values')

        # Compute HF_LF and generate related graph
        try:
            hf_value, lf_value = compute_hf_lf(
                                    compute_hr.data,
                                    sampling_frequency=(
                                        heartypach_frequency),
                                    preprocessing=False)

            df_hf_lf = df_hf_lf.append({'timestamp': spot_df['timestamp'].
                                        values[-1],
                                        'hf': hf_value,
                                        'lf': lf_value},
                                        ignore_index=True)

            chart_hf_lf.plotly_chart(figure_or_data=generation_hf_lf_graph(
                df_hf_lf[df_hf_lf['timestamp'] >= start_frame],
                start_frame=start_frame,
                end_frame=end_frame))

        except Exception:
            print('Cannot compute HF/LF')

        # Update of ticks of heartbeats
        try:

            st_xqrs_tags = np.array(compute_hr.data['xqrs']['qrs'][-hr_delay:])
            st_swt_tags = np.array(compute_hr.data['swt']['qrs'][-hr_delay:])
            st_hamilton_tags = np.array(compute_hr.data['hamilton']['qrs'][
                -hr_delay:])

            tags_list = [st_xqrs_tags,
                        st_swt_tags,
                        st_hamilton_tags]

            for name_count in range(len(tags_list)):
                for i in range(len(tags_list[name_count])):
                        if tags_list[name_count][i] > chart.data[0]['x'][0]:
                            chart.layout.shapes[i + name_count*hr_delay]\
                                .x0 = tags_list[name_count][i]
                            chart.layout.shapes[i + name_count*hr_delay]\
                                .x1 = tags_list[name_count][i]
        except Exception:
            print('bad beat marker generation at {}:{}'.format(
                name_count, i))

        chart_dispay.plotly_chart(figure_or_data=chart)
