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
            eps = np.finfo(np.float32).eps
            try:
                if np.linalg.det(cx) != 0 and np.linalg.det(cy) != 0:
                    cx_inv = np.linalg.inv(cx)
                    cy_inv = np.linalg.inv(cy)
                else:
                    # print("Taking changed version of cx and cy...")
                    coef = 10 ** (-5)
                    cx_inv = np.linalg.inv(cx + coef * eps * np.eye(cx.shape[0]))
                    cy_inv = np.linalg.inv(cy + coef * eps * np.eye(cy.shape[0]))
                corr_coef = cy_inv @ cyx @ cx_inv @ cxy
            except Exception as e:
                print("*" * 100)
                print(f"Exception was triggered. Values:\n cx = {cx}")
                print("full thing: \n", cx + eps * np.eye(cx.shape[0]))
                print("Dtype cx: ", cx.dtype)
                print("Dtype cy: ", cy.dtype)
                print(
                    "Determinant of original cx: ",
                    np.linalg.det(cx),
                )
                print(
                    "Determinant of updated cx: ",
                    np.linalg.det(cx + coef * eps * np.eye(cx.shape[0])),
                )
                print("*" * 100)
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
