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

        data = data.T

        data = self.car(data)

        return data

    def car(self, data: np.ndarray, reference_channel: int = None) -> np.ndarray:
        """Computes the common average reference (CAR) for EEG signals.

        _extended_summary_

        Args:
            data (np.ndarray): EEG data matrix with dimensions (number of samples, number of channels).
            reference_channel (int, optional): Index of the reference channel for CAR. If None, the average
                                               potential across all electrodes is used. Defaults to None.

        Returns:
            np.ndarray: _description_
        """
        data_car = data.copy()

        if reference_channel is not None:
            # Subtract the reference signal from each electrode's potential
            channels = np.delete(np.arange(data_car.shape[1]), reference_channel)

            if data_car.ndim > 2:
                data_car[:, channels, :] -= np.reshape(
                    data_car[:, reference_channel, :],
                    (data_car.shape[0], 1, data_car.shape[-1]),
                )
            else:
                data_car[:, channels] -= data_car[:, reference_channel].reshape(-1, 1)

        else:
            average_potential = np.mean(data_car, axis=1, keepdims=True)
            average_potential = (
                np.array(average_potential)
                if not isinstance(average_potential, np.ndarray)
                else average_potential
            )
            data_car -= average_potential
        return data_car
