import signal
import asyncio
from functools import partial

from ssvep_analyzer_async import SSVEPAnalyzer
from communications import SocketServer
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds

from PyQt5 import QtWidgets
from qasync import QEventLoop  # Import QEventLoop for integrating PyQt and asyncio
from ui import UI

# Gracefully stop all other async functions
def stop(ssvep_analyzer: SSVEPAnalyzer, socket_server: SocketServer, sig, frame):
    print("Stopping the application....")
    socket_server.close_connection()
    ssvep_analyzer.stop()

def main():
    # Communication Setup
    socket_server = SocketServer()

    # Define target SSVEP frequencies
    frequencies = [6.66, 7.5, 8.57, 10, 12, 15]
    controls = ["W", "A", "S", "D", "Q", "E"]

    # Enable BrainFlow debug logging
    BoardShim.enable_dev_board_logger()

    # Initialize the UI
    app = QtWidgets.QApplication([])
    ui = UI()
    ui.init_ui()
    ui.show()

    # Create an instance of SSVEPAnalyzer
    ssvep_analyzer = SSVEPAnalyzer(
        frequencies=frequencies,
        controls=controls,
        socket_server=socket_server,
        ui=ui  # Pass the UI instance to the analyzer
    )

    # Attach a signal handler for graceful termination
    signal.signal(signal.SIGINT, partial(stop, ssvep_analyzer, socket_server))

    # Integrate the PyQt event loop with asyncio
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    try:
        with loop:
            # Schedule the SSVEPAnalyzer run method and UI update method
            asyncio.ensure_future(ssvep_analyzer.run())
            asyncio.ensure_future(ui.update())
            loop.run_forever()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
