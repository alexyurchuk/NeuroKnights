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

from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from processing import DataProcessor  # EEG preprocessing
from analysis import FoCAA_KNN  # CCA-based SSVEP classification

class SSVEPAnalyzer:

    # initializes the SSVEP Analyzer
    def __init__(
        self,
        board_shim: BoardShim,
        frequencies: list,
        channels: list,
        channel_names: list,
        gain_value: int = 12,
        buffer_size: int = 450000,
        cca_buffer_size: int = 1000,
        n_components: int = 1,
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
        self.frequencies = list(map(float, frequencies))  # convert frequencies to floats
        self.sampling_rate = BoardShim.get_sampling_rate(board_id=board_shim.get_board_id())
        self.n_components = n_components
        self.channels = channels  # indices of EEG channels used for analysis
        self.channel_names = channel_names  # names of the channels
        self.gain_value = gain_value  # gain value for channel amplification
        self.buffer_size = buffer_size  # data stream buffer size
        self.cca_buffer_size = cca_buffer_size  # number of samples per CCA analysis
        self._run = True  # flag to control the main loop

    # prepares the board session and enables the EEG channels
    def initialize(self) -> None:
        print("Initializing channels...")
        self.board_shim.prepare_session()  # prepares the EEG board for streaming
        time.sleep(1)
        self.board_shim.start_stream(self.buffer_size)  # starts data streaming
        time.sleep(1)
        for channel in self.channels:
            self.board_shim.config_board(f"chon_{channel}_{self.gain_value}")  # enable channel
            print(f"Enabled channel {channel} with gain {self.gain_value}.")
            time.sleep(1)


    # main function to start data acquisition, processing, and SSVEP classification.
    def run(self) -> None:
        self.initialize()

        # initialize writers for EEG data and CCA results
        eeg_writer, eeg_csv_file = recording.initialize_writer(
            file_name="./data/processed_eeg_data", header=self.channel_names
        )
        sk_cca_writer, sk_cca_csv = recording.initialize_writer(
            file_name="./data/sk_cca_data",
            header=self.frequencies + ["Stimuli", "Freq", "Time"],
        )

        # initialize FoCAA-KNN and DataProcessor
        focca_knn = FoCAA_KNN(self.n_components, self.frequencies, self.sampling_rate, self.cca_buffer_size)
        data_processor = DataProcessor(self.sampling_rate)

        # ensure sufficient data is available for processing
        while self.board_shim.get_board_data_count() < self.cca_buffer_size:
            time.sleep(0.5)

        # main loop for data acquisition and analysis
        while self._run:
            # fetch EEG data for analysis (specific channels)
            data = self.board_shim.get_current_board_data(self.cca_buffer_size)[1:4]

            t_stamp = time.time()  # record the current timestamp

            # process the EEG data (filtering, detrending, CAR)
            data = data_processor.process_data(data)

            # record preprocessed EEG data
            recording.record_eeg_data(writer=eeg_writer, data=data)

            # perform SSVEP classification using sklearn-based CCA
            sk_result = focca_knn.sk_findCorr(self.n_components, data)

            # record CCA results with metadata
            recording.record_cca_data(
                writer=sk_cca_writer,
                cca_coefs=sk_result,
                stimuli=True,  # stimuli status (active or not)
                frequency=0.0,  # TODO: Replace with actual stimulus frequency
                time=t_stamp,
            )

            # perform custom CCA analysis (manual implementation)
            cca_analysis_result = focca_knn.cca_analysis(data=data)

            print("=" * 100)
            print("Sklearn CCA Result:", sk_result)
            print("Custom CCA Result:", cca_analysis_result)
            print("=" * 100)

            # determine the predicted frequency class
            predictedClass = np.argmax(sk_result) + 1  # adjust for 1-based indexing
            print(predictedClass)

            time.sleep(1)  # pause before the next iteration

        # finalize and close all files
        recording.uninitialize_writer(eeg_csv_file)
        recording.uninitialize_writer(sk_cca_csv)

        self.uninitialize()


    # stops the analyzer gracefully when a signal is received.
    def stop(self, sig, frame) -> None:
        """
        Args:
            sig: signal type
            frame: current stack frame
        """
        print("Stopping SSVEP Analyzer....")
        self._run = False  # terminate the main loop


    # disables the channels and stops the board session
    def uninitialize(self) -> None:
        print("Unitializing...")
        for channel in self.channels:
            self.board_shim.config_board(f"choff_{channel}")  # disable channel
            print(f"Disabled channel {channel}.")
            time.sleep(1)
        self.board_shim.stop_stream()  # stop data streaming
        self.board_shim.release_session()  # release resources


if __name__ == "__main__":
    # define target SSVEP frequencies
    frequencies = [8, 10, 12, 15]

    # enable BrainFlow debug logging
    BoardShim.enable_dev_board_logger()

    # set up connection parameters for the EEG board
    params = BrainFlowInputParams()
    params.serial_port = "COM6"  # adjust based on your system configuration

    # initialize the EEG board
    board = BoardShim(BoardIds.NEUROPAWN_KNIGHT_BOARD, params)

    # define EEG channels and their names
    channels = [1, 2, 3]  # modify based on your board configuration
    channel_names = ["O1", "Oz", "O2"]

    # create an instance of SSVEPAnalyzer
    ssvep_analyzer = SSVEPAnalyzer(board, frequencies, channels, channel_names)

    # attach a signal handler for graceful termination
    signal.signal(signal.SIGINT, ssvep_analyzer.stop)

    # run the analyzer
    ssvep_analyzer.run()
