import logging
import math
import time
import numpy as np
import pyqtgraph as pg
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import DataFilter, FilterTypes, DetrendOperations
from enum import Enum  # Import Enum for WindowFunctions
from pyqtgraph.Qt import QtGui, QtCore
import serial.tools.list_ports
from functools import partial


# Define WindowFunctions Enum
class WindowFunctions(Enum):
    NO_WINDOW = 0
    HANNING = 1
    HAMMING = 2
    BLACKMAN_HARRIS = 3


class Graph:
    def __init__(self):
        self.board_shim = None
        self.board_id = None
        self.exg_channels = []
        self.sampling_rate = None
        self.update_speed_ms = 50
        self.window_size = 4
        self.num_points = None
        self.mode = "SSVEP"  # Default mode

        self.app = QtGui.QApplication([])
        self.win = QtGui.QWidget()
        self.win.setWindowTitle("BrainFlow Plot")
        self.win.resize(1000, 800)

        self.init_ui()
        self.win.show()

        QtGui.QApplication.instance().exec_()

    def init_ui(self):
        self.main_layout = QtGui.QHBoxLayout(self.win)
        self.graph_layout_widget = pg.GraphicsLayoutWidget()
        self.main_layout.addWidget(self.graph_layout_widget, stretch=2)

        self.controls_widget = QtGui.QWidget()
        self.controls_layout = QtGui.QVBoxLayout(self.controls_widget)
        self.controls_layout.setAlignment(QtCore.Qt.AlignTop)
        self.main_layout.addWidget(self.controls_widget, stretch=1)

        self._init_timeseries()
        self._init_controls()

    def _init_timeseries(self):
        self.plots = []
        self.curves = []
        self.peak_freq_labels = []  # Add this line
        for i in range(8):  # Assuming 8 channels maximum
            p = self.graph_layout_widget.addPlot(row=i, col=0)
            if i == 0:
                p.setTitle("TimeSeries Plot")
            self.plots.append(p)
            curve = p.plot()
            self.curves.append(curve)
            # Create peak frequency label
            peak_freq_label = pg.TextItem("", anchor=(1, 0))
            peak_freq_label.setPos(0, 0)  # Set initial position
            p.addItem(peak_freq_label)
            self.peak_freq_labels.append(peak_freq_label)

        self.ssvep_plot = self.graph_layout_widget.addPlot(row=8, col=0)
        self.ssvep_plot.setTitle("SSVEP/P300 Plot")
        self.ssvep_plot.setLabel("left", "Intensity")
        self.ssvep_plot.setLabel("bottom", "Frequency (Hz)")
        self.ssvep_curve = self.ssvep_plot.plot()

    def _init_controls(self):
        # Board Info
        board_info_layout = QtGui.QHBoxLayout()
        self.board_name_label = QtGui.QLabel("Board Name: Not Connected")
        self.connection_status_label = QtGui.QLabel("Status: Disconnected")
        board_info_layout.addWidget(self.board_name_label)
        board_info_layout.addWidget(self.connection_status_label)
        self.controls_layout.addLayout(board_info_layout)

        # Mode Switch
        mode_label = QtGui.QLabel("Mode:")
        self.mode_combo = QtGui.QComboBox()
        self.mode_combo.addItems(["SSVEP", "P300"])
        self.mode_combo.currentTextChanged.connect(self.mode_changed)
        mode_layout = QtGui.QHBoxLayout()
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_combo)
        self.controls_layout.addLayout(mode_layout)

        # COM Port Dropdown
        com_port_label = QtGui.QLabel("COM Port:")
        self.com_port_combo = QtGui.QComboBox()
        available_ports = self.get_available_com_ports()
        self.com_port_combo.addItems(available_ports)
        if available_ports:
            self.com_port_combo.setCurrentIndex(0)
        com_port_layout = QtGui.QHBoxLayout()
        com_port_layout.addWidget(com_port_label)
        com_port_layout.addWidget(self.com_port_combo)
        self.controls_layout.addLayout(com_port_layout)

        # Channels with Gain and Checkbox
        self.channel_checkboxes = []
        self.gain_inputs = []

        for i in range(8):
            channel_layout = QtGui.QHBoxLayout()

            channel_checkbox = QtGui.QCheckBox(f"Channel {i}")
            channel_checkbox.setChecked(False)
            channel_checkbox.stateChanged.connect(
                partial(self.channel_checkbox_changed, i)
            )
            self.channel_checkboxes.append(channel_checkbox)

            gain_label = QtGui.QLabel("Gain:")
            gain_input = QtGui.QLineEdit()
            gain_input.setText("12")
            gain_input.setFixedWidth(50)
            gain_input.returnPressed.connect(partial(self.gain_value_changed, i))
            self.gain_inputs.append(gain_input)

            channel_layout.addWidget(channel_checkbox)
            channel_layout.addWidget(gain_label)
            channel_layout.addWidget(gain_input)
            channel_layout.addStretch()  # Add stretch to push items to the left
            self.controls_layout.addLayout(channel_layout)

        # Connect Buttons
        button_layout = QtGui.QHBoxLayout()
        connect_4_button = QtGui.QPushButton("Connect 4 Channels")
        connect_4_button.clicked.connect(self.connect_4_channels)
        connect_all_button = QtGui.QPushButton("Connect All Channels")
        connect_all_button.clicked.connect(self.connect_all_channels)
        turn_off_all_button = QtGui.QPushButton("Turn Off All")
        turn_off_all_button.clicked.connect(self.turn_off_all_channels)
        button_layout.addWidget(connect_4_button)
        button_layout.addWidget(connect_all_button)
        button_layout.addWidget(turn_off_all_button)
        self.controls_layout.addLayout(button_layout)

        self.controls_layout.addStretch()

    def mode_changed(self, mode):
        self.mode = mode
        if mode == "P300":
            self.ssvep_plot.setTitle("P300 ERP Plot")
            self.ssvep_plot.setLabel("left", "Voltage (µV)")
            self.ssvep_plot.setLabel("bottom", "Time (ms)")
            # Reset P300 epochs
            self.p300_epochs = [[] for _ in range(8)]
        else:
            self.ssvep_plot.setTitle("SSVEP Frequency Spectrum")
            self.ssvep_plot.setLabel("left", "Intensity")
            self.ssvep_plot.setLabel("bottom", "Frequency (Hz)")

    def update(self):
        if self.board_shim is None:
            return  # Do nothing if the board is not connected

        # Get the latest data from the board
        data = self.board_shim.get_current_board_data(self.num_points)

        if data.shape[1] < self.num_points:
            # Not enough data collected yet
            for i in range(8):
                self.curves[i].setData([])
                self.peak_freq_labels[i].setText("Collecting data...")
            return

        if self.mode == "SSVEP":
            self.process_ssvep_data(data)
        elif self.mode == "P300":
            self.process_p300_data(data)

        self.app.processEvents()

    def process_ssvep_data(self, data):
        psd_list = []
        freqs = None
        for i in range(8):  # For channels 0 to 7
            if self.channel_checkboxes[i].isChecked():
                data_index = self.channel_to_data_index.get(i, None)
                if data_index is not None:
                    # Get channel data
                    channel_data = data[data_index]
                    channel_data = np.asarray(
                        channel_data, dtype=np.float64
                    )  # Ensure correct type

                    # Ensure we have enough data
                    if len(channel_data) < 8:
                        # Skip processing if not enough data
                        self.curves[i].setData([])
                        self.peak_freq_labels[i].setText("Collecting data...")
                        continue

                    # Process and plot data
                    DataFilter.detrend(channel_data, DetrendOperations.CONSTANT.value)
                    DataFilter.perform_bandpass(
                        channel_data,
                        int(self.sampling_rate),
                        3.0,
                        45.0,
                        2,
                        FilterTypes.BUTTERWORTH_ZERO_PHASE.value,
                        0,
                    )
                    DataFilter.perform_bandstop(
                        channel_data,
                        int(self.sampling_rate),
                        48.0,
                        52.0,
                        2,
                        FilterTypes.BUTTERWORTH_ZERO_PHASE.value,
                        0,
                    )
                    DataFilter.perform_bandstop(
                        channel_data,
                        int(self.sampling_rate),
                        58.0,
                        62.0,
                        2,
                        FilterTypes.BUTTERWORTH_ZERO_PHASE.value,
                        0,
                    )
                    self.curves[i].setData(channel_data.tolist())

                    nfft = 2 ** int(math.floor(math.log2(len(channel_data))))
                    if nfft < 8:
                        self.peak_freq_labels[i].setText("Collecting data...")
                        continue

                    overlap_samples = nfft // 2  # For 50% overlap

                    psd_data = DataFilter.get_psd_welch(
                        channel_data,
                        nfft=nfft,
                        overlap=overlap_samples,
                        sampling_rate=int(self.sampling_rate),
                        window=WindowFunctions.HAMMING.value,
                    )
                    # Get frequencies and power
                    power = psd_data[0]
                    freqs = psd_data[1]
                    psd_list.append(power)

                    # Find peak frequency in a specified range (e.g., 5-20 Hz)
                    freq_range = (freqs >= 5) & (freqs <= 20)
                    if np.any(freq_range):
                        peak_freq_index = np.argmax(power[freq_range])
                        peak_freq = freqs[freq_range][peak_freq_index]
                        peak_power = power[freq_range][peak_freq_index]

                        # Display peak frequency
                        self.peak_freq_labels[i].setText(
                            f"Peak Freq: {peak_freq:.2f} Hz"
                        )
                    else:
                        self.peak_freq_labels[i].setText("No Peak")
                else:
                    # Data index not available
                    self.curves[i].setData([])
                    self.peak_freq_labels[i].setText("")
            else:
                # Clear the plot and peak frequency for this channel
                self.curves[i].setData([])
                self.peak_freq_labels[i].setText("")

        # Aggregate PSDs and update SSVEP plot
        if psd_list and freqs is not None:
            avg_psd = np.mean(psd_list, axis=0)
            self.ssvep_curve.setData(freqs, avg_psd)
        else:
            # No active channels or no data, clear the SSVEP plot
            self.ssvep_curve.setData([], [])

    def process_p300_data(self, data):
        marker_data = data[self.marker_channel].astype(int)
        # Find indices where marker is set
        event_indices = np.where(marker_data != 0)[0]
        for i, curve in enumerate(self.curves):
            if self.channel_checkboxes[i].isChecked():
                data_index = self.channel_to_data_index.get(i, None)
                if data_index is not None:
                    channel_data = data[data_index]
                    # For each event index, extract an epoch
                    for event_index in event_indices:
                        # Define epoch window around event (e.g., -100ms to 400ms)
                        pre_event_samples = int(0.1 * self.sampling_rate)  # 100ms
                        post_event_samples = int(0.4 * self.sampling_rate)  # 400ms
                        start_idx = event_index - pre_event_samples
                        end_idx = event_index + post_event_samples
                        # Ensure indices are within data range
                        if start_idx >= 0 and end_idx <= len(channel_data):
                            epoch = channel_data[start_idx:end_idx]
                            # Store the epoch for averaging
                            if not hasattr(self, "p300_epochs"):
                                self.p300_epochs = [
                                    [] for _ in range(8)
                                ]  # Assuming 8 channels
                            self.p300_epochs[i].append(epoch)
                else:
                    pass  # Data index not available

        # After collecting enough epochs, average them
        # Let's define a minimum number of epochs
        min_epochs = 10
        for i in range(8):
            if self.channel_checkboxes[i].isChecked() and hasattr(self, "p300_epochs"):
                if len(self.p300_epochs[i]) >= min_epochs:
                    # Average the epochs
                    avg_epoch = np.mean(self.p300_epochs[i], axis=0)
                    # Plot the averaged epoch
                    time_axis = np.linspace(-100, 400, len(avg_epoch))  # Time in ms
                    self.ssvep_curve.setData(time_axis, avg_epoch)
                    self.p300_epochs[i] = []  # Reset epochs after averaging
                else:
                    pass  # Not enough epochs yet
            else:
                pass  # Channel not active or no epochs

    def detect_stimulus(self):
        # Dummy function to demonstrate stimulus detection, replace with real stimulus logic
        return None if np.random.rand() > 0.5 else np.random.randint(100, 500)

    def get_available_com_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def initialize_board(self):
        # Get COM port from the dropdown
        port = self.com_port_combo.currentText()

        # Get enabled channels and gain values
        channels = []
        gain_values = []
        for i, checkbox in enumerate(self.channel_checkboxes):
            if checkbox.isChecked():
                channels.append(i)
                gain_value = int(self.gain_inputs[i].text())
                gain_values.append(gain_value)

        if not channels:
            return  # No channels selected, do not initialize

        # Initialize the board
        self.board_shim = initialize_connection(
            port=port, channels=channels, gain_values=gain_values
        )
        self.board_id = self.board_shim.get_board_id()
        self.eeg_channels = BoardShim.get_exg_channels(self.board_id)
        self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)
        self.num_points = int(self.window_size * self.sampling_rate)

        # Map channel numbers to data indices
        self.channel_to_data_index = {}
        for i in range(8):  # Assuming channels 0-7
            if i < len(self.eeg_channels):
                self.channel_to_data_index[i] = self.eeg_channels[i]
            else:
                self.channel_to_data_index[i] = None

        # Get marker channel index
        self.marker_channel = BoardShim.get_marker_channel(self.board_id)

        # Update the board name label
        self.board_name_label.setText(
            f"Board Name: {BoardShim.get_device_name(self.board_id)}"
        )
        self.connection_status_label.setText("Status: Connected")

        # Start the update loop
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(self.update_speed_ms)

    def channel_checkbox_changed(self, index, state):
        channel = index

        if self.channel_checkboxes[index].isChecked():
            gain_value = int(self.gain_inputs[index].text())

            if self.board_shim is None:
                self.initialize_board()

            # Send command to connect the channel with gain (add 1 to channel index)
            channel_num = channel + 1
            self.board_shim.config_board(f"chon_{channel_num}_{gain_value}")
            print(f"Connected channel {channel_num} with gain {gain_value}")
        else:
            if self.board_shim is not None:
                # Send command to disconnect the channel (add 1 to channel index)
                channel_num = channel + 1
                self.board_shim.config_board(f"choff_{channel_num}")
                print(f"Disconnected channel {channel_num}")

    def gain_value_changed(self, index):
        channel = index

        if self.channel_checkboxes[index].isChecked():
            gain_value = int(self.gain_inputs[index].text())

            if self.board_shim is None:
                self.initialize_board()

            # Update the gain value (add 1 to channel index)
            channel_num = channel + 1
            self.board_shim.config_board(f"chon_{channel_num}_{gain_value}")
            print(f"Updated channel {channel_num} with gain {gain_value}")

    def connect_4_channels(self):
        for i in range(4):
            self.channel_checkboxes[i].setChecked(True)

    def connect_all_channels(self):
        for checkbox in self.channel_checkboxes:
            checkbox.setChecked(True)

    def turn_off_all_channels(self):
        for checkbox in self.channel_checkboxes:
            checkbox.setChecked(False)


def initialize_connection(port, channels, gain_values) -> BoardShim:
    params = BrainFlowInputParams()
    params.serial_port = port

    board_shim = BoardShim(BoardIds.NEUROPAWN_KNIGHT_BOARD.value, params)
    board_shim.prepare_session()
    board_shim.start_stream(450000)

    # Send setup commands to knight board
    for i in range(len(channels)):
        channel_num = channels[i] + 1  # Add 1 to channel index
        board_shim.config_board(f"chon_{channel_num}_{gain_values[i]}")
        print(f"Connected channel {channel_num} with gain {gain_values[i]}")
        time.sleep(0.5)

    return board_shim


def main():
    BoardShim.enable_dev_board_logger()
    logging.basicConfig(level=logging.DEBUG)

    try:
        Graph()
    except BaseException:
        logging.warning("Exception", exc_info=True)
    finally:
        logging.info("End")


if __name__ == "__main__":
    main()
