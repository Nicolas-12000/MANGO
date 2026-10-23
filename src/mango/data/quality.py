"""Load Mall Customers and separate capture errors from real tails.

Tukey fences and the Iglewicz–Hoaglin modified z-score screen each numeric
column. Mahalanobis distance screens the numeric cloud. Those flags label
rows. A row is removed only when a value cannot occur.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import chi2

from mango.constants import (
    ALLOWED_GENDERS,
    COLUMN_MAP,
    HARD_BOUNDS,
    IDENTIFIER_COLUMN,
    IQR_MULTIPLIER,
    MAHALANOBIS_ALPHA,
    MODIFIED_Z_THRESHOLD,
    NUMERIC_COLUMNS,
    RAW_CSV_PATH,
)


def load_customers(path: Path | None = None) -> pd.DataFrame:
    """Read the Kaggle file and rename every column to English snake_case."""
    source = path or RAW_CSV_PATH
    frame = pd.read_csv(source)
    missing = [column for column in COLUMN_MAP if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing source columns: {missing}")
    renamed = frame.rename(columns=COLUMN_MAP)
    return renamed.loc[:, list(COLUMN_MAP.values())].copy()


def screen_customers(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Return the analysis-ready frame and a quality report."""
    rows_raw = int(len(frame))
    working = frame.copy()

    coercion_failures = _coerce_numeric(working)
    missing_by_column = {column: int(working[column].isna().sum()) for column in working.columns}
    duplicate_rows = int(working.duplicated().sum())
    duplicate_customer_ids = int(working[IDENTIFIER_COLUMN].duplicated().sum())
    deduped = working.drop_duplicates().drop_duplicates(subset=[IDENTIFIER_COLUMN], keep="first")

    capture_error = pd.Series(False, index=deduped.index)
    capture_errors_by_column: dict[str, int] = {}
    invalid_gender = ~deduped["gender"].isin(ALLOWED_GENDERS) | deduped["gender"].isna()
    capture_errors_by_column["gender"] = int(invalid_gender.sum())
    capture_error = capture_error | invalid_gender
    for column, (lower, upper) in HARD_BOUNDS.items():
        invalid = deduped[column].isna() | (deduped[column] < lower) | (deduped[column] > upper)
        capture_errors_by_column[column] = int(invalid.sum())
        capture_error = capture_error | invalid

    ready = deduped.loc[~capture_error].copy()
    iqr_detail = {}
    modified_z_detail = {}
    any_iqr = pd.Series(False, index=ready.index)
    any_modified_z = pd.Series(False, index=ready.index)
    for column in NUMERIC_COLUMNS:
        iqr_mask, fences = _iqr_mask(ready[column])
        modified_mask = _modified_z(ready[column]).abs() > MODIFIED_Z_THRESHOLD
        ready[f"is_iqr_outlier_{column}"] = iqr_mask.to_numpy()
        ready[f"is_modified_z_outlier_{column}"] = modified_mask.to_numpy()
        any_iqr = any_iqr | iqr_mask
        any_modified_z = any_modified_z | modified_mask
        iqr_detail[column] = {
            "lower": fences[0],
            "upper": fences[1],
            "count": int(iqr_mask.sum()),
            "customer_ids": _ids(ready, iqr_mask),
        }
        modified_z_detail[column] = {
            "threshold": MODIFIED_Z_THRESHOLD,
            "count": int(modified_mask.sum()),
            "customer_ids": _ids(ready, modified_mask),
        }

    mahalanobis_numeric, numeric_threshold = _mahalanobis_mask(ready, NUMERIC_COLUMNS)
    ready["is_iqr_outlier"] = any_iqr.to_numpy()
    ready["is_modified_z_outlier"] = any_modified_z.to_numpy()
    ready["is_mahalanobis_outlier"] = mahalanobis_numeric.to_numpy()
    statistical_tail = any_iqr | any_modified_z | mahalanobis_numeric
    ready["anomaly_category"] = np.where(statistical_tail, "statistical_tail", "normal")

    report: dict[str, Any] = {
        "rows_raw": rows_raw,
        "rows_ready": int(len(ready)),
        "rows_removed": int(rows_raw - len(ready)),
        "missing_by_column": missing_by_column,
        "coercion_failures": coercion_failures,
        "duplicate_rows": duplicate_rows,
        "duplicate_customer_ids": duplicate_customer_ids,
        "capture_errors_by_column": capture_errors_by_column,
        "iqr_fences": iqr_detail,
        "modified_z": modified_z_detail,
        "mahalanobis": {
            "alpha": MAHALANOBIS_ALPHA,
            "degrees_of_freedom": len(NUMERIC_COLUMNS),
            "threshold": numeric_threshold,
            "count": int(mahalanobis_numeric.sum()),
            "customer_ids": _ids(ready, mahalanobis_numeric),
            "assumption": "single_gaussian",
        },
        "statistical_tail_count": int(statistical_tail.sum()),
        "removal_policy": "capture_errors_only",
    }
    return ready.reset_index(drop=True), report


def summarize_customers(frame: pd.DataFrame) -> dict[str, Any]:
    """Basic descriptive statistics for the ready frame."""
    numeric = frame.loc[:, list(NUMERIC_COLUMNS)]
    described = numeric.describe(percentiles=[0.25, 0.5, 0.75]).transpose()
    summary = {}
    for column, row in described.iterrows():
        summary[str(column)] = {
            "count": int(row["count"]),
            "mean": float(row["mean"]),
            "std": float(row["std"]),
            "min": float(row["min"]),
            "q1": float(row["25%"]),
            "median": float(row["50%"]),
            "q3": float(row["75%"]),
            "max": float(row["max"]),
        }
    gender_counts = {str(key): int(value) for key, value in frame["gender"].value_counts().items()}
    correlations = numeric.corr(method="pearson").round(6)
    return {
        "rows": int(len(frame)),
        "columns": list(COLUMN_MAP.values()),
        "numeric_summary": summary,
        "gender_counts": gender_counts,
        "correlations": correlations.to_dict(),
    }


def _coerce_numeric(frame: pd.DataFrame) -> dict[str, int]:
    failures: dict[str, int] = {}
    for column in NUMERIC_COLUMNS:
        numeric = pd.to_numeric(frame[column], errors="coerce")
        failures[column] = int((numeric.isna() & frame[column].notna()).sum())
        frame[column] = numeric
    frame[IDENTIFIER_COLUMN] = pd.to_numeric(frame[IDENTIFIER_COLUMN], errors="coerce")
    return failures


def _iqr_mask(series: pd.Series) -> tuple[pd.Series, tuple[float, float]]:
    q1 = float(series.quantile(0.25))
    q3 = float(series.quantile(0.75))
    iqr = q3 - q1
    lower = q1 - IQR_MULTIPLIER * iqr
    upper = q3 + IQR_MULTIPLIER * iqr
    return (series < lower) | (series > upper), (lower, upper)


def _modified_z(series: pd.Series) -> pd.Series:
    median = float(series.median())
    mad = float(np.median(np.abs(series - median)))
    if mad == 0:
        return pd.Series(np.zeros(len(series)), index=series.index)
    return 0.6745 * (series - median) / mad


def _mahalanobis_mask(frame: pd.DataFrame, columns: tuple[str, ...]) -> tuple[pd.Series, float]:
    values = frame.loc[:, list(columns)].to_numpy(dtype=float)
    center = values.mean(axis=0)
    covariance = np.atleast_2d(np.cov(values, rowvar=False))
    precision = np.linalg.pinv(covariance)
    delta = values - center
    distances = np.einsum("ij,jk,ik->i", delta, precision, delta)
    threshold = float(chi2.ppf(MAHALANOBIS_ALPHA, df=len(columns)))
    return pd.Series(distances > threshold, index=frame.index), threshold


def _ids(frame: pd.DataFrame, mask: pd.Series) -> list[int]:
    identifiers = frame.loc[mask.to_numpy(), IDENTIFIER_COLUMN]
    return [int(value) for value in identifiers.tolist()]
