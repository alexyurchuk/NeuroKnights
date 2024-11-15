# src / ssvep / MatveysScripts / main.py

"""
Summary: 

Runs a real-time visualization of EEG signals using the BrainFlow library and PyQtGraph. 
Designed to work with the NeuroPawn BCI tech, specifically the Knight EEG board, 
displaying live data streams for analysis or debugging.

Author(s): Matvey Okoneshnikov
Commenter(s): Ivan Costa Neto
Last Updated: Nov. 15, 2024
"""


import argparse
import logging
import time
import pyqtgraph as pg  #real-time data visualization
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds  #interacts with Knight board
from brainflow.data_filter import DataFilter, FilterTypes, DetrendOperations  #preprocessing tools (i.e. filtering)
from pyqtgraph.Qt import QtGui, QtCore  #graphical interface

# initializes the EEG graphing tool with parameters from the connected Knight board
class Graph:
    def __init__(self, board_shim):
        self.board_id = board_shim.get_board_id()  #Knight board ID
        self.board_shim = board_shim  #board, channels, and parameters
        self.exg_channels = BoardShim.get_exg_channels(self.board_id)  #EEG channels connected
        self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)  #rate is in Hz
        self.update_speed_ms = 50  #graph updates every 50 ms
        self.window_size = 4  #displays data window of 4 s
        self.num_points = self.window_size * self.sampling_rate  #total data points displayed

        # sets up the GUI application window
        self.app = QtGui.QApplication([])
        self.win = pg.GraphicsWindow(title='BrainFlow Plot', size=(800, 600))

        # initialize the graph
        self._init_timeseries()

        # loops the GUI setup with a refreshing graph
        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(self.update_speed_ms)
        QtGui.QApplication.instance().exec_()

    # creates a row of plots for each EEG channel connected
    def _init_timeseries(self):
        self.plots = list()  #individual plots for each channel
        self.curves = list()  #graphical curves corresponding to the continuous data

        # iterates through each avaliable channel and initializates a time-series graph setup
        for i in range(len(self.exg_channels)):
            p = self.win.addPlot(row=i, col=0)
            p.showAxis('left', False)
            p.setMenuEnabled('left', False)
            p.showAxis('bottom', False)
            p.setMenuEnabled('bottom', False)
            if i == 0:
                p.setTitle('TimeSeries Plot')
            self.plots.append(p)
            curve = p.plot()
            self.curves.append(curve)

    # fetches the latest EEG data and updates the graph in real-time (with filtering)
    def update(self):
        data = self.board_shim.get_current_board_data(self.num_points)  #latest EEG data

        # iterates through each avaliable channel
        for count, channel in enumerate(self.exg_channels):
            # plot timeseries with preprocessing tools
            DataFilter.detrend(data[channel], DetrendOperations.CONSTANT.value)  #removes linear/constant signal trends
            DataFilter.perform_bandpass(data[channel], self.sampling_rate, 3.0, 45.0, 2,
                                        FilterTypes.BUTTERWORTH_ZERO_PHASE, 0)  #frequencies b/w 3-45 Hz (alpha, beta, low gamma bands)
            DataFilter.perform_bandstop(data[channel], self.sampling_rate, 48.0, 52.0, 2,
                                        FilterTypes.BUTTERWORTH_ZERO_PHASE, 0)  #notch filter (removes 48-52 Hz)
            DataFilter.perform_bandstop(data[channel], self.sampling_rate, 58.0, 62.0, 2,
                                        FilterTypes.BUTTERWORTH_ZERO_PHASE, 0)  #notch filter (removes 58-62 Hz)
            self.curves[count].setData(data[channel].tolist())

        # processes pending events, refreshing the display in real-time
        self.app.processEvents()

# establishes a connection with the Knight board using preset parameters and serial port 
def initialize_connection(port = "COM3", channels = range(9), gain_values = [12] * 8) -> BoardShim:
    params = BrainFlowInputParams()
    params.serial_port = port

    # identifies the board type and parameters associated for session
    board_shim = BoardShim(BoardIds.NEUROPAWN_KNIGHT_BOARD.value, params)

    board_shim.prepare_session()  #allocates resources for data streaming
    board_shim.start_stream(450000)  #buffer size

    # configurate params
    gain_value = 12

    # send setup commands to Knight board iterating through all channels
    for i in range(len(channels)):
        board_shim.config_board(f"chon_{channels[i]}_{gain_values[i]}")
        print(f"Connected channel {channels[i]} with gain {gain_values[i]}")
        time.sleep(0.5)

    # returns instance of BoardShim class along with the board, parameters, and accessable channels
    return board_shim


# initializes the system and starts real-time EEG visualization
def main():
    BoardShim.enable_dev_board_logger()  #enables troubleshooting
    logging.basicConfig(level=logging.DEBUG)  #configures the debug-level logger

    # prepare the board and connect to EEG channels
    board_shim = initialize_connection()

    # launches the GUI and begins real-time data visualization
    try:
        Graph(board_shim)  #begins graphing
    except BaseException:
        logging.warning('Exception', exc_info=True)  #logs any exceptions during execution
    finally:
        logging.info('End')
        # ensures proper cleanup by releasing the board session
        if board_shim.is_prepared():
            logging.info('Releasing session')
            board_shim.release_session()


if __name__ == '__main__':
    main()
