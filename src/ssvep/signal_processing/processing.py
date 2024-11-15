# src / ssvep / signal_processing / processing.py

"""
Summary:

Defines the DataProcessor class, which is responsible for preprocessing EEG signals before analysis. 
It ensures the EEG data is cleaned, filtered, and prepared for further steps like 
SSVEP classification or other feature extraction techniques.

Author(s): Alex Yurchuk
Commenter(s): Ivan Costa Neto
Last Updated: Nov. 15, 2024
"""

import numpy as np
from brainflow.data_filter import DataFilter, FilterTypes, DetrendOperations


#  initializes the DataProcessor with the given sampling rate
class DataProcessor:
    def __init__(self, sampling_rate) -> None:
        """
        Args:
            sampling_rate (int): The EEG sampling rate in Hz
        """
        self.sampling_rate = sampling_rate


    # preprocesses EEG data by detrending, filtering, and applying CAR
    def process_data(self, data: np.ndarray) -> np.ndarray:
        """
        Args:
            data (np.ndarray): EEG data matrix (shape: [channels, samples])

        Returns:
            data (np.ndarray): preprocessed EEG data (shape: [samples, channels])
        """
        for i in range(0, len(data)):  # loop through each EEG channel
            # detrend to remove linear drifts (DC offset)
            DataFilter.detrend(data[i], DetrendOperations.CONSTANT.value)

            # bandpass filter (6-40 Hz) to isolate EEG frequencies of interest
            DataFilter.perform_bandpass(
                data=data[i],
                sampling_rate=self.sampling_rate,
                start_freq=6.0,
                stop_freq=40.0,
                order=2,
                filter_type=FilterTypes.BUTTERWORTH_ZERO_PHASE.value,  # minimal phase distortion
                ripple=0,
            )

            # bandstop (notch) filters to remove powerline noise at 48 Hz to 62 Hz
            DataFilter.perform_bandstop(
                data=data[i],
                sampling_rate=self.sampling_rate,
                start_freq=48.0,
                stop_freq=52.0,
                order=2,
                filter_type=FilterTypes.BUTTERWORTH_ZERO_PHASE.value,
                ripple=0,
            )
            DataFilter.perform_bandstop(
                data=data[i],
                sampling_rate=self.sampling_rate,
                start_freq=58.0,
                stop_freq=62.0,
                order=2,
                filter_type=FilterTypes.BUTTERWORTH_ZERO_PHASE.value,
                ripple=0,
            )

        # transpose data to make it [samples, channels] for further processing
        data = data.T

        # apply Common Average Referencing (CAR)
        data = self.car(data)

        return data


    # computes the Common Average Reference (CAR) for EEG signals
    def car(self, data: np.ndarray, reference_channel: int = None) -> np.ndarray:
        """
        Args:
            data (np.ndarray): EEG data matrix (shape: [samples, channels])
            reference_channel (int, optional): reference channel index (if None --> average of all channels is used)

        Returns:
            data_car (np.ndarray): EEG data after CAR (shape: [samples, channels])
        """
        data_car = data.copy()  # a copy to avoid modifying the original data

        if reference_channel is not None:
            # subtract the reference signal from all other channels
            channels = np.delete(np.arange(data_car.shape[1]), reference_channel)  # all channels except the reference

            if data_car.ndim > 2:  # handles multi-dimensional data (e.g., trial-based)
                data_car[:, channels, :] -= np.reshape(
                    data_car[:, reference_channel, :],
                    (data_car.shape[0], 1, data_car.shape[-1]),
                )
            else:
                data_car[:, channels] -= data_car[:, reference_channel].reshape(-1, 1)

        else:
            # compute the average signal across all channels
            average_potential = np.mean(data_car, axis=1, keepdims=True)  # shape: [samples, 1]

            # ensure it's a numpy array for consistency
            average_potential = (
                np.array(average_potential)
                if not isinstance(average_potential, np.ndarray)
                else average_potential
            )

            # subtract the average signal from all channels
            data_car -= average_potential

        return data_car
