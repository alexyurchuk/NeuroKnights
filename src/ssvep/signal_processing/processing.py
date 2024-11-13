import numpy as np

from brainflow.data_filter import DataFilter, FilterTypes, DetrendOperations


class DataProcessor:
    def __init__(self, sampling_rate) -> None:
        self.sampling_rate = sampling_rate

    def process_data(self, data: np.ndarray) -> np.ndarray:
        for i in range(0, len(data)):
            DataFilter.detrend(data[i], DetrendOperations.CONSTANT.value)
            DataFilter.perform_bandpass(
                data=data[i],
                sampling_rate=self.sampling_rate,
                start_freq=6.0,
                stop_freq=40.0,
                order=2,
                filter_type=FilterTypes.BUTTERWORTH_ZERO_PHASE.value,
                ripple=0,
            )
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
            # data[i] -= data[i].mean()
        return data
