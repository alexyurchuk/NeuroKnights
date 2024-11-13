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
            self.reference_signals.appen(
                self.get_reference_signals(cca_buffer_size, frequency)
            )
        self.reference_signals = np.array(self.reference_signals)

    def get_reference_signals(self, length, target_freq) -> np.ndarray:
        """Get reference signals

        Only signals with first and second harmonics of each of the frequencies.

        Args:
            length (int): length of data needed -> # of samples
            target_freq (float): target frequency
        """

        reference_signals = []
        t = np.arange(
            0, (length / (self.sampling_rate)), step=1.0 / (self.sampling_rate)
        )
        reference_signals.append(np.sin(2 * np.pi * target_freq * t))
        reference_signals.append(np.cos(2 * np.pi * target_freq * t))

        reference_signals.append(np.sin(4 * np.pi * target_freq * t))
        reference_signals.append(np.cos(4 * np.pi * target_freq * t))

        reference_signals = np.array(reference_signals)

        return reference_signals

    def findCorr(self, n_components: int, data: np.ndarray) -> np.ndarray:
        """Perform Canonical correlation analysis (CCA)

        _extended_summary_

        Args:
            n_components (int): _description_
            data (np.ndarray): consists of the EEG data

        Returns:
            np.ndarray: _description_
        """
        # Perform Canonical correlation analysis (CCA)
        # data - consists of the EEG
        # print(data.T)
        cca = CCA(n_components)
        corr = np.zeros(n_components)
        result = np.zeros((self.reference_signals.shape)[0])
        for freqIdx in range(0, (self.reference_signals.shape)[0]):
            # print(np.squeeze(freq[freqIdx, :, :]).T)
            cca.fit(data.T, np.squeeze(self.reference_signals[freqIdx, :, :]).T)
            O1_a, O1_b = cca.transform(
                data.T, np.squeeze(self.reference_signals[freqIdx, :, :]).T
            )
            indVal = 0
            for indVal in range(0, n_components):
                corr[indVal] = np.corrcoef(O1_a[:, indVal], O1_b[:, indVal])[0, 1]
            result[freqIdx] = np.max(corr)
        # print(result)
        return result
