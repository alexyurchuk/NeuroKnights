import numpy as np

from sklearn.cross_decomposition import CCA


class FoCAA_KNN:
    def __init__(
        self,
        n_components: int,
        frequencies: list,
        sampling_rate: int,
        cca_buffer_size: int,
    ) -> None:
        """Implementation of FoCAA-KNN

        _extended_summary_

        Args:
            n_components (int): _description_
            frequencies (list): _description_
            sampling_rate (int): _description_
            cca_buffer_size (int): _description_
        """
        self.n_components = n_components
        self.sampling_rate = sampling_rate
        self.cca_buffer_size = cca_buffer_size
        self.reference_signals = []
        for frequency in frequencies:
            self.reference_signals.append(
                self.get_reference_signals(cca_buffer_size, frequency)
            )
        self.reference_signals = np.array(self.reference_signals)
        # print("init: ", self.reference_signals.shape)

    def get_reference_signals(self, length, target_freq) -> np.ndarray:
        """Get reference signals

        Only signals with first and second harmonics of each of the frequencies.

        Args:
            length (int): length of data needed -> # of samples
            target_freq (float): target frequency
        """

        reference_signals = []
        t = np.arange(
            0, (length / (self.sampling_rate)), step=(1.0 / (self.sampling_rate))
        )
        # print(t)
        reference_signals.append(np.sin(2 * np.pi * target_freq * t))
        reference_signals.append(np.cos(2 * np.pi * target_freq * t))

        reference_signals.append(np.sin(4 * np.pi * target_freq * t))
        reference_signals.append(np.cos(4 * np.pi * target_freq * t))

        reference_signals = np.array(reference_signals)

        return reference_signals

    def sk_findCorr(self, n_components: int, data: np.ndarray) -> np.ndarray:
        """Perform Canonical correlation analysis (CCA)

        _extended_summary_

        Args:
            n_components (int): _description_
            data (np.ndarray): consists of the EEG, rows -> data, columns -> channels

        Returns:
            np.ndarray: _description_
        """
        # Perform Canonical correlation analysis (CCA)
        # data - consists of the EEG, rows -> data, columns -> channels
        # print("data: ", data.shape)

        cca = CCA(n_components)
        corr = np.zeros(n_components)
        result = np.zeros((self.reference_signals.shape)[0])
        for freqIdx in range(0, (self.reference_signals.shape)[0]):
            # print(
            #     f"ref_{freqIdx}:",
            #     np.squeeze(self.reference_signals[freqIdx, :, :]).T.shape,
            # )
            # print(np.squeeze(freq[freqIdx, :, :]).T)
            cca.fit(data, np.squeeze(self.reference_signals[freqIdx, :, :]).T)
            O1_a, O1_b = cca.transform(
                data, np.squeeze(self.reference_signals[freqIdx, :, :]).T
            )
            indVal = 0
            for indVal in range(0, n_components):
                corr[indVal] = np.corrcoef(O1_a[:, indVal], O1_b[:, indVal])[0, 1]
                # print(np.corrcoef(O1_a[:, indVal], O1_b[:, indVal]))
            result[freqIdx] = np.max(corr)

        # print(result)
        return result

    def cca_analysis(self, data: np.ndarray):
        # data and data_ref are assumed to be of dimensions:
        # data: (# of samples, # of channels)
        # data_ref: (# of samples, # of )

        # Combine the data and reference data based on their dimensionality
        result = []
        for freqIdx in range(0, (self.reference_signals.shape)[0]):
            data_ref = np.squeeze(self.reference_signals[freqIdx, :, :]).T
            xy = (
                np.concatenate((data, data_ref), axis=1)
                if data.shape[1] <= data_ref.shape[1]
                else np.concatenate((data_ref, data), axis=1)
            )

            # Calculate covariance matrices
            covariance = np.cov(xy, rowvar=False)
            n = min(data.shape[1], data_ref.shape[1])
            cx = covariance[:n, :n]
            cy = covariance[n:, n:]
            cxy = covariance[:n, n:]
            cyx = covariance[n:, :n]

            # Solve the optimization problem using eigenvalue decomposition
            eps = np.finfo(float).eps
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

            # Eigenvalue decomposition and sorting
            eig_vals = np.linalg.eigvals(corr_coef)

            # Set any small negative eigenvalues to zero, assuming they are due to numerical error
            eig_vals[eig_vals < 0] = 0
            d_coeff = np.sort(np.real(eig_vals))[
                ::-1
            ]  # Only real parts, sorted in descending order
            d_coeff = np.sqrt(
                np.sort(np.real(eig_vals))[::-1]
            )  # Only real parts, sorted in descending order

            result.append(d_coeff[:n])
        result = np.array(result)
        return result
        # return d_coeff[:n]  # Return the canonical correlations
