import signal
import asyncio

from ssvep_analyzer_async import SSVEPAnalyzer
from communicating import SocketServer

from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from functools import partial


# Gracefully stop all other async functions....
def stop(ssvep_analyzer: SSVEPAnalyzer, socket_server: SocketServer, sig, frame):
    print("Stopping the application....")
    socket_server.close_connection()
    ssvep_analyzer.stop()


def config():
    # ================== Communication Setup [BEG] =================================
    socket_server = SocketServer()
    # ================== Communication Setup [END] =================================

    # ================== Communication Start [BEG] =================================
    receive_thread = socket_server.run()
    # ================== Communication Start [END] =================================

    # ================== SSVEPAnalyzer Config [BEG] ================================
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
        board_1,
        frequencies,
        channels,
        channel_names,
        controls=controls,  # TODO add socket_server param
    )
    # ================== SSVEPAnalyzer Config [END] ================================

    # ========== Attach a signal handler for graceful termination [BEG] ============
    signal.signal(signal.SIGINT, partial(stop, ssvep_analyzer, socket_server))
    # ========== Attach a signal handler for graceful termination [END] ============

    return ssvep_analyzer


async def main():
    ssvep_analyzer = config()

    await asyncio.gather(
        ssvep_analyzer.run(),
    )  # add more async funcs or methods here


if __name__ == "__main__":

    # attach a signal handler for graceful termination
    # signal.signal(signal.SIGINT, partial(stop, ssvep_analyzer))

    asyncio.run(main())  # ssvep_analyzer=ssvep_analyzer, socket_server=socket_server
