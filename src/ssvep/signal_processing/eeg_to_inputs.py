# src / ssvep / signal_processing / eeg_to_inputs.py

"""
Summary:

Maps real-time EEG classifications to WASD keypresses for controlling the chess game.

Author(s): Ivan Costa Neto
Commenter(s): Ivan Costa Neto
Last Updated: Nov. 16, 2024
"""

from ssvep.signal_processing.ssvep_analyzer import analyze_eeg_and_control, setup_board  # import functions from svvep_analyzer.py
from pynput.keyboard import Controller  # keyboard mapping 

# mapping and simulation functions
keyboard = Controller()

# map the classification integer to a corresponding WASD action
def map_classification_to_action(classification):
  """
    Args:
        classification (int): classification result (0 for W, 1 for A, etc.)
    Returns:
        action_map.get() (str): ('W', 'A', 'S', 'D') or None if classification is invalid
    """
    action_map = {
        0: 'W',  # forward
        1: 'A',  # left
        2: 'S',  # down
        3: 'D'   # right
    }
    return action_map.get(classification, None)


# simulates a keypress based on the mapped action using the pynput library
def simulate_keypress(action):
    """
    Args:
        action (str): the action that simulates ('W', 'A', 'S', 'D')
    """
    if action:
        print(f"Simulating keypress: {action}")  # debugging
        keyboard.press(action)  # simulate key
        keyboard.release(action)  # key release 

# extend the real-time control logic
def eeg_to_wasd_control(board, sampling_rate, window_size):
    """
    Args:
        board: EEG board instance
        sampling_rate (int): in Hz
        window_size (int): for classification in samples
    """
    while True:
        # get classified action
        classification_result = analyze_eeg_and_control(board, sampling_rate, window_size)

        # map to a specific action and simulate
        action = map_classification_to_action(classification_result)
        simulate_keypress(action)

if __name__ == "__main__":
    # EEG setup
    sampling_rate = 250  # update computer
    window_size = sampling_rate * 2  # 2 sec data window

    try:
        # initialize the EEG board
        board = setup_board()

        # start the EEG-to-WASD control loop
        eeg_to_wasd_control(board, sampling_rate, window_size)
    finally:
        # ensure the EEG board stream is stopped and resources are released
        print("Stopping EEG stream and releasing resources...")
        board.stop_stream()
        board.release_session()
