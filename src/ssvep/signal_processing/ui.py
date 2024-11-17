import sys
import asyncio
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg

class UI(QtWidgets.QWidget):
    # Signal to notify when settings have changed
    settings_changed = QtCore.pyqtSignal()

    def __init__(self, socket_server):
        super().__init__()
        self.data_queue = asyncio.Queue()
        self.socket_server = socket_server  # Store the SocketServer instance
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("BrainFlow Plot")
        self.resize(1200, 1000)

        self.main_layout = QtWidgets.QVBoxLayout(self)

        # Top layout for settings
        self.settings_layout = QtWidgets.QHBoxLayout()
        self.main_layout.addLayout(self.settings_layout)

        self._init_settings()
        self._init_timeseries()
        self._init_controls()

    def _init_settings(self):
        # Implement settings initialization here
        # For the sake of completeness, I'll add minimal settings initialization
        # You can adjust this as per your needs
        # Board 1 Settings
        self.board1_group = QtWidgets.QGroupBox("Board 1 Settings")
        self.board1_layout = QtWidgets.QFormLayout()
        self.board1_group.setLayout(self.board1_layout)

        self.board1_type = QtWidgets.QComboBox()
        self.board1_type.addItems(["Synthetic Board", "NeuroPawn Knight Board"])
        self.board1_type.currentIndexChanged.connect(self.on_board1_type_changed)

        self.board1_port = QtWidgets.QLineEdit()
        self.board1_port.setEnabled(False)  # Disabled by default

        self.board1_layout.addRow("Board Type:", self.board1_type)
        self.board1_layout.addRow("COM Port:", self.board1_port)

        # Board 2 Settings
        self.board2_group = QtWidgets.QGroupBox("Board 2 Settings")
        self.board2_layout = QtWidgets.QFormLayout()
        self.board2_group.setLayout(self.board2_layout)

        self.board2_type = QtWidgets.QComboBox()
        self.board2_type.addItems(["Synthetic Board", "NeuroPawn Knight Board"])
        self.board2_type.currentIndexChanged.connect(self.on_board2_type_changed)

        self.board2_port = QtWidgets.QLineEdit()
        self.board2_port.setEnabled(False)  # Disabled by default

        self.board2_layout.addRow("Board Type:", self.board2_type)
        self.board2_layout.addRow("COM Port:", self.board2_port)

        # Connect Button
        self.connect_button = QtWidgets.QPushButton("Connect")
        self.connect_button.clicked.connect(self.on_connect_clicked)

        # Add to settings layout
        self.settings_layout.addWidget(self.board1_group)
        self.settings_layout.addWidget(self.board2_group)
        self.settings_layout.addWidget(self.connect_button)

    def on_board1_type_changed(self, index):
        board_type = self.board1_type.currentText()
        if board_type == "NeuroPawn Knight Board":
            self.board1_port.setEnabled(True)
        else:
            self.board1_port.setEnabled(False)

    def on_board2_type_changed(self, index):
        board_type = self.board2_type.currentText()
        if board_type == "NeuroPawn Knight Board":
            self.board2_port.setEnabled(True)
        else:
            self.board2_port.setEnabled(False)

    def on_connect_clicked(self):
        # Emit signal that settings have changed
        self.settings_changed.emit()

    def _init_timeseries(self):
        # Initialize the timeseries plots
        self.graph_layout_widget = pg.GraphicsLayoutWidget()
        self.main_layout.addWidget(self.graph_layout_widget)

        self.num_channels = 16  # Total number of channels (8 per board)
        self.plots = []
        self.curves = []
        self.data = [[] for _ in range(self.num_channels)]

        for i in range(self.num_channels):
            p = self.graph_layout_widget.addPlot(row=i, col=0)
            p.showAxis('left', False)
            p.showAxis('bottom', False)
            if i == 0:
                p.setTitle("TimeSeries Plot")
            self.plots.append(p)
            curve = p.plot()
            self.curves.append(curve)
            p.setYRange(-100, 100)  # Adjust as needed

    def _init_controls(self):
        # Add a label to display the predicted command
        self.command_label = QtWidgets.QLabel("Predicted Command: None")
        self.command_label.setStyleSheet("font-size: 16px;")
        self.main_layout.addWidget(self.command_label)

        # Add buttons for commands W, A, S, D, E
        self.buttons_layout = QtWidgets.QHBoxLayout()
        self.main_layout.addLayout(self.buttons_layout)

        self.command_buttons = {}
        commands = ["W", "A", "S", "D", "E"]
        for cmd in commands:
            button = QtWidgets.QPushButton(cmd)
            button.clicked.connect(lambda checked, cmd=cmd: self.send_command(cmd))
            self.buttons_layout.addWidget(button)
            self.command_buttons[cmd] = button

        # Timer to update plots
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plots)
        self.timer.start(50)  # Update plots every 50 ms

    def send_command(self, command):
        """Sends the command via the SocketServer."""
        if self.socket_server and self.socket_server.running:
            self.socket_server.send(command)
        else:
            print("SocketServer is not running or no client connected. Cannot send command.")

    async def update(self):
        while True:
            data_item = await self.data_queue.get()
            # Check if the data item contains a command
            if 'predicted_command' in data_item:
                command = data_item['predicted_command']
                self.display_command(command)
                # Send the command via SocketServer
                self.send_command(command)
            # Check if the data item contains EEG data
            if 'eeg_data' in data_item:
                eeg_data = data_item['eeg_data']
                for i, channel_data in enumerate(eeg_data):
                    # Flatten channel_data if necessary
                    if len(channel_data) > 0 and isinstance(channel_data[0], list):
                        channel_data = [item for sublist in channel_data for item in sublist]
                    if len(self.data[i]) >= 500:
                        self.data[i] = self.data[i][-499:]
                    self.data[i].extend(channel_data)
            await asyncio.sleep(0)  # Yield control to the event loop

    def update_plots(self):
        # Update the plots with the current data
        for i in range(len(self.curves)):
            self.curves[i].setData(self.data[i])

    def display_command(self, command):
        self.command_label.setText(f"Predicted Command: {command}")

    def close(self):
        super().close()
