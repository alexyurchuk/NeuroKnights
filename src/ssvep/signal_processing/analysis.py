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

from scipy import signal


# class: Frequency-Optimized Canonical Correlation Analysis with K-Nearest Neighbors
class FoCAA_KNN:

    # initializes the FoCAA-KNN model for SSVEP classification
    def __init__(
        self,
        n_components: int,
        frequencies: list,
        sampling_rate: int,
        cca_buffer_size: int,
    ) -> None:
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
        result = np.zeros(
            (self.reference_signals.shape)[0]
        )  # correlations for each frequency

        # iterates through each reference signal (one per frequency)
        for freqIdx in range(0, (self.reference_signals.shape)[0]):
            # print(
            #     f"ref_{freqIdx}:",
            #     np.squeeze(self.reference_signals[freqIdx, :, :]).T.shape,
            # )
            # print(np.squeeze(freq[freqIdx, :, :]).T)

            ref_signal = np.squeeze(
                self.reference_signals[freqIdx, :, :]
            ).T  # extract reference signals
            cca.fit(data, ref_signal)  # fit EEG data and reference signals
            O1_a, O1_b = cca.transform(
                data, ref_signal
            )  # transforms datasets into canonical space

            # compute correlations for each canonical component
            for indVal in range(n_components):
                corr[indVal] = np.corrcoef(O1_a[:, indVal], O1_b[:, indVal])[0, 1]
                # print(np.corrcoef(O1_a[:, indVal], O1_b[:, indVal]))
            result[freqIdx] = np.max(corr)  # maximum correlation for the frequency

        # print(result)
        return result

    # ============================================================================================================

    def cca_analysis_beta(self, Xa: np.ndarray, Xb: np.ndarray):
        """
        Fits CCA parameters using the standard eigenvalue problem.

        :param Xa: Observations with shape (n_samps, p_dim).
        :param Xb: Observations with shape (n_samps, q_dim).
        :return:   Linear transformations Wa and Wb.
        """
        inv = np.linalg.inv
        mm = np.matmul

        N, p = Xa.shape
        N, q = Xb.shape
        r = min(p, q)

        Xa -= Xa.mean(axis=0)
        Xa /= Xa.std(axis=0)
        Xb -= Xb.mean(axis=0)
        Xb /= Xb.std(axis=0)

        p = Xa.shape[1]
        C = np.cov(Xa.T, Xb.T)
        Caa = C[:p, :p]
        Cbb = C[p:, p:]
        Cab = C[:p, p:]
        Cba = C[p:, :p]

        # Either branch results in: r x r matrix where r = min(p, q).
        if q < p:
            M = mm(mm(inv(Cbb), Cba), mm(inv(Caa), Cab))
        else:
            M = mm(mm(inv(Caa), Cab), mm(inv(Cbb), Cba))

        # Solving the characteristic equation,
        #
        #     det(M - rho^2 I) = 0
        #
        # is equivalent to solving for rho^2, which are the eigenvalues of the
        # matrix.
        eigvals, eigvecs = np.linalg.eig(M)
        rhos = np.sqrt(eigvals)

        # Ensure we go through eigenvectors in descending order.
        inds = (-rhos).argsort()
        rhos = rhos[inds]
        eigvals = eigvals[inds]
        # NumPy returns each eigenvector as a column in a matrix.
        eigvecs = eigvecs.T[inds].T
        Wb = eigvecs

        Wa = np.zeros((p, r))
        for i, (rho, wb_i) in enumerate(zip(rhos, Wb.T)):
            wa_i = mm(mm(inv(Caa), Cab), wb_i) / rho
            Wa[:, i] = wa_i

        # Sanity check: canonical correlations are equal to the rhos.
        Za = np.linalg.norm(mm(Xa, Wa), 2, axis=0)
        Zb = np.linalg.norm(mm(Xb, Wb), 2, axis=0)
        print("=" * 100)
        print("Canonical correlations (Za): ", Za)
        print("Canonical correlations (Zb): ", Zb)
        print("=" * 100)
        CCs = np.zeros(r)

        for i in range(r):
            za = Za[:, i]
            zb = Zb[:, i]
            CCs[i] = np.dot(za, zb)
        assert np.allclose(CCs, rhos)

        return Wa, Wb

    # ============================================================================================================

    def focca_analysis(self, data: np.ndarray, a: list, b: list):
        num_harmonic = 2

        k = np.arange(
            1, min(data.shape[1], num_harmonic * 2) + 1, dtype=float
        )  # Create the array k

        coeff = np.zeros(self.reference_signals.shape[0])
        print("+" * 100)
        for val_a in a:
            for val_b in b:
                phi = np.power(k, -val_a) + val_b  # Compute phi

                # for i in range(data.shape[-1]):  # Loop through all Trials
                for ind in range(
                    self.reference_signals.shape[0]
                ):  # Calculate CCA for frequencies stimulation
                    cano_corr = self.cca_analysis(
                        data,
                        data_ref=np.squeeze(self.reference_signals[ind, :, :]).T,
                    )
                    coeff[ind] = np.sum(
                        phi * (cano_corr**2), axis=0
                    )  # Calculate the coefficient coeff(L)

                print(f"val_a = {val_a}, val_b = {val_b} --> {coeff}")

                # predict_label[i] = np.argmax(
                #     coeff
                # )  # Predict label for the current trial
        print("+" * 100)
        return coeff

    def fbcca_analysis(
        self,
        data: np.ndarray,
        a: list,
        b: list,
        filter_banks,
        order,
        notch_freq,
        quality_factor,
        filter_active,
        notch_filter,
        type_filter,
    ):
        num_harmonic = 2

        k = np.arange(
            1, np.array(filter_banks).shape[-1] + 1, dtype=float
        )  # Create the array k

        # coeff = np.zeros(self.reference_signals.shape[0])
        coeff = np.zeros((len([*filter_banks][0]), self.reference_signals.shape[0]))
        # print("+" * 100)
        labels = []

        for val_a in a:
            for val_b in b:
                phi = np.power(k, -val_a) + val_b  # Compute phi

                # for i in range(data.shape[-1]):  # Loop through all Trials
                for ind_sb, (val_sb1, val_sb2) in enumerate(zip(*filter_banks)):
                    data_sub_banks = self.filtering(
                        data,
                        val_sb1,
                        val_sb2,
                        order,
                        self.sampling_rate,
                        notch_freq,
                        quality_factor,
                        filter_active,
                        notch_filter,
                        type_filter,
                    )
                    for ind_fstim in range(
                        self.reference_signals.shape[0]
                    ):  # Calculate CCA for frequencies stimulation
                        cano_corr = self.cca_analysis(
                            data_sub_banks,
                            data_ref=np.squeeze(
                                self.reference_signals[ind_fstim, :, :]
                            ).T,
                        )
                        # Calculate the coefficient coeff(L)
                        coeff[ind_sb, ind_fstim] = np.max(cano_corr)

                    label = np.argmax(np.sum(phi * (coeff**2).T, axis=1))
                    c = np.sum(phi * (coeff**2).T, axis=1)
                    labels.append(label)
                # print(f"val_a = {val_a}, val_b = {val_b} --> {coeff}")

                # predict_label[i] = np.argmax(
                #     coeff
                # )  # Predict label for the current trial
        # print("+" * 100)
        labels = np.array(labels)
        label = np.bincount(labels).argmax()
        return c, label

    # performs CCA-based analysis for SSVEP classification
    def cca_analysis(self, data: np.ndarray, data_ref: np.ndarray):
        """
        Args:
            data (np.ndarray): EEG data (shape: [# of samples, # of channels]).

        Returns:
            np.ndarray: Canonical correlation coefficients for each frequency.
        """
        # combine the data and reference data based on their dimensionality
        # result = (
        #     []
        # )  # will store the canonical correlation coefficients for all frequencies

        # for freqIdx in range(self.reference_signals.shape[0]):
        # data_ref = np.squeeze(
        #     self.reference_signals[freqIdx, :, :]
        # ).T  # extract reference signals

        # combine EEG data and reference signals for covariance computation
        xy = (
            np.concatenate((data, data_ref), axis=1)
            if data.shape[1] <= data_ref.shape[1]
            else np.concatenate((data_ref, data), axis=1)
        )

        # calculate covariance matrices
        covariance = np.cov(xy, rowvar=False)

        n = min(
            data.shape[1], data_ref.shape[1]
        )  # minimum dimension (channels vs. references)
        cx = covariance[:n, :n]  # covariance of EEG data
        cy = covariance[n:, n:]  # covariance of reference signals
        cxy = covariance[:n, n:]  # cross-covariance
        cyx = covariance[n:, :n]  # transposed cross-covariance

        # Solve the optimization problem using eigenvalue decomposition
        eps = np.finfo(np.float32).eps  # small value to prevent singular matrices
        # try:
        if np.linalg.det(cx) != 0 and np.linalg.det(cy) != 0:
            cx_inv = np.linalg.inv(cx)
            cy_inv = np.linalg.inv(cy)
        else:
            # print("Taking changed version of cx and cy...")
            coef = 10 ** (-5)
            cx_inv = np.linalg.inv(cx + coef * eps * np.eye(cx.shape[0]))
            cy_inv = np.linalg.inv(cy + coef * eps * np.eye(cy.shape[0]))
        corr_coef = cy_inv @ cyx @ cx_inv @ cxy
        # except Exception as e:
        #     print("*" * 100)
        #     print(f"Exception was triggered. Values:\n cx = {cx}")
        #     print("full thing: \n", cx + eps * np.eye(cx.shape[0]))
        #     print("Dtype cx: ", cx.dtype)
        #     print("Dtype cy: ", cy.dtype)
        #     print(
        #         "Determinant of original cx: ",
        #         np.linalg.det(cx),
        #     )
        #     print(
        #         "Determinant of updated cx: ",
        #         np.linalg.det(cx + coef * eps * np.eye(cx.shape[0])),
        #     )
        #     print("*" * 100)
        #     raise e

        # eigenvalue decomposition and sorting
        eig_vals = np.linalg.eigvals(corr_coef)

        # compute eigenvalues and canonical correlations
        eig_vals = np.linalg.eigvals(corr_coef)  # solve for eigenvalues
        eig_vals[eig_vals < 0] = 0  # set small negative values to zero
        d_coeff = np.sqrt(
            np.sort(np.real(eig_vals))[::-1]
        )  # square root of eigenvalues

        # result.append(
        #     d_coeff[:n]
        # )  # append top canonical correlations for this frequency

        # result = np.array(result)

        return d_coeff[:n]  # return results for all frequencies

        # return d_coeff[:n]  # Return the canonical correlations

    # ============================================= Filtering ====================================================
    # Function to apply digital filtering to data
    def filtering(
        self,
        data,
        f_low,
        f_high,
        order,
        fs,
        notch_freq,
        quality_factor,
        filter_active="on",
        notch_filter="on",
        type_filter="bandpass",
    ):
        """
        FILTERING applies digital filtering to data.
        Inputs:
        - data: Input data to be filtered.
        - f_low: Low cutoff frequency.
        - f_high: High cutoff frequency.
        - order: Filter order.
        - fs: Sampling frequency.
        - notch_freq: Frequency to be notched out.
        - filter_active: Activate filtering ('on' or 'off').
        - notch_filter: Activate notch filtering ('on' or 'off').
        - type_filter: Type of filter ('low', 'high', 'bandpass', 'stop').
        Output:
        - filtered_data: Filtered data.
        ================================= Flowchart for the filtering function ===================================
        Start
        1. Normalize frequency values (f_low, f_high)
        2. Check the dimensions of the input data:
            a. If it's a 3D matrix and has more rows than columns:
            - Transpose the data using permute to make channels as slices
            b. If it has more columns than rows:
            - Transpose the data to make channels as rows
        3. Design Butterworth filter based on the specified type:
            - Lowpass filter: Design Butterworth filter with 'low' option
            - Highpass filter: Design Butterworth filter with 'high' option
            - Bandpass filter: Design Butterworth filter with 'bandpass' option
            - Bandstop filter: Design Butterworth filter with 'bandstop' option
        4. Design a notch filter:
            - Use iirnotch to design a notch filter based on notch frequency and quality factor
        5. Notch filter:
            - Apply notch filtering if notch_filter is 'on'
        6. Apply the digital filter using filtfilt:
            - Apply filtering if filter_active is 'on'
        7. Output the filtered data (filtered_data)
        End
        ==========================================================================================================
        """
        # ---------------------------------------- Normalize frequency values ------------------------------------
        f_low = f_low / (fs / 2)
        f_high = f_high / (fs / 2)

        filtered_data = data.copy()  # Make a copy of the input data
        # ---------------------------- Convert data to ndarray if it's not already -------------------------------
        filtered_data = (
            np.array(filtered_data)
            if not isinstance(filtered_data, np.ndarray)
            else filtered_data
        )
        # ----------------------- Transpose data if it has more rows than columns --------------------------------
        filtered_data = (
            filtered_data.T
            if filtered_data.ndim > 1
            and filtered_data.shape[0] > filtered_data.shape[-1]
            else filtered_data
        )
        # ----------------------- Design Butterworth filter based on the specified type --------------------------
        if type_filter == "low":
            b, a = signal.butter(order, f_low, btype="low")
        elif type_filter == "high":
            b, a = signal.butter(order, f_high, btype="high")
        elif type_filter == "bandpass":
            b, a = signal.butter(order, [f_low, f_high], btype="bandpass")
        elif type_filter == "bandstop":
            b, a = signal.butter(order, [f_low, f_high], btype="bandstop")

        # Design a notch filter using signal.iirnotch
        # b_notch, a_notch = signal.butter(3, np.array([notch_freq - 0.4, notch_freq + 0.4])/fs/2, btype='bandstop')
        b_notch, a_notch = signal.iirnotch(notch_freq, quality_factor, fs)
        # -------------------------------------------- Notch filter ----------------------------------------------
        if notch_filter == "on":
            if filtered_data.ndim == 3:
                for i in range(filtered_data.shape[0]):
                    filtered_data[i, :, :] = signal.filtfilt(
                        b_notch, a_notch, filtered_data[i, :, :]
                    )
            else:
                filtered_data = signal.filtfilt(b_notch, a_notch, filtered_data)
        # ---------------- Apply the digital filter using filtfilt to avoid phase distortion --------------------
        if filter_active == "on":
            if filtered_data.ndim == 3:
                for i in range(filtered_data.shape[0]):
                    filtered_data[i, :, :] = signal.filtfilt(
                        b, a, filtered_data[i, :, :]
                    )
            else:
                filtered_data = signal.filtfilt(b, a, filtered_data)
        # ----------------------------- Transpose data if it has more columns than rows --------------------------------
        filtered_data = (
            filtered_data.T
            if filtered_data.ndim > 1
            and filtered_data.shape[0] < filtered_data.shape[-1]
            else filtered_data
        )

        return filtered_data
