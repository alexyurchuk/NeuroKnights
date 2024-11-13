import time
import numpy as np
import signal
import serial.tools.list_ports

from functools import partial
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds

from processing import DataProcessor
from analysis import FoCAA_KNN


class SSVEPAnalyzer:
    def __init__(
        self,
        board_shim: BoardShim,
        frequencies: list,
        channels: list,
        gain_value: int = 12,
        buffer_size: int = 450000,
        cca_buffer_size: int = 1000,
        n_components: int = 1,
    ):
        """SSVEP Analyzer

        Uses FoCAA-KNN pipeline

        Args:
            board_shim (BoardShim): _description_
            frequencies (list): _description_
            channels (list): _description_
            gain_value (int, optional): _description_. Defaults to 12.
            buffer_size (int, optional): _description_. Defaults to 450000.
            cca_buffer_size (int, optional): _description_. Defaults to 1000.
            n_components (int, optional): _description_. Defaults to 1.
        """
        self.board_shim = board_shim
        self.frequencies = map(float, frequencies)
        self.sampling_rate = BoardShim.get_sampling_rate(
            board_id=board_shim.get_board_id()
        )
        self.n_components = n_components
        self.channels = channels
        self.gain_value = gain_value
        self.buffer_size = buffer_size
        self.cca_buffer_size = cca_buffer_size
        self._run = True

    def initialize(self):
        """Prepare the board and enable channels

        _extended_summary_
        """
        print("Initializing channels...")
        self.board_shim.prepare_session()
        time.sleep(1)
        self.board_shim.start_stream(self.buffer_size)
        time.sleep(1)
        for channel in self.channels:
            self.board_shim.config_board(f"chon_{channel}_{self.gain_value}")
            print(
                f"Enabled channel {channel} with gain {self.gain_value}."
            )  # change to logging
            time.sleep(1)

    def run(self):
        self.initialize()

        focca_knn = FoCAA_KNN(
            self.n_components,
            self.frequencies,
            self.sampling_rate,
            self.cca_buffer_size,
        )

        data_processor = DataProcessor(self.sampling_rate)

        while self.board_shim.get_board_data_count() < self.cca_buffer_size:
            time.sleep(0.5)

        while self._run:
            data = self.board_shim.get_current_board_data(self.cca_buffer_size)[
                1:4  # dont forget to change this
            ]

            data = data_processor.process_data(data)

            result = focca_knn.findCorr(self.n_components, data)

            predictedClass = np.argmax(result) + 1
            print(predictedClass)

            time.sleep(1)

        self.uninitialize()

    def stop(self, sig, frame):
        print("Stopping SSVEP Analyzer....")
        self._run = False

    def uninitialize(self):
        print("Unitializing...")
        for channel in self.channels:
            self.board_shim.config_board(f"choff_{channel}")
            print(f"Disabled channel {channel}.")
            time.sleep(1)
        self.board_shim.stop_stream()
        self.board_shim.release_session()


if __name__ == "__main__":
    frequencies = [8, 10, 12, 15]

    BoardShim.enable_dev_board_logger()

    params = BrainFlowInputParams()

    params.serial_port = "COM6"

    board = BoardShim(BoardIds.NEUROPAWN_KNIGHT_BOARD, params)

    channels = [1, 2, 3]

    ssvep_analyzer = SSVEPAnalyzer(board, frequencies, channels)

    signal.signal(signal.SIGINT, ssvep_analyzer.stop)

    ssvep_analyzer.run()