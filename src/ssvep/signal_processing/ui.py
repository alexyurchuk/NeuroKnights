import sys
import asyncio
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg

class UI:
    def __init__(self, data_queue):
        self.data_queue = data_queue
        self.app = QtWidgets.QApplication(sys.argv)
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.init_ui()

    def init_ui(self):
        self.win = QtWidgets.QWidget()
        self.win.setWindowTitle("BrainFlow Plot")
        self.win.resize(1000, 800)

        self.main_layout = QtWidgets.QHBoxLayout(self.win)
        self.graph_layout_widget = pg.GraphicsLayoutWidget()
        self.main_layout.addWidget(self.graph_layout_widget, stretch=2)

        self.controls_widget = QtWidgets.QWidget()
        self.controls_layout = QtWidgets.QVBoxLayout(self.controls_widget)
        self.controls_layout.setAlignment(QtCore.Qt.AlignTop)
        self.main_layout.addWidget(self.controls_widget, stretch=1)

        self._init_timeseries()
        self._init_controls()

        self.win.show()

    def _init_timeseries(self):
        self.plots = []
        self.curves = []
        self.data = [[] for _ in range(8)]  # Assuming 8 channels maximum
        for i in range(8):
            p = self.graph_layout_widget.addPlot(row=i, col=0)
            if i == 0:
                p.setTitle("TimeSeries Plot")
            self.plots.append(p)
            curve = p.plot()
            self.curves.append(curve)
            p.setYRange(-100, 100)  # Adjust as needed

    def _init_controls(self):
        # Implement controls as needed
        # Add a label to display the predicted command
        self.command_label = QtWidgets.QLabel("Predicted Command: None")
        self.command_label.setStyleSheet("font-size: 16px;")
        self.controls_layout.addWidget(self.command_label)

    def run(self):
        # Start the event loop and the data update coroutine
        self.loop.create_task(self.update())
        self.loop.run_forever()

    async def update(self):
        while True:
            data_item = await self.data_queue.get()
            # Check if the data item contains a command
            if 'command' in data_item:
                command = data_item['command']
                self.display_command(command)
            # Check if the data item contains EEG data
            if 'eeg_data' in data_item:
                eeg_data = data_item['eeg_data']
                # Update the plots with new data
                for i, channel_data in enumerate(eeg_data):
                    if len(self.data[i]) >= 500:
                        self.data[i] = self.data[i][-499:]
                    self.data[i].extend(channel_data)
                    self.curves[i].setData(self.data[i])
            await asyncio.sleep(0.05)  # Adjust as needed

    def display_command(self, command):
        self.command_label.setText(f"Predicted Command: {command}")

    def stop(self):
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.app.quit()
