import logging
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore
from functools import partial


class Graph:
    def __init__(self):
        self.update_speed_ms = 50
        self.window_size = 4

        self.app = QtWidgets.QApplication([])
        self.win = QtWidgets.QWidget()
        self.win.setWindowTitle("BrainFlow Plot")
        self.win.resize(1000, 800)

        self.init_ui()
        self.win.show()

        self.app.exec()

    def init_ui(self):
        self.main_layout = QtWidgets.QHBoxLayout(self.win)
        self.graph_layout_widget = pg.GraphicsLayoutWidget()
        self.main_layout.addWidget(self.graph_layout_widget, stretch=2)

        self.controls_widget = QtWidgets.QWidget()
        self.controls_layout = QtWidgets.QVBoxLayout(self.controls_widget)
        self.controls_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.main_layout.addWidget(self.controls_widget, stretch=1)

        self._init_timeseries()
        self._init_controls()

    def _init_timeseries(self):
        self.plots = []
        self.curves = []
        for i in range(8):  # Assuming 8 channels maximum
            p = self.graph_layout_widget.addPlot(row=i, col=0)
            if i == 0:
                p.setTitle("TimeSeries Plot")
            self.plots.append(p)
            curve = p.plot()
            self.curves.append(curve)

    def _init_controls(self):
        # Channels with Gain and Checkbox
        self.channel_checkboxes = []
        self.gain_inputs = []

        for i in range(8):
            channel_layout = QtWidgets.QHBoxLayout()

            channel_checkbox = QtWidgets.QCheckBox(f"Channel {i}")
            channel_checkbox.setChecked(False)
            channel_checkbox.stateChanged.connect(
                partial(self.channel_checkbox_changed, i)
            )
            self.channel_checkboxes.append(channel_checkbox)

            gain_label = QtWidgets.QLabel("Gain:")
            gain_input = QtWidgets.QLineEdit()
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
        button_layout = QtWidgets.QHBoxLayout()
        connect_4_button = QtWidgets.QPushButton("Connect 4 Channels")
        connect_4_button.clicked.connect(self.connect_4_channels)
        connect_all_button = QtWidgets.QPushButton("Connect All Channels")
        connect_all_button.clicked.connect(self.connect_all_channels)
        turn_off_all_button = QtWidgets.QPushButton("Turn Off All")
        turn_off_all_button.clicked.connect(self.turn_off_all_channels)
        button_layout.addWidget(connect_4_button)
        button_layout.addWidget(connect_all_button)
        button_layout.addWidget(turn_off_all_button)
        self.controls_layout.addLayout(button_layout)

        self.controls_layout.addStretch()

    def update(self):
        pass  # Currently, no data updates are performed

    def channel_checkbox_changed(self, index, state):
        pass  # Placeholder for future functionality

    def gain_value_changed(self, index):
        pass  # Placeholder for future functionality

    def connect_4_channels(self):
        for i in range(4):
            self.channel_checkboxes[i].setChecked(True)

    def connect_all_channels(self):
        for checkbox in self.channel_checkboxes:
            checkbox.setChecked(True)

    def turn_off_all_channels(self):
        for checkbox in self.channel_checkboxes:
            checkbox.setChecked(False)


def main():
    logging.basicConfig(level=logging.DEBUG)

    try:
        Graph()
    except BaseException:
        logging.warning("Exception", exc_info=True)
    finally:
        logging.info("End")


if __name__ == "__main__":
    main()
