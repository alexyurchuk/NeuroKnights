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
import threading 

from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from processing import DataProcessor  # EEG preprocessing
from analysis import FoCAA_KNN  # CCA-based SSVEP classification
from communications import SocketServer
from ui import UI  # Import the UI class
from qasync import QEventLoop  # Import QEventLoop for integrating PyQt and asyncio




class SSVEPAnalyzer:

    # initializes the SSVEP Analyzer
    def __init__(
        self,
        frequencies: list,
        controls: list = None,
        socket_server: SocketServer = None,
        ui: UI = None
    ) -> None:
        """
        Initializes the SSVEP Analyzer.

        Args:
            frequencies (list): Target SSVEP frequencies in Hz.
            controls (list, optional): List of controls corresponding to frequencies.
            socket_server (SocketServer, optional): Instance of SocketServer for communication.
            ui (UI, optional): Instance of the UI.
        """
        # Store the frequencies and controls
        self.frequencies = list(map(float, frequencies))
        self.controls = controls
        self.socket_server = socket_server

        # Store the UI instance and connect signals
        self.ui = ui
        self.ui.settings_changed.connect(self.on_settings_changed)

        # Initialize variables for two boards
        self.board_shim1 = None
        self.board_shim2 = None
        self.params1 = None
        self.params2 = None

        self.channels_per_board = 8  # Assuming 8 channels per board
        self.total_channels = self.channels_per_board * 2
        self.channels = list(range(self.channels_per_board))  # Channel indices per board
        self.channel_names = ["Ch{}".format(i + 1) for i in range(self.total_channels)]

        self.gain_value = 12  # Default gain value
        self.buffer_size = 450000
        self.cca_buffer_size = 500
        self.n_components = 1
        self._run = True

        # Initialize the data queue
        self.data_queue = self.ui.data_queue

        # Initialize variables for sampling rate
        self.sampling_rate = None  # Will be set after boards are initialized

        # Initialize other necessary variables
        self.turn = 0  # 0 or 1 based on player number

        # Flag to indicate if boards are initialized
        self.boards_initialized = False

        # Initialize the data processor and analysis classes (will be set after sampling rate is known)
        self.data_processor = None
        self.focaa_knn = None

    def on_settings_changed(self):
        """
        Handler for when the settings are changed in the UI.
        Initializes or reinitializes the board shims based on new settings.
        """
        # Retrieve settings from the UI
        board1_type_text = self.ui.board1_type.currentText()
        board2_type_text = self.ui.board2_type.currentText()

        board1_port = self.ui.board1_port.text()
        board2_port = self.ui.board2_port.text()

        # Map board type text to BoardIds
        board_type_mapping = {
            "SYNTHETIC_BOARD": BoardIds.SYNTHETIC_BOARD.value,
            "NEUROPAWN_KNIGHT_BOARD": BoardIds.NEUROPAWN_KNIGHT_BOARD.value
        }

        # Initialize BrainFlowInputParams
        self.params1 = BrainFlowInputParams()
        self.params2 = BrainFlowInputParams()

        # Set serial port if necessary
        if board1_type_text == "NEUROPAWN_KNIGHT_BOARD":
            self.params1.serial_port = board1_port
        if board2_type_text == "NEUROPAWN_KNIGHT_BOARD":
            self.params2.serial_port = board2_port

        # Create BoardShim instances
        self.board_shim1 = BoardShim(board_type_mapping[board1_type_text], self.params1)
        self.board_shim2 = BoardShim(board_type_mapping[board2_type_text], self.params2)

        # Reinitialize boards asynchronously
        asyncio.create_task(self.reinitialize_boards())

    async def reinitialize_boards(self):
        """
        Reinitializes the boards based on the new settings.
        """
        # Stop existing streams if any
        if self.boards_initialized:
            if self.board_shim1.is_prepared():
                self.board_shim1.stop_stream()
                self.board_shim1.release_session()
            if self.board_shim2.is_prepared():
                self.board_shim2.stop_stream()
                self.board_shim2.release_session()

        # Prepare sessions
        self.board_shim1.prepare_session()
        self.board_shim2.prepare_session()

        # Start streams
        self.board_shim1.start_stream(self.buffer_size)
        self.board_shim2.start_stream(self.buffer_size)

        # Get sampling rate (assuming both boards have the same sampling rate)
        self.sampling_rate = self.board_shim1.get_sampling_rate(self.board_shim1.board_id)

        # Initialize data processor and analysis classes
        self.data_processor = DataProcessor(self.sampling_rate)
        self.focaa_knn = FoCAA_KNN(
            self.n_components,
            self.frequencies,
            self.sampling_rate,
            self.cca_buffer_size,
        )

        # Wait until sufficient data is available
        while self.board_shim1.get_board_data_count() < self.cca_buffer_size or \
              self.board_shim2.get_board_data_count() < self.cca_buffer_size:
            await asyncio.sleep(0.5)

        self.boards_initialized = True

        print("Boards have been reinitialized and are ready.")
    
    def execute(self):
        # Integrate the PyQt event loop with asyncio
        loop = QEventLoop(self.app)
        asyncio.set_event_loop(loop)
        try:
            with loop:
                # Schedule the run coroutine
                asyncio.ensure_future(self.run())
                loop.run_forever()
        except KeyboardInterrupt:
            pass

    def start_ui(self):
        # Start the UI and pass the data queue
        self.ui = UI(self.data_queue)
        self.ui.run()

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
        if self.board_shim.board_id != -1: # Do not send serial init commands if using simulated board
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
        '''
        eeg_writer, eeg_csv_file = recording.initialize_writer(
            file_name="D:\\natHacks\\NeuroKnights\\src\\ssvep\\signal_processing\\data\\processed_eeg_data",
            header=self.channel_names + ["Timestamp"],
        )
        sk_cca_writer, sk_cca_csv = recording.initialize_writer(
            file_name="D:\\natHacks\\NeuroKnights\\src\\ssvep\\signal_processing\\data\\sk_cca_data",
            header=self.frequencies + ["Stimuli", "Freq", "Time"],
        )

        fbcca_writer, fbcca_csv = recording.initialize_writer(
            file_name="D:\\natHacks\\NeuroKnights\\src\\ssvep\\signal_processing\\data\\sk_cca_data",
            header=self.frequencies + ["Stimuli", "Freq", "Time"],
        )
        '''

        # initialize FoCAA-KNN and DataProcessor
        focca_knn = FoCAA_KNN(
            self.n_components,
            self.frequencies,
            self.sampling_rate,
            self.cca_buffer_size,
        )
        data_processor = DataProcessor(self.sampling_rate)

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

        # Wait for the boards to be initialized
        while self.board_shim1 is None or self.board_shim2 is None:
            await asyncio.sleep(0.1)

        # main loop for data acquisition and analysis
        while self._run:
            # fetch EEG data for analysis (specific channels)
            board_shim = self.get_players_board_schim()
            data = board_shim.get_current_board_data(self.cca_buffer_size)
            samp_timestamps = data[11].T
            samp_timestamps.shape = (samp_timestamps.shape[0], 1)
            
            # Fetch data from both boards
            data1 = self.board_shim1.get_current_board_data(self.cca_buffer_size)
            data2 = self.board_shim2.get_current_board_data(self.cca_buffer_size)

            t_stamp = time.time()  # record the current timestamp

            # Choose correct data based on turn
            data = data1 if self.turn == 1 else data2

            # process the EEG data (filtering, detrending, CAR)
            data = data_processor.process_data(data)

            # record preprocessed EEG data
            # eeg_writer.writerows(data)
            '''
            recording.record_eeg_data(
                writer=eeg_writer, data=data, samp_timestamps=samp_timestamps
            )
            '''

            # perform SSVEP classification using sklearn-based CCA
            sk_result = focca_knn.sk_findCorr(self.n_components, data)

            '''
            # record CCA results with metadata
            recording.record_cca_data(
                writer=sk_cca_writer,
                cca_coefs=sk_result,
                stimuli=False,  # stimuli status (active or not)
                frequency=0.0,  # TODO: Replace with actual stimulus frequency
                time=t_stamp,
            )
            '''

            print("=" * 100)
            print("Sklearn CCA Result:", sk_result)

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

            '''
            recording.record_cca_data(
                writer=fbcca_writer,
                cca_coefs=custom_result_fbcca,
                stimuli=False,  # stimuli status (active or not)
                frequency=0.0,  # TODO: Replace with actual stimulus frequency
                time=t_stamp,
            )
            '''

            print("Custom FBCCA coeff:", custom_result_fbcca)
            # print("Custom FoCCA Result:", custom_result_focca)
            print("=" * 100)

            # determine the predicted frequency class
            sklearn_predictedClass = np.argmax(sk_result)  # adjust for 0-based indexing
            print("Sklearn CCA prediction: ", sklearn_predictedClass)
            print(
                "Sklearn CCA prediction freq: ",
                self.frequencies[sklearn_predictedClass],
            )
            print("Custom FBCCA prediction: ", predicted_label_fbcca)
            print(
                "Custom FBCCA prediction freq: ",
                self.frequencies[predicted_label_fbcca],
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

            # Send control command if controls are defined
            if self.controls:
                command = self.controls[predicted_label_fbcca]
                await self.send_command(command)
            
            # Send data to the UI
            await self.data_queue.put({
                'timestamp': t_stamp,
                'eeg_data': data.tolist(),
                'sk_result': sk_result.tolist(),
                'fbcca_result': custom_result_fbcca.tolist(),
                'predicted_command': command if self.controls else None
            })

            await asyncio.sleep(1)  # pause before the next iteration

        '''
        # finalize and close all files
        recording.uninitialize_writer(eeg_csv_file)
        recording.uninitialize_writer(sk_cca_csv)
        recording.uninitialize_writer(fbcca_csv)
        '''

        await self.uninitialize()

    async def send_command(self, command):
        # Put the command into the data queue for the UI
        await self.data_queue.put({'command': command})


    # stops the analyzer gracefully when a signal is received.
    def stop(self, *args, **kwargs) -> None:
        """Gracefully stop the execution of the SSVEPAnalyzer

        _extended_summary_
        """
        print("Stopping SSVEP Analyzer....")

        self._run = False  # terminate the main loop

        # Stop the UI
        self.ui.close()
        self.app.quit()

        

        

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
