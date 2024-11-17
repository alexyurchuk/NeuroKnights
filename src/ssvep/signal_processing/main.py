import signal
import asyncio

from ssvep_analyzer_async import SSVEPAnalyzer

from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from functools import partial


# def configure_ssvep_analizer():


def stop(ssvep_analyzer: SSVEPAnalyzer, sig, frame):
    print("Stopping the application....")
    ssvep_analyzer.stop()
    # Gracefully stop all other async functions....


async def main(ssvep_analyzer: SSVEPAnalyzer):
    await asyncio.gather(
        ssvep_analyzer.run(),
    )  # add more async funcs or methods here


if __name__ == "__main__":
    # ================== SSVEPAnalyzer Config ================================
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
        board_1, frequencies, channels, channel_names, controls=controls
    )
    # ================== SSVEPAnalyzer Config ================================

    # attach a signal handler for graceful termination
    signal.signal(signal.SIGINT, partial(stop, ssvep_analyzer))

    asyncio.run(main(ssvep_analyzer=ssvep_analyzer))
