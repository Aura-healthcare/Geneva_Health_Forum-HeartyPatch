import numpy as np
from hrvanalysis import (remove_outliers,
                         remove_ectopic_beats,
                         interpolate_nan_values)
from hrvanalysis import plot_psd


def generate_psd_plot_hamilton(data: dict, sampling_frequency: int = 128):

    rr_intervals_list = data['hamilton']['rr_intervals']

    # Processing pré-pipeline
    # This remove outliers from signal
    rr_intervals_without_outliers = remove_outliers(
        rr_intervals=rr_intervals_list,
        low_rri=300, high_rri=2000)

    # This replace outliers nan values with linear interpolation
    interpolated_rr_intervals = interpolate_nan_values(
        rr_intervals=rr_intervals_without_outliers,
        interpolation_method="linear")

    # This remove ectopic beats from signal
    nn_intervals_list = remove_ectopic_beats(
        rr_intervals=interpolated_rr_intervals,
        method="malik")
    # This replace ectopic beats nan values with linear interpolation
    interpolated_nn_intervals = interpolate_nan_values(
        rr_intervals=nn_intervals_list)

    plot_psd(interpolated_nn_intervals, method="lomb", sampling_frequency=128)


if __name__ == '__main__':
    data = np.load('data/simulation/data_df_simulation.npy',
                   allow_pickle='TRUE').item()
    generate_psd_plot_hamilton(data)
