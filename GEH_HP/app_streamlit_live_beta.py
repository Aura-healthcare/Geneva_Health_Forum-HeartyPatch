import streamlit as st
import pandas as pd
import numpy as np
from modules.graph_utilities import (generate_graph_data_handler,
                                     fig_generation)
from modules.RR_detection import compute_heart_rate
from modules.hrv_analysis import generate_psd_plot_hamilton
from threading import Thread
import time
from PIL import Image
import datetime
from modules.tcp_script_integrated import HeartyPatch_TCP_Parser


heartypach_frequency = 128
hr_displayed = 10

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
    value=1)

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

st_gqrs_tags = []
st_xqrs_tags = []
st_swt_tags = []
st_hamilton_tags = []

x, y = graph_data_handler.x_axis, graph_data_handler.y_axis
chart = fig_generation(x, y, y_axis, data_freq, hr_displayed)
chart_dispay = st.plotly_chart(figure_or_data=chart)

# to do: improve warning
print('Ready for stream !')


if st.sidebar.button(label='Start'):

    starting_timestamp = datetime.datetime.today()
    trigger_timestamp = starting_timestamp + datetime.timedelta(seconds=60)

    st.sidebar.markdown(
        body='<span style="color: green"> Ready for stream! </span>',
        unsafe_allow_html=True)

    st.sidebar.subheader(body='Legend:')

    st.sidebar.markdown(
        body='<span style="color: red"> GQRS  </span>',
        unsafe_allow_html=True)

    st.sidebar.markdown(
        body='<span style="color: blue"> XQRS </span>',
        unsafe_allow_html=True)

    st.sidebar.markdown(
        body='<span style="color: violet"> SWT </span>',
        unsafe_allow_html=True)

    st.sidebar.markdown(
        body='<span style="color: black"> Hamilton </span>',
        unsafe_allow_html=True)

    # Initializing threads
    print('Waiting for HP connexion')

    hp = HeartyPatch_TCP_Parser()
    hp.start()
    print('ok')
    thr_data_delay = data_delay(data_freq=data_freq)
    compute_hr = compute_heart_rate()
    compute_hr_plot = compute_heart_rate()

 
    thr_data_delay.start()
    print('Starting stream\n')

    time.sleep(5)

    while True:

        spot_df = thr_data_delay.graph_data

        chart.data[0]['x'], chart.data[0]['y'] = \
            graph_data_handler.update_graph_data_stream(
                df_ecg=spot_df)

        compute_hr.compute(df_input=spot_df[
            -heartypach_frequency*hr_delay:])

        try:

            if trigger_timestamp-datetime.datetime.today() < (
                    datetime.timedelta(seconds=0)):

                compute_hr_plot.compute(df_input=thr_tcp_server_st.df)
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

            st_gqrs_tags = np.array(compute_hr.data['gqrs']['qrs'][
                -hr_displayed:])
            st_xqrs_tags = np.array(compute_hr.data['xqrs']['qrs'][
                -hr_displayed:])
            st_swt_tags = np.array(compute_hr.data['swt']['qrs'][
                -hr_displayed:])
            st_hamilton_tags = np.array(compute_hr.data['hamilton']['qrs'][
                -hr_displayed:])

            tags_list = [st_gqrs_tags,
                         st_xqrs_tags,
                         st_swt_tags,
                         st_hamilton_tags]

            for name_count in range(len(tags_list)):
                for i in range(len(st_gqrs_tags)):
                    try:
                        if tags_list[name_count][i] > chart.data[0]['x'][0]:
                            chart.layout.shapes[i + name_count*hr_displayed]\
                                .x0 = tags_list[name_count][i]
                            chart.layout.shapes[i + name_count*hr_displayed]\
                                .x1 = tags_list[name_count][i]
                        else:
                            chart.layout.shapes[i + name_count*hr_displayed]. \
                                x0 = tags_list[name_count][-1]
                            chart.layout.shapes[i + name_count*hr_displayed].\
                                x1 = tags_list[name_count][-1]
                    except Exception:
                        print('bad graph generation')

        except Exception:
            print('Error')
            try:
                for i in tags_list:
                    print(i)
            except Exception:
                pass

        chart_dispay.plotly_chart(figure_or_data=chart)
        time.sleep(1)
