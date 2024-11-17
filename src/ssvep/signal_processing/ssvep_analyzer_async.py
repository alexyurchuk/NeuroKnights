# src / ssvep / signal_processing / ssvep_analyzer.py

"""
Summary:

Implements a real-time system for analyzing Steady-State Visual Evoked Potentials (SSVEP) using EEG data.
It leverages BrainFlow for EEG data acquisition, applies preprocessing techniques, and performs 
frequency classification using Canonical Correlation Analysis (CCA) through the FoCAA-KNN framework.

Author(s): Alex Yurchuk
Commenter(s): Ivan Costa Neto
Last Updated: Nov. 15, 2024
"""

import time
import numpy as np
import signal
import serial.tools.list_ports
import recording  # custom module for data recording
import asyncio

from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from processing import DataProcessor  # EEG preprocessing
from analysis import FoCAA  # CCA-based SSVEP classification
from communicating import SocketServer


class SSVEPAnalyzer:

    # initializes the SSVEP Analyzer
    def __init__(
        self,
        board_shim: BoardShim,
        frequencies: list,
        channels: list,
        channel_names: list,
        # two_players: bool = False,
        socket_server: SocketServer,
        second_board_shim: BoardShim = None,
        gain_value: int = 12,
        buffer_size: int = 450000,
        cca_buffer_size: int = 500,
        n_components: int = 1,
        controls: list = None,
    ) -> None:
        """
        Args:
            board_shim (BoardShim): instance of BrainFlow's BoardShim for data streaming
            frequencies (list): target SSVEP frequencies in Hz
            channels (list): EEG channel indices
            channel_names (list): readable names for the channels
            gain_value (int, optional): gain value for the EEG channels (default: 12)
            buffer_size (int, optional): buffer size for the EEG data stream (default: 450000)
            cca_buffer_size (int, optional): # of samples for CCA analysis (default: 1000)
            n_components (int, optional): # of CCA components to compute (default: 1)
        """
        self.board_shim = board_shim
        self.turn = 0  # 0 or 1 based on player number
        self.second_board_schim = second_board_shim
        self.frequencies = list(
            map(float, frequencies)
        )  # convert frequencies to floats
        self.sampling_rate = BoardShim.get_sampling_rate(
            board_id=board_shim.get_board_id()
        )
        self.n_components = n_components
        self.channels = channels  # indices of EEG channels used for analysis
        self.channel_names = channel_names  # names of the channels
        self.gain_value = gain_value  # gain value for channel amplification
        self.buffer_size = buffer_size  # data stream buffer size
        self.cca_buffer_size = cca_buffer_size  # number of samples per CCA analysis
        self._run = True  # flag to control the main loop
        self.controls = controls
        self.socket_server = socket_server

    def switch_turn(self):
        self.turn = 1 if self.turn == 0 else 0
        return

    def get_players_board_schim(self):
        """Based on the self.turn variable return player's board_schim"""
        if self.turn == 0:
            return self.board_shim
        return self.second_board_schim

    # prepares the board session and enables the EEG channels
    async def initialize(self) -> None:
        print("Initializing channels...")
        self.board_shim.prepare_session()  # prepares the EEG board for streaming
        await asyncio.sleep(1)
        self.board_shim.start_stream(self.buffer_size)  # starts data streaming
        await asyncio.sleep(1)
        for channel in self.channels:
            self.board_shim.config_board(
                f"chon_{channel}_{self.gain_value}"
            )  # enable channel
            await asyncio.sleep(1)
            self.board_shim.config_board(f"rldadd_{channel}")  # enable rdl for channel
            print(f"Enabled channel {channel} with gain {self.gain_value}.")
            await asyncio.sleep(1)

    # main function to start data acquisition, processing, and SSVEP classification.
    async def run(self) -> None:
        await self.initialize()

        # initialize writers for EEG data and CCA results
        # eeg_writer, eeg_csv_file = recording.initialize_writer(
        #     file_name="D:\\natHacks\\NeuroKnights\\src\\ssvep\\signal_processing\\data\\processed_eeg_data",
        #     header=self.channel_names + ["Timestamp"],
        # )
        # sk_cca_writer, sk_cca_csv = recording.initialize_writer(
        #     file_name="D:\\natHacks\\NeuroKnights\\src\\ssvep\\signal_processing\\data\\sk_cca_data",
        #     header=self.frequencies + ["Stimuli", "Freq", "Time"],
        # )

        # fbcca_writer, fbcca_csv = recording.initialize_writer(
        #     file_name="D:\\natHacks\\NeuroKnights\\src\\ssvep\\signal_processing\\data\\sk_cca_data",
        #     header=self.frequencies + ["Stimuli", "Freq", "Time"],
        # )

        knn_writer, knn_csv = recording.initialize_writer(
            file_name="D:\\natHacks\\NeuroKnights\\src\\ssvep\\signal_processing\\data\\knn_data_no_s",
            header=self.frequencies
            + [f"PSD_{x}" for x in self.frequencies]
            + ["Stimuli", "Freq", "Time"],
        )

        # initialize FoCAA and DataProcessor
        focca_knn = FoCAA(
            self.n_components,
            self.frequencies,
            self.sampling_rate,
            self.cca_buffer_size,
        )
        data_processor = DataProcessor(self.sampling_rate, self.frequencies)

        # ensure sufficient data is available for processing
        while self.board_shim.get_board_data_count() < self.cca_buffer_size:
            await asyncio.sleep(0.5)

        # ---------------------- FBCCA Config [BEG] ----------------------
        # a = [0.01, 0.1, 0, 3, 5]
        # b = [0.01, 0.1, 0, 1, 10]
        a = [0.01]
        b = [0.001]
        filter_banks = [
            [6, 8, 10, 12, 14, 16, 18],
            [35, 35, 35, 35, 35, 35, 35],
        ]
        order = 4  # Define filter order
        notch_filter = "off"  # on or off
        filter_active = "on"  # on or off
        type_filter = "bandpass"  # low, high, bandpass, or bandstop
        notch_freq = (
            50  # Define frequency to be removed from the signal for notch filter (Hz)
        )
        quality_factor = 20  # Define quality factor for the notch filter
        # ---------------------- FBCCA Config [END] ----------------------

        number_of_conseq = 3
        conseq = []

        # main loop for data acquisition and analysis
        while self._run:

            # fetch EEG data for analysis (specific channels)
            board_shim = self.get_players_board_schim()
            data = board_shim.get_current_board_data(self.cca_buffer_size)
            samp_timestamps = data[11].T
            samp_timestamps.shape = (samp_timestamps.shape[0], 1)
            data = data[self.channels]  # dont forget to change this

            t_stamp = time.time()  # record the current timestamp

            # process the EEG data (filtering, detrending, CAR)
            data = data_processor.process_data(data)

            psd_values = data_processor.get_PSD_values(data.T)

            # record preprocessed EEG data
            # eeg_writer.writerows(data)
            # recording.record_eeg_data(
            #     writer=eeg_writer, data=data, samp_timestamps=samp_timestamps
            # )

            # perform SSVEP classification using sklearn-based CCA
            # sk_result = focca_knn.sk_findCorr(self.n_components, data)

            # record CCA results with metadata
            # recording.record_cca_data(
            #     writer=sk_cca_writer,
            #     cca_coefs=sk_result,
            #     stimuli=False,  # stimuli status (active or not)
            #     frequency=0.0,  # TODO: Replace with actual stimulus frequency
            #     time=t_stamp,
            # )

            print("=" * 100)
            # print("Sklearn CCA Result:", sk_result)

            # custom_result = []

            # for freq_id in range(0, (focca_knn.reference_signals.shape)[0]):
            #     Xb = np.squeeze(focca_knn.reference_signals[freq_id, :, :]).T
            #     Wa, Wb = focca_knn.cca_analysis(Xa=data, Xb=Xb)
            #     custom_result.append(np.array([Wa, Wb]))
            # custom_result = np.array(custom_result)

            # perform custom CCA analysis (manual implementation)
            # custom_result_focca = focca_knn.focca_analysis(data=data, a=a, b=b)

            custom_result_fbcca, predicted_label_fbcca = focca_knn.fbcca_analysis(
                data=data,
                a=a,
                b=b,
                filter_banks=filter_banks,
                order=order,
                notch_freq=notch_freq,
                quality_factor=quality_factor,
                filter_active=filter_active,
                notch_filter=notch_filter,
                type_filter=type_filter,
            )

            # recording.record_cca_data(
            #     writer=fbcca_writer,
            #     cca_coefs=custom_result_fbcca,
            #     stimuli=False,  # stimuli status (active or not)
            #     frequency=0.0,  # TODO: Replace with actual stimulus frequency
            #     time=t_stamp,
            # )

            print("Custom FBCCA coeff:", custom_result_fbcca)
            # print("Custom FoCCA Result:", custom_result_focca)

            # determine the predicted frequency class
            # sklearn_predictedClass = np.argmax(sk_result)  # adjust for 0-based indexing
            # print("Sklearn CCA prediction: ", sklearn_predictedClass)
            # print(
            #     "Sklearn CCA prediction freq: ",
            #     self.frequencies[sklearn_predictedClass],
            # )
            print("Custom FBCCA prediction: ", predicted_label_fbcca)
            print(
                "Custom FBCCA prediction freq: ",
                self.frequencies[predicted_label_fbcca],
            )

            print("=" * 100)

            data_for_KNN = np.array([custom_result_fbcca, psd_values])

            data_for_csv = np.concatenate(data_for_KNN)

            recording.record_cca_data(
                writer=knn_writer,
                cca_coefs=data_for_csv,
                stimuli=False,  # stimuli status (active or not)
                frequency=-1,  # TODO: Replace with actual stimulus frequency
                time=t_stamp,
            )

            # if self.controls:
            #     # send(self.controls[predicted_label_fbcca])
            #     pass

            # custom_predictedClass = (
            #     np.argmax(custom_result_focca) + 1
            # )  # adjust for 1-based indexing

            # print("Custom FoCCA prediction: ", custom_predictedClass + 1)
            # print(
            #     "Custom FoCCA prediction freq: ",
            #     self.frequencies[custom_predictedClass],
            # )

            await asyncio.sleep(1)  # pause before the next iteration

        # finalize and close all files
        # recording.uninitialize_writer(eeg_csv_file)
        # recording.uninitialize_writer(sk_cca_csv)
        # recording.uninitialize_writer(fbcca_csv)
        recording.uninitialize_writer(knn_csv)

        await self.uninitialize()

    # stops the analyzer gracefully when a signal is received.
    def stop(self, *args, **kwargs) -> None:
        """Gracefully stop the execution of the SSVEPAnalyzer

        _extended_summary_
        """
        print("Stopping SSVEP Analyzer....")
        self._run = False  # terminate the main loop

    # disables the channels and stops the board session
    async def uninitialize(self) -> None:
        print("Unitializing...")
        for channel in self.channels:
            self.board_shim.config_board(f"choff_{channel}")  # disable channel
            print(f"Disabled channel {channel}.")
            await asyncio.sleep(1)
        self.board_shim.stop_stream()  # stop data streaming
        self.board_shim.release_session()  # release resources


async def listener(ssvep_analyzer: SSVEPAnalyzer):
    while ssvep_analyzer._run:
        print(f"Conquerent task....")
        await asyncio.sleep(1)


async def main(ssvep_analyzer):
    await asyncio.gather(ssvep_analyzer.run())  # , listener(ssvep_analyzer)


if __name__ == "__main__":
    # ================== SSVEPAnalyzer Config ================================
    # define target SSVEP frequencies
    # frequencies = [7, 9, 11, 13, 15, 17]  # 10, 19
    frequencies = [6.66, 7.5, 8.57, 10, 12, 15]

    controls = ["W", "A", "S", "D", "Q", "E"]

    # frequencies = [8, 10, 12, 15]

    # enable BrainFlow debug logging
    BoardShim.enable_dev_board_logger()

    # set up connection parameters for the EEG board
    params_1 = BrainFlowInputParams()
    params_1.serial_port = "COM6"  # adjust based on your system configuration

    # initialize the EEG board
    board_1 = BoardShim(BoardIds.NEUROPAWN_KNIGHT_BOARD, params_1)

    # define EEG channels and their names
    # modify based on your board configuration
    channels = [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
    ]
    channel_names = ["PO8", "PO4", "O2", "POZ", "Oz", "PO3", "O1", "PO7"]

    # create an instance of SSVEPAnalyzer
    ssvep_analyzer = SSVEPAnalyzer(
        board_1, frequencies, channels, channel_names, controls=controls
    )
    # ================== SSVEPAnalyzer Config ================================

    # attach a signal handler for graceful termination
    signal.signal(signal.SIGINT, ssvep_analyzer.stop)

    asyncio.run(main(ssvep_analyzer=ssvep_analyzer))
