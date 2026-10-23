"""Map K-Means centroids to marketing profiles."""

from __future__ import annotations

from typing import Any

import pandas as pd

PROFILE_ORDER = (
    "high_value",
    "potential",
    "average",
    "budget_constrained",
    "low_value",
)

PROFILE_CATALOG: dict[str, dict[str, str]] = {
    "high_value": {
        "headline": "Clientes de alto valor",
        "description": "Ingreso alto y gasto alto. Ya concentran margen y frecuencia de compra.",
        "strategy": (
            "Fidelización, acceso anticipado y servicio personal. "
            "Evitar descuentos agresivos que erosionen el margen."
        ),
    },
    "potential": {
        "headline": "Clientes con potencial",
        "description": (
            "Ingreso alto y gasto bajo. Tienen capacidad de pago y poca participación en el centro comercial."
        ),
        "strategy": (
            "Campañas de conversión: experiencias, personal shopper y surtido aspiracional. "
            "Una visita nueva en este grupo mueve más el ingreso que en el resto."
        ),
    },
    "average": {
        "headline": "Clientes promedio",
        "description": "Ingreso y gasto cercanos al centro de la base de clientes.",
        "strategy": (
            "Retención con campañas de temporada y venta cruzada moderada. "
            "Medir la respuesta antes de subir la inversión."
        ),
    },
    "budget_constrained": {
        "headline": "Clientes de presupuesto ajustado",
        "description": "Gastan mucho respecto de un ingreso bajo. Compran, pero el presupuesto limita el ticket.",
        "strategy": (
            "Promociones, financiación y formatos accesibles. "
            "El volumen no se convierte solo en margen: cuidar el descuento."
        ),
    },
    "low_value": {
        "headline": "Clientes de bajo valor",
        "description": "Ingreso bajo y gasto bajo.",
        "strategy": (
            "Comunicación de precio y surtido básico. "
            "No concentrar el presupuesto de adquisición en este grupo."
        ),
    },
}

GROWTH_OPPORTUNITY = "potential"


def assign_profile_names(
    centroids: list[dict[str, float]],
    median_income: float,
    median_spending: float,
) -> dict[int, str]:
    """Label the centroid closest to the sample median as average, and the rest by quadrant."""
    middle = min(
        centroids,
        key=lambda row: (row["annual_income_k"] - median_income) ** 2
        + (row["spending_score"] - median_spending) ** 2,
    )
    names = {int(middle["cluster_id"]): "average"}
    for row in centroids:
        cluster_id = int(row["cluster_id"])
        if cluster_id == int(middle["cluster_id"]):
            continue
        high_income = row["annual_income_k"] >= median_income
        high_spending = row["spending_score"] >= median_spending
        if high_income and high_spending:
            profile = "high_value"
        elif high_income and not high_spending:
            profile = "potential"
        elif not high_income and high_spending:
            profile = "budget_constrained"
        else:
            profile = "low_value"
        names[cluster_id] = profile
    return names


def build_cluster_summaries(
    frame: pd.DataFrame,
    labels: list[int],
    names: dict[int, str],
    original_centroids: list[dict[str, float]],
    scaled_centroids: list[dict[str, float]],
) -> list[dict[str, Any]]:
    labeled = frame.copy()
    labeled["cluster_id"] = labels
    labeled["profile"] = [names[int(label)] for label in labels]
    total = len(labeled)
    original_by_id = {int(row["cluster_id"]): row for row in original_centroids}
    scaled_by_id = {int(row["cluster_id"]): row for row in scaled_centroids}
    summaries = []
    for cluster_id, group in labeled.groupby("cluster_id"):
        profile = names[int(cluster_id)]
        catalog = PROFILE_CATALOG[profile]
        female_count = int((group["gender"] == "Female").sum())
        male_count = int((group["gender"] == "Male").sum())
        size = int(len(group))
        centroid = {
            key: float(value)
            for key, value in original_by_id[int(cluster_id)].items()
            if key != "cluster_id"
        }
        scaled_centroid = {
            key: float(value)
            for key, value in scaled_by_id[int(cluster_id)].items()
            if key != "cluster_id"
        }
        summaries.append(
            {
                "cluster_id": int(cluster_id),
                "profile": profile,
                "headline": catalog["headline"],
                "description": catalog["description"],
                "strategy": catalog["strategy"],
                "size": size,
                "share": size / total,
                "centroid": centroid,
                "scaled_centroid": scaled_centroid,
                "mean_age": float(group["age"].mean()),
                "female_count": female_count,
                "male_count": male_count,
                "female_share": female_count / size,
            }
        )
    order = {profile: index for index, profile in enumerate(PROFILE_ORDER)}
    return sorted(summaries, key=lambda row: order[row["profile"]])
