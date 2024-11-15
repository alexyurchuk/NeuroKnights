# src / ssvep / signal_processing / recording.py

"""
Summary:

Provides utilities for recording EEG and analysis-related data into CSV files. 
It ensures data is logged in an organized and structured format, 
with unique filenames and clear headers.

Author(s): Alex Yurchuk
Commenter(s): Ivan Costa Neto
Last Updated: Nov. 15, 2024
"""


import csv
import _csv  # internal CSV module used to type the writer
from typing import IO  # for type hinting file objects
import numpy as np
from datetime import datetime

# import pandas as pd 


# initializes a CSV writer for recording data
def initialize_writer(
    file_name: str,
    header: str,
    mode: str = "w",
) -> tuple["_csv._writer", IO]:
    """
    Args:
        file_name (str): base name of the file (without extension)
        header (str): list of column names for the CSV file
        mode (str, optional): file write mode

    Returns:
        writer, csv_file (tuple["_csv._writer", IO]): a tuple containing the CSV writer object and the file object
    """
    # timestamp to the file name for uniqueness
    file_name = file_name + "_" + datetime.now().strftime(r"%Y%m%d-%H%M") + ".csv"
    # open the file in the specified mode ('w' for overwrite)
    csv_file = open(file_name, mode=mode, newline="")
    # create a CSV writer object
    writer = csv.writer(csv_file)
    # write the header row to the CSV
    writer.writerow(header)
    return writer, csv_file


# safely closes the CSV file when writing is complete to ensure data is written
def uninitialize_writer(csv_file) -> None:
    """
    Args:
        csv_file (IO): the file object to close
    """
    csv_file.close()


# records EEG data to a CSV file
def record_eeg_data(writer: "_csv._writer", data: np.ndarray) -> None:
    """
    Args:
        writer (_csv._writer): CSV writer object to write data.
        data (np.ndarray): EEG data array (channels x samples).
    """
    # ensures data is correctly oriented for writing
    record_data(writer=writer, data=data)


# records Canonical Correlation Analysis (CCA) coefficients with additional metadata.
def record_cca_data(
    writer: "_csv._writer",
    cca_coefs: np.ndarray,
    stimuli: bool,
    frequency: float,
    time,
) -> None:
    """
    Args:
        writer (_csv._writer): CSV writer object to write data.
        cca_coefs (np.ndarray): Array of CCA coefficients.
        stimuli (bool): Whether the stimuli are active.
        frequency (float): Target frequency of the stimuli.
        time: Timestamp of the recorded data.
    """
    # appends the metadata (stimuli state, frequency, timestamp) to the CCA coefficients
    data = np.append(cca_coefs, [stimuli, frequency, time])
    writer.writerow(data)  # write a single row of data


# writes multiple rows of data to the CSV
def record_data(writer: "_csv._writer", data: np.ndarray) -> None:
    """
    Args:
        writer (_csv._writer): CSV writer object to write data.
        data (np.ndarray): Data to be written (rows x columns).
    """
    writer.writerows(data)  # write multiple rows to the CSV


"""
Below are alternative versions of the above functions using pandas (commented out).
These functions are unused but show an alternate approach for recording data.
"""

# def record_eeg_data(data: np.ndarray, file_name: str, mode: str = "a") -> None:
#     data = data.T if data.shape[0] < data.shape[1] else data
#     record_data(data=data, file_name=file_name, mode=mode)

# def record_cca_data(
#     cca_coefs: np.ndarray, stimuly: bool, file_name: str, mode: str = "a"
# ) -> None:
#     data = np.append(cca_coefs, stimuly)
#     record_data(data=data, file_name=file_name, mode=mode)

# def record_data(data: np.ndarray, file_name: str, mode: str = "a") -> None:
#     df = pd.DataFrame(data)
#     df.to_csv(path_or_buf=file_name, index=False, mode=mode)
