"""One orchestrator. It is the only place that runs the segmentation steps in order."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from mango.clustering.model import (
    compare_feature_sets,
    elbow_curve,
    fit_kmeans,
    geometric_elbow_k,
    scale_features,
    select_k,
    silhouette_curve,
)
from mango.constants import (
    ARTIFACT_PATH,
    FEATURE_SETS,
    SEGMENT_FEATURES,
    SILHOUETTE_TOLERANCE,
)
from mango.data.quality import load_customers, screen_customers, summarize_customers
from mango.interpretation.profiles import (
    GROWTH_OPPORTUNITY,
    PROFILE_CATALOG,
    assign_profile_names,
    build_cluster_summaries,
)
from mango.serialization import to_builtin


class SegmentationOrchestrator:
    def __init__(self, data_path: Path | None = None) -> None:
        self.data_path = data_path
        self.frame: pd.DataFrame | None = None
        self.scaler: Any = None
        self.model: Any = None
        self.selected_features: tuple[str, ...] = SEGMENT_FEATURES
        self.analysis: dict[str, Any] | None = None
        self.training_ranges: dict[str, tuple[float, float]] = {}

    def fit(self) -> dict[str, Any]:
        raw = load_customers(self.data_path)
        ready, quality = screen_customers(raw)
        comparison = compare_feature_sets(ready, FEATURE_SETS)
        selected = _select_features(comparison)
        scaled, scaler = scale_features(ready, selected)
        elbow = elbow_curve(scaled)
        silhouette = silhouette_curve(scaled)
        decision = select_k(geometric_elbow_k(elbow), silhouette)
        model = fit_kmeans(scaled, decision["selected_k"])
        labels = [int(label) for label in model.labels_]
        original_centroids = _original_centroids(model.cluster_centers_, scaler, selected)
        scaled_centroids = _scaled_centroids(model.cluster_centers_, selected)
        names = assign_profile_names(
            original_centroids,
            float(ready["annual_income_k"].median()),
            float(ready["spending_score"].median()),
        )
        clusters = build_cluster_summaries(ready, labels, names, original_centroids, scaled_centroids)
        sensitivity = _sensitivity(ready, selected, labels, decision["selected_k"])
        customers = _customer_records(ready, labels, names)
        ranges = {
            feature: (float(ready[feature].min()), float(ready[feature].max())) for feature in selected
        }
        analysis = to_builtin(
            {
                "dataset": summarize_customers(ready),
                "quality": quality,
                "feature_selection": {
                    "selected_features": list(selected),
                    "preferred_features": list(SEGMENT_FEATURES),
                    "comparison": comparison,
                    "rule": _feature_rule(comparison, selected),
                },
                "scaling": {
                    "method": "standard_scaler",
                    "features": list(selected),
                    "mean": {feature: float(value) for feature, value in zip(selected, scaler.mean_)},
                    "scale": {feature: float(value) for feature, value in zip(selected, scaler.scale_)},
                },
                "elbow": elbow,
                "silhouette_curve": silhouette,
                "k_selection": decision,
                "selected_k": decision["selected_k"],
                "model_silhouette": decision["silhouette"],
                "inertia": float(model.inertia_),
                "sensitivity": sensitivity,
                "clusters": clusters,
                "growth_opportunity": GROWTH_OPPORTUNITY,
                "growth_headline": PROFILE_CATALOG[GROWTH_OPPORTUNITY]["headline"],
                "customers": customers,
            }
        )
        self.frame = ready.assign(
            cluster_id=labels,
            profile=[names[label] for label in labels],
        )
        self.scaler = scaler
        self.model = model
        self.selected_features = selected
        self.training_ranges = ranges
        self.analysis = analysis
        return analysis

    def classify(self, customer: dict[str, Any]) -> dict[str, Any]:
        if self.model is None or self.scaler is None or self.analysis is None:
            self.fit()
        assert self.model is not None
        assert self.scaler is not None
        assert self.analysis is not None
        features = self.selected_features
        scaled_row = self.scaler.transform([[float(customer[feature]) for feature in features]])
        cluster_id = int(self.model.predict(scaled_row)[0])
        center = self.model.cluster_centers_[cluster_id]
        distance = float(np.linalg.norm(scaled_row[0] - center))
        cluster = next(item for item in self.analysis["clusters"] if item["cluster_id"] == cluster_id)
        outside = [
            feature
            for feature in features
            if float(customer[feature]) < self.training_ranges[feature][0]
            or float(customer[feature]) > self.training_ranges[feature][1]
        ]
        return to_builtin(
            {
                "cluster_id": cluster_id,
                "profile": cluster["profile"],
                "headline": cluster["headline"],
                "description": cluster["description"],
                "strategy": cluster["strategy"],
                "distance_to_centroid": distance,
                "scaled_input": {
                    feature: float(value) for feature, value in zip(features, scaled_row[0], strict=True)
                },
                "features_used": list(features),
                "features_ignored": ["gender", "age"],
                "outside_training_range": outside,
                "centroid": cluster["centroid"],
            }
        )

    def save(self, path: Path | None = None) -> Path:
        if self.analysis is None:
            self.fit()
        target = path or ARTIFACT_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "scaler": self.scaler,
                "model": self.model,
                "selected_features": self.selected_features,
                "analysis": self.analysis,
                "training_ranges": self.training_ranges,
            },
            target,
        )
        return target

    def load(self, path: Path | None = None) -> dict[str, Any]:
        payload = joblib.load(path or ARTIFACT_PATH)
        self.scaler = payload["scaler"]
        self.model = payload["model"]
        self.selected_features = tuple(payload["selected_features"])
        self.analysis = payload["analysis"]
        self.training_ranges = payload["training_ranges"]
        assert self.analysis is not None
        return self.analysis


def _select_features(comparison: list[dict[str, Any]]) -> tuple[str, ...]:
    best = max(comparison, key=lambda row: row["silhouette"])
    preferred = next(row for row in comparison if tuple(row["features"]) == SEGMENT_FEATURES)
    if preferred["silhouette"] >= best["silhouette"] - SILHOUETTE_TOLERANCE:
        return SEGMENT_FEATURES
    return tuple(best["features"])


def _feature_rule(comparison: list[dict[str, Any]], selected: tuple[str, ...]) -> str:
    best = max(comparison, key=lambda row: row["silhouette"])
    if tuple(best["features"]) == selected:
        return "best_silhouette"
    return "preferred_within_tolerance"


def _original_centroids(centers: np.ndarray, scaler: Any, features: tuple[str, ...]) -> list[dict[str, float]]:
    restored = scaler.inverse_transform(centers)
    rows = []
    for cluster_id, center in enumerate(restored):
        row: dict[str, float] = {"cluster_id": float(cluster_id)}
        for feature, value in zip(features, center, strict=True):
            row[feature] = float(value)
        rows.append(row)
    return rows


def _scaled_centroids(centers: np.ndarray, features: tuple[str, ...]) -> list[dict[str, float]]:
    rows = []
    for cluster_id, center in enumerate(centers):
        row: dict[str, float] = {"cluster_id": float(cluster_id)}
        for feature, value in zip(features, center, strict=True):
            row[feature] = float(value)
        rows.append(row)
    return rows


def _customer_records(frame: pd.DataFrame, labels: list[int], names: dict[int, str]) -> list[dict[str, Any]]:
    records = []
    for row, label in zip(frame.itertuples(index=False), labels, strict=True):
        records.append(
            {
                "customer_id": int(row.customer_id),
                "gender": row.gender,
                "age": int(row.age),
                "annual_income_k": float(row.annual_income_k),
                "spending_score": float(row.spending_score),
                "cluster_id": int(label),
                "profile": names[int(label)],
                "anomaly_category": row.anomaly_category,
            }
        )
    return records


def _sensitivity(
    frame: pd.DataFrame,
    features: tuple[str, ...],
    labels: list[int],
    k: int,
) -> dict[str, float | int]:
    from sklearn.metrics import silhouette_score

    holdout = pd.Series(False, index=frame.index)
    for feature in features:
        column = f"is_iqr_outlier_{feature}"
        if column in frame.columns:
            holdout = holdout | frame[column]
    kept = frame.loc[~holdout]
    full_scaled, full_scaler = scale_features(frame, features)
    full_model = fit_kmeans(full_scaled, k)
    full_score = float(silhouette_score(full_scaled, labels))
    if len(kept) <= k or int(holdout.sum()) == 0:
        return {
            "rows_held_out": int(holdout.sum()),
            "silhouette_full": full_score,
            "silhouette_without_tails": full_score,
            "max_centroid_shift": 0.0,
        }
    reduced_scaled, reduced_scaler = scale_features(kept, features)
    reduced_model = fit_kmeans(reduced_scaled, k)
    reduced_score = float(silhouette_score(reduced_scaled, reduced_model.labels_))
    full_original = full_scaler.inverse_transform(full_model.cluster_centers_)
    reduced_original = reduced_scaler.inverse_transform(reduced_model.cluster_centers_)
    aligned = _match_centers(full_original, reduced_original)
    shift = float(np.max(np.linalg.norm(aligned - reduced_original, axis=1)))
    return {
        "rows_held_out": int(holdout.sum()),
        "silhouette_full": full_score,
        "silhouette_without_tails": reduced_score,
        "max_centroid_shift": shift,
    }


def _match_centers(reference: np.ndarray, other: np.ndarray) -> np.ndarray:
    """Reorder reference centers so each row lines up with the nearest row in other."""
    order = []
    used: set[int] = set()
    for center in other:
        distances = np.linalg.norm(reference - center, axis=1)
        for index in np.argsort(distances):
            if int(index) not in used:
                used.add(int(index))
                order.append(int(index))
                break
    return reference[order]
