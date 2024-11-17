import numpy as np
import joblib

from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier

from datetime import datetime


class KNN:
    def __init__(self, features, labels):  # n_neighbors=5
        """_summary_

        _extended_summary_

        Args:
            features (_type_): [[[6 correlation coefficients], [6 PSD values]], ...] mix of different states (defferent stimuli frequencies and no stimuli too)
            labels (_type_): [...] -> -1 is no stimuli, and other (0 to 7) are indecies for the stimuli frequencies
        """
        self.X = features
        self.y = labels

    def prepare_features(self, X):
        X = [np.concatenate(features) for features in X]
        X = np.array(X)
        return X

    def split_data(self, X, y):
        # 70% training, 15% validation, 15% testing
        X_train, X_temp, y_train, y_temp = train_test_split(
            X, y, test_size=0.3, random_state=42
        )
        X_val, X_test, y_val, y_test = train_test_split(
            X_temp, y_temp, test_size=0.5, random_state=42
        )
        return X_train, X_val, X_test, y_train, y_val, y_test

    def normalize_data(
        self, X_train, X_val, X_test
    ):  # this is optional but recommended
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_val = scaler.transform(X_val)
        X_test = scaler.transform(X_test)
        joblib.dump(scaler, f"scaler_{datetime.now().strftime(r"%Y%m%d-%H%M")}.pkl")

    def train(self, X_train, y_train, n_neighbors=5):
        # Initialize k-NN model with k=5 (you can tune this)
        knn = KNeighborsClassifier(n_neighbors=n_neighbors)

        # Train the model
        knn.fit(X_train, y_train)

        return knn

    def find_best_n_negh(self, X_train, X_val, y_train, y_val):
        # Test different values of k
        for k in range(1, 11):
            knn = KNeighborsClassifier(n_neighbors=k)
            knn.fit(X_train, y_train)
            y_val_pred = knn.predict(X_val)
            accuracy = accuracy_score(y_val, y_val_pred)
            print(f"k={k}, Validation Accuracy: {accuracy:.2f}")

    def test_model(self, knn, n_neighbors, X_test, y_test):
        # Predict on the test set
        y_test_pred = knn.predict(X_test)

        # Evaluate
        test_accuracy = accuracy_score(y_test, y_test_pred)
        print(f"Test Accuracy: {test_accuracy:.2f}")

    def save_model(self, knn):
        joblib.dump(knn, f'knn_model_{datetime.now().strftime(r"%Y%m%d-%H%M")}.pkl')

    def load_model(self, filename):
        knn = joblib.load(filename)
        return knn

    def load_scaler(self, filename):
        scaler = joblib.load(filename)
        return scaler
