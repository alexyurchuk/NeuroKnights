import csv
import _csv
from typing import IO
import numpy as np

from datetime import datetime

# import pandas as pd


def initialize_writer(
    file_name: str,
    header: str,
    mode: str = "w",
) -> tuple[_csv._writer, IO]:
    """_summary_

    _extended_summary_

    Args:
        file_name (str): file name only, without file extention
        mode (str, optional): _description_. Defaults to "a".
    """
    file_name = file_name + "_" + datetime.strftime(r"%Y%m%d-%H%M") + ".csv"
    csv_file = open(file_name, mode=mode, newline="")
    writer = csv.writer(csv_file)
    writer.writerow(header)
    return writer, csv_file


def uninitialize_writer(csv_file) -> None:
    csv_file.close()


def record_eeg_data(writer: _csv._writer, data: np.ndarray) -> None:
    data = data.T if data.shape[0] < data.shape[1] else data
    record_data(writer=writer, data=data)


def record_cca_data(
    writer: _csv._writer,
    cca_coefs: np.ndarray,
    stimuly: bool,
    time,
) -> None:
    data = np.append(cca_coefs, [stimuly, time])
    record_data(writer=writer, data=data)


def record_data(writer: _csv._writer, data: np.ndarray) -> None:
    writer.writerows(data)


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
