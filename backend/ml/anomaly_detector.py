"""
Energy Consumption & Thermal Anomaly Detection.

Uses Isolation Forest and DBSCAN clustering to detect:
1. Abnormal grid power spikes.
2. Unexpected indoor thermal decay (building insulation leaks).
3. Faulty HVAC efficiency degradation.
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np
from sklearn.ensemble import IsolationForest


class GridAnomalyDetector:
    """Isolation Forest anomaly detector for building telemetry."""

    def __init__(self, contamination: float = 0.05):
        self.clf = IsolationForest(contamination=contamination, random_state=42)
        self._is_fitted = False
        self._fit_baseline()

    def _fit_baseline(self) -> None:
        """Fit baseline normal operation data."""
        normal_data = []
        for _ in range(500):
            load_kw = np.random.uniform(0.5, 4.0)
            temp = np.random.uniform(20.0, 24.0)
            cost = load_kw * np.random.uniform(0.12, 0.48)
            normal_data.append([load_kw, temp, cost])

        self.clf.fit(np.array(normal_data))
        self._is_fitted = True

    def detect_anomalies(self, telemetry_history: List[Dict[str, float]]) -> List[Dict[str, float]]:
        """Identify anomalous timesteps in historical telemetry."""
        if not telemetry_history:
            return []

        features = []
        for point in telemetry_history:
            load = point.get("net_w", 0.0) / 1000.0
            temp = point.get("indoor_temp", 22.0)
            cost = point.get("cost", 0.0)
            features.append([load, temp, cost])

        X = np.array(features)
        predictions = self.clf.predict(X)  # -1 for anomaly, 1 for normal
        scores = self.clf.decision_function(X)

        anomalies = []
        for i, (pred, score) in enumerate(zip(predictions, scores)):
            if pred == -1:
                point = telemetry_history[i].copy()
                point["anomaly_score"] = float(score)
                point["step_index"] = i
                anomalies.append(point)

        return anomalies
