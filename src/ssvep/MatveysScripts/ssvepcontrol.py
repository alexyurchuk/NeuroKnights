import sys
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget

# Frequency list in Hz
frequencies = [6.66, 7.5, 8.57, 10, 10.91, 12, 13.33, 15, 17.14]
frequencies = [8.0, 10.0, 12.0, 15.0]
frequency_index = 0


class FlashingWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setWindowState(Qt.WindowFullScreen)

        self.current_color = Qt.black
        self.current_frequency = frequencies[frequency_index]

        # Main layout
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignBottom)

        # Frequency display label at the bottom
        self.frequency_label = QLabel(f"{self.current_frequency} Hz", self)
        self.frequency_label.setStyleSheet("color: black; font-size: 48px;")
        self.frequency_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.frequency_label)

        # Set up central widget and layout
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Timer for flashing
        self.timer = QTimer()
        self.timer.timeout.connect(self.toggle_color)
        self.update_timer()

    def update_timer(self):
        # Update label at the bottom of the screen with the current frequency
        self.frequency_label.setText(f"{self.current_frequency} Hz")

        # Update timer interval based on the frequency
        interval = 1000 / (
            self.current_frequency * 2
        )  # 2 toggles per cycle (black to white)
        self.timer.start(interval)

    def toggle_color(self):
        # Toggle between black and white and update frequency display color
        if self.current_color == Qt.black:
            self.current_color = Qt.white
            self.setStyleSheet("background-color: white;")
            self.frequency_label.setStyleSheet("color: black; font-size: 48px;")
        else:
            self.current_color = Qt.black
            self.setStyleSheet("background-color: black;")
            self.frequency_label.setStyleSheet("color: white; font-size: 48px;")

    def keyPressEvent(self, event):
        global frequency_index
        if event.key() == Qt.Key_Space:
            # Move to the next preset frequency and loop back to the start if at the end
            frequency_index = (frequency_index + 1) % len(frequencies)
            self.current_frequency = frequencies[frequency_index]
            self.update_timer()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FlashingWindow()
    window.show()
    sys.exit(app.exec_())
