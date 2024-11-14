import argparse
import logging
import time
import pyqtgraph as pg
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import DataFilter, FilterTypes, DetrendOperations
from pyqtgraph.Qt import QtGui, QtCore


class Graph:
    def __init__(self, board_shim):
        self.board_id = board_shim.get_board_id()
        self.board_shim = board_shim
        self.exg_channels = BoardShim.get_exg_channels(self.board_id)
        self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)
        self.update_speed_ms = 50
        self.window_size = 4
        self.num_points = self.window_size * self.sampling_rate

        self.app = QtGui.QApplication([])
        self.win = pg.GraphicsWindow(title='BrainFlow Plot', size=(800, 600))

        self._init_timeseries()

        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(self.update_speed_ms)
        QtGui.QApplication.instance().exec_()

    def _init_timeseries(self):
        self.plots = []
        self.curves = []
        for i in range(len(self.exg_channels)):
            plot = self.win.addPlot(row=i, col=0)
            plot.showAxis('left', False)
            plot.setMenuEnabled('left', False)
            plot.showAxis('bottom', False)
            plot.setMenuEnabled('bottom', False)
            if i == 0:
                plot.setTitle('EEG TimeSeries')
            self.plots.append(plot)
            curve = plot.plot()
            self.curves.append(curve)

    def update(self):
        data = self.board_shim.get_current_board_data(self.num_points)
        for count, channel in enumerate(self.exg_channels):
            DataFilter.detrend(data[channel], DetrendOperations.CONSTANT.value)
            DataFilter.perform_bandpass(data[channel], self.sampling_rate, 3.0, 45.0, 2,
                                        FilterTypes.BUTTERWORTH_ZERO_PHASE, 0)
            DataFilter.perform_bandstop(data[channel], self.sampling_rate, 48.0, 52.0, 2,
                                        FilterTypes.BUTTERWORTH_ZERO_PHASE, 0)
            DataFilter.perform_bandstop(data[channel], self.sampling_rate, 58.0, 62.0, 2,
                                        FilterTypes.BUTTERWORTH_ZERO_PHASE, 0)
            self.curves[count].setData(data[channel].tolist())

        self.app.processEvents()


def main():
    BoardShim.enable_dev_board_logger()
    logging.basicConfig(level=logging.DEBUG)

    # Define basic parameters for BrainFlow
    params = BrainFlowInputParams()
    params.serial_port = "COM3"  # Adjust this port based on your actual setup

    # Initialize and start the board session
    board_shim = BoardShim(BoardIds.NEUROPAWN_KNIGHT_BOARD.value, params)
    try:
        board_shim.prepare_session()
        board_shim.start_stream(450000)

        # Set up channel configurations for the NeuroPawn Knight board
        channels = list(range(0, 9))
        gain_value = 12

        for channel in channels:
            board_shim.config_board(f"chon_{channel}_{gain_value}")
            print(f"Configured channel {channel} with gain {gain_value}")
            time.sleep(2.5)  # Brief delay for each channel configuration

        Graph(board_shim)

    except BaseException as e:
        logging.warning('An error occurred', exc_info=True)
    finally:
        logging.info('Ending session')
        if board_shim.is_prepared():
            logging.info('Releasing session')
            board_shim.release_session()


if __name__ == '__main__':
    main()
