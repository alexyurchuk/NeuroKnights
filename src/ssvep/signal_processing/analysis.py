# src / ssvep / signal_processing / analysis.py

"""
Summary: 

Implements Frequency-Optimized Canonical Correlation Analysis (FoCCA) for 
SSVEP-based classification, focusing on determining which flickering frequency 
a user is attending to based on their EEG data.

Author(s): Alex Yurchuk, Ivan Costa Neto
Commenter(s): Ivan Costa Neto
Last Updated: Nov. 15, 2024
"""

import numpy as np

# Canonical Correlation Analysis (CCA) implementation from the scikit-learn library 
# finds linear relationships b/w two datasets by projecting them into a shared space where the correlation is maximized
from sklearn.cross_decomposition import CCA

# class: Frequency-Optimized Canonical Correlation Analysis with K-Nearest Neighbors
class FoCAA_KNN:

    # initializes the FoCAA-KNN model for SSVEP classification
    def __init__(self, n_components: int, frequencies: list, sampling_rate: int, cca_buffer_size: int,) -> None:
        """
        Args:
            n_components (int): Number of canonical components to compute for CCA.
            frequencies (list): List of target frequencies (Hz) for SSVEP detection.
            sampling_rate (int): Sampling rate of EEG data (Hz).
            cca_buffer_size (int): Length of EEG data buffer (number of samples).
        """
        self.n_components = n_components
        self.sampling_rate = sampling_rate
        self.cca_buffer_size = cca_buffer_size

         # generate reference signals for each frequency
        self.reference_signals = []  # list to store reference signals

        # iterates through every frequency
        for frequency in frequencies:
             # generate sine/cosine signals for the given frequency
            self.reference_signals.append(
                self.get_reference_signals(cca_buffer_size, frequency)
            )

        self.reference_signals = np.array(self.reference_signals)  # converts to ndarray
        # print("init: ", self.reference_signals.shape)


    # gets reference signals (sine/cosine waves) for the given target frequency
    def get_reference_signals(self, length, target_freq) -> np.ndarray:
        """
        Only signals with first (fundamental) and second harmonics of each of the frequencies.

        Args:
            length (int): length of data needed -> # of samples
            target_freq (float): target frequency

        Returns:
            reference_signals (np.ndarray): array of reference signals including harmonics (shape: [4, length])
        """
        reference_signals = []  # list to store individual reference signals
        # create a time vector from 0 --> duration of signal
        t = np.arange(
            0, (length / (self.sampling_rate)), step=(1.0 / (self.sampling_rate))
        )
        # print(t)

        # first (fundamental) frequency components
        reference_signals.append(np.sin(2 * np.pi * target_freq * t))  # sine wave
        reference_signals.append(np.cos(2 * np.pi * target_freq * t))  # cosine wave

        # second frequency components (x2 target frequency)
        reference_signals.append(np.sin(4 * np.pi * target_freq * t))  # sine wave
        reference_signals.append(np.cos(4 * np.pi * target_freq * t))  # cosine wave

        reference_signals = np.array(reference_signals)

        # return a numpy array of shape (4, length)
        return reference_signals


    # computes canonical correlations using CCA for each reference signal
    def sk_findCorr(self, n_components: int, data: np.ndarray) -> np.ndarray:
        """
        Args:
            n_components (int): number of canonical components to compute
            data (np.ndarray): consists of the EEG, rows -> data, columns -> channels

        Returns:
            result (np.ndarray): array of maximum canonical correlations for each frequency
        """
        # print("data: ", data.shape)

        cca = CCA(n_components)  # initialize cca
        corr = np.zeros(n_components)  # stores correlations for each component
        result = np.zeros((self.reference_signals.shape)[0])  # correlations for each frequency

        # iterates through each reference signal (one per frequency)
        for freqIdx in range(0, (self.reference_signals.shape)[0]):
            # print(
            #     f"ref_{freqIdx}:",
            #     np.squeeze(self.reference_signals[freqIdx, :, :]).T.shape,
            # )
            # print(np.squeeze(freq[freqIdx, :, :]).T)

            ref_signal = np.squeeze(self.reference_signals[freqIdx, :, :]).T  # extract reference signals
            cca.fit(data, ref_signal)  # fit EEG data and reference signals
            O1_a, O1_b = cca.transform(data, ref_signal)  # transforms datasets into canonical space

            # compute correlations for each canonical component
            for indVal in range(n_components):
                corr[indVal] = np.corrcoef(O1_a[:, indVal], O1_b[:, indVal])[0, 1]
                # print(np.corrcoef(O1_a[:, indVal], O1_b[:, indVal]))
            result[freqIdx] = np.max(corr)  # maximum correlation for the frequency

        # print(result)

        return result  # return correlations for all frequencies


    # performs CCA-based analysis for SSVEP classification
    def cca_analysis(self, data: np.ndarray):
        """
        Args:
            data (np.ndarray): EEG data (shape: [# of samples, # of channels]).

        Returns:
            np.ndarray: Canonical correlation coefficients for each frequency.
        """
        # combine the data and reference data based on their dimensionality
        result = []  # will store the canonical correlation coefficients for all frequencies

        for freqIdx in range(self.reference_signals.shape[0]):
            data_ref = np.squeeze(self.reference_signals[freqIdx, :, :]).T  # extract reference signals
            
            # combine EEG data and reference signals for covariance computation
            xy = (
                np.concatenate((data, data_ref), axis=1)
                if data.shape[1] <= data_ref.shape[1]
                else np.concatenate((data_ref, data), axis=1)
            )

            # calculate covariance matrices
            covariance = np.cov(xy, rowvar=False)
            n = min(data.shape[1], data_ref.shape[1])  # minimum dimension (channels vs. references)
            cx = covariance[:n, :n]  # covariance of EEG data
            cy = covariance[n:, n:]  # covariance of reference signals
            cxy = covariance[:n, n:]  # cross-covariance
            cyx = covariance[n:, :n]  # transposed cross-covariance

           # solve for canonical correlations using eigenvalue decomposition
            eps = np.finfo(float).eps  # small value to prevent singular matrices
            try:
                corr_coef = (
                    np.linalg.inv(cy + eps * np.eye(cy.shape[0]))
                    @ cyx
                    @ np.linalg.inv(cx + eps * np.eye(cx.shape[0]))
                    @ cxy
                )
            except Exception as e:
                print(f"Exception was triggered. Values: cx={cx}")
                print("full thing: ", cx + eps * np.eye(cx.shape[0]))
                raise e

            # eigenvalue decomposition and sorting
            eig_vals = np.linalg.eigvals(corr_coef)

            # compute eigenvalues and canonical correlations
            eig_vals = np.linalg.eigvals(corr_coef)  # Solve for eigenvalues
            eig_vals[eig_vals < 0] = 0  # Set small negative values to zero
            d_coeff = np.sqrt(np.sort(np.real(eig_vals))[::-1])  # Square root of eigenvalues

            result.append(d_coeff[:n])  # append top canonical correlations for this frequency

        result = np.array(result)

        return result  # return results for all frequencies
    
        # return d_coeff[:n]  # Return the canonical correlations
