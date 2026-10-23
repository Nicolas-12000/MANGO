"""StandardScaler, elbow, silhouette, and K-Means."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from mango.constants import (
    K_RANGE,
    K_SILHOUETTE_GAP,
    N_INIT,
    RANDOM_STATE,
    SILHOUETTE_K_RANGE,
)


def scale_features(
    frame: pd.DataFrame,
    features: tuple[str, ...] | list[str],
) -> tuple[np.ndarray, StandardScaler]:
    scaler = StandardScaler()
    scaled = scaler.fit_transform(frame.loc[:, list(features)].to_numpy(dtype=float))
    return scaled, scaler


def elbow_curve(scaled: np.ndarray, k_values: range = K_RANGE) -> list[dict[str, float]]:
    curve = []
    for k in k_values:
        model = _kmeans(k)
        model.fit(scaled)
        curve.append({"k": int(k), "inertia": float(model.inertia_)})
    return curve


def silhouette_curve(scaled: np.ndarray, k_values: range = SILHOUETTE_K_RANGE) -> list[dict[str, float]]:
    curve = []
    for k in k_values:
        if k >= len(scaled):
            continue
        model = _kmeans(k)
        labels = model.fit_predict(scaled)
        score = float(silhouette_score(scaled, labels))
        curve.append({"k": int(k), "score": score})
    return curve


def geometric_elbow_k(curve: list[dict[str, float]]) -> int:
    """K farthest from the chord between the first and last inertia."""
    k_values = np.asarray([point["k"] for point in curve], dtype=float)
    inertia = np.asarray([point["inertia"] for point in curve], dtype=float)
    x_norm = (k_values - k_values[0]) / (k_values[-1] - k_values[0])
    span = inertia[0] - inertia[-1]
    if span == 0:
        return int(k_values[0])
    y_norm = (inertia - inertia[-1]) / span
    x1, y1 = x_norm[0], y_norm[0]
    x2, y2 = x_norm[-1], y_norm[-1]
    numerator = np.abs((y2 - y1) * x_norm - (x2 - x1) * y_norm + x2 * y1 - y2 * x1)
    denominator = float(np.hypot(x2 - x1, y2 - y1))
    return int(k_values[int(np.argmax(numerator / denominator))])


def select_k(elbow_k: int, silhouette: list[dict[str, float]]) -> dict[str, Any]:
    """Agree with the elbow when the silhouette gap is small; otherwise follow silhouette."""
    best = max(silhouette, key=lambda point: point["score"])
    silhouette_k = int(best["k"])
    elbow_score = next(point["score"] for point in silhouette if int(point["k"]) == elbow_k)
    if elbow_k == silhouette_k:
        selected_k = elbow_k
        rule = "elbow_and_silhouette_agree"
    elif best["score"] - elbow_score > K_SILHOUETTE_GAP:
        selected_k = silhouette_k
        rule = "silhouette_breaks_the_tie"
    else:
        selected_k = elbow_k
        rule = "elbow_when_silhouette_gap_is_small"
    selected_score = next(point["score"] for point in silhouette if int(point["k"]) == selected_k)
    return {
        "selected_k": int(selected_k),
        "elbow_k": int(elbow_k),
        "silhouette_k": silhouette_k,
        "rule": rule,
        "silhouette": float(selected_score),
        "methods_agree": elbow_k == silhouette_k,
    }


def compare_feature_sets(
    frame: pd.DataFrame,
    feature_sets: tuple[tuple[str, ...], ...],
) -> list[dict[str, Any]]:
    comparison = []
    for features in feature_sets:
        scaled, _scaler = scale_features(frame, features)
        curve = silhouette_curve(scaled)
        best = max(curve, key=lambda point: point["score"])
        comparison.append(
            {
                "features": list(features),
                "best_k": int(best["k"]),
                "silhouette": float(best["score"]),
            }
        )
    return comparison


def fit_kmeans(scaled: np.ndarray, k: int) -> KMeans:
    model = _kmeans(k)
    model.fit(scaled)
    return model


def _kmeans(k: int) -> KMeans:
    return KMeans(n_clusters=k, n_init=N_INIT, random_state=RANDOM_STATE)
