"""
Unit tests for Machine Learning models: XGBoost/LSTM forecaster, PINN model, Anomaly Detector, Optuna tuner.
"""

from __future__ import annotations

import pytest

from backend.ml.anomaly_detector import GridAnomalyDetector
from backend.ml.forecast import GridEnergyForecaster
from backend.ml.pinn_model import PINNPredictor
from backend.training.optuna_tuner import OptunaRLTuner


def test_xgboost_lstm_forecaster():
    forecaster = GridEnergyForecaster()
    pred = forecaster.predict_24h(start_hour=0.0)

    assert len(pred["hours"]) == 96
    assert len(pred["temp_mean"]) == 96
    assert len(pred["solar_mean"]) == 96
    assert pred["temp_upper"][0] >= pred["temp_mean"][0]


def test_pinn_thermal_predictor():
    pinn = PINNPredictor()
    next_temp = pinn.predict_next_temp(
        t_in=22.0, t_out=32.0, solar_pu=0.8, hvac_power_ratio=0.5
    )
    assert isinstance(next_temp, float)
    assert 10.0 <= next_temp <= 40.0


def test_anomaly_detector():
    detector = GridAnomalyDetector()
    telemetry = [
        {"net_w": 2000.0, "indoor_temp": 22.0, "cost": 0.25},
        {"net_w": 25000.0, "indoor_temp": 45.0, "cost": 15.0}, # Anomaly spike
    ]
    anomalies = detector.detect_anomalies(telemetry)
    assert isinstance(anomalies, list)


def test_optuna_tuner():
    tuner = OptunaRLTuner(n_trials=2)
    study_results = tuner.run_study()
    assert "best_value" in study_results
