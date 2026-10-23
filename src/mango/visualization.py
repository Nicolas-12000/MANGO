"""Figures for the notebook, the report, and Streamlit. Colors match frontend/DESIGN.md."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from mango.constants import FIGURES_DIR, PALETTE, PROFILE_COLORS
from mango.interpretation.profiles import PROFILE_ORDER

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "axes.titlesize": 13,
        "axes.labelsize": 11,
        "figure.facecolor": PALETTE["paper"],
        "axes.facecolor": PALETTE["surface"],
        "axes.edgecolor": PALETTE["ink"],
        "axes.labelcolor": PALETTE["ink"],
        "xtick.color": PALETTE["ink"],
        "ytick.color": PALETTE["ink"],
        "text.color": PALETTE["ink"],
        "axes.titlecolor": PALETTE["ink"],
    }
)


def plot_elbow(analysis: dict) -> plt.Figure:
    figure, axis = plt.subplots(figsize=(7, 4.2))
    k_values = [point["k"] for point in analysis["elbow"]]
    inertia = [point["inertia"] for point in analysis["elbow"]]
    chosen = analysis["selected_k"]
    axis.plot(k_values, inertia, color=PALETTE["mango"], marker="o")
    chosen_inertia = next(point["inertia"] for point in analysis["elbow"] if point["k"] == chosen)
    axis.scatter([chosen], [chosen_inertia], s=90, color=PALETTE["ink"], zorder=3)
    axis.set_title("Método del codo")
    axis.set_xlabel("K")
    axis.set_ylabel("Inertia (WCSS)")
    axis.set_xticks(k_values)
    figure.tight_layout()
    return figure


def plot_silhouette(analysis: dict) -> plt.Figure:
    figure, axis = plt.subplots(figsize=(7, 4.2))
    k_values = [point["k"] for point in analysis["silhouette_curve"]]
    scores = [point["score"] for point in analysis["silhouette_curve"]]
    chosen = analysis["selected_k"]
    colors = [PALETTE["ink"] if k == chosen else PALETTE["mango"] for k in k_values]
    axis.bar(k_values, scores, color=colors)
    axis.set_title("Coeficiente de silueta")
    axis.set_xlabel("K")
    axis.set_ylabel("Silhouette")
    axis.set_xticks(k_values)
    figure.tight_layout()
    return figure


def plot_clusters(analysis: dict) -> plt.Figure:
    figure, axis = plt.subplots(figsize=(7.2, 5.2))
    frame = pd.DataFrame(analysis["customers"])
    for profile in PROFILE_ORDER:
        group = frame.loc[frame["profile"] == profile]
        if group.empty:
            continue
        headline = next(cluster["headline"] for cluster in analysis["clusters"] if cluster["profile"] == profile)
        axis.scatter(
            group["annual_income_k"],
            group["spending_score"],
            s=36,
            color=PROFILE_COLORS[profile],
            label=headline,
        )
    for cluster in analysis["clusters"]:
        axis.scatter(
            [cluster["centroid"]["annual_income_k"]],
            [cluster["centroid"]["spending_score"]],
            s=120,
            marker="X",
            color=PALETTE["ink"],
        )
    axis.set_title("Segmentos")
    axis.set_xlabel("annual_income_k")
    axis.set_ylabel("spending_score")
    axis.legend(frameon=False, fontsize=8)
    figure.tight_layout()
    return figure


def plot_boxplots(analysis: dict) -> plt.Figure:
    frame = pd.DataFrame(analysis["customers"])
    figure, axes = plt.subplots(1, 3, figsize=(9, 3.8))
    columns = ("age", "annual_income_k", "spending_score")
    for axis, column in zip(axes, columns, strict=True):
        axis.boxplot(
            frame[column],
            patch_artist=True,
            boxprops={"facecolor": PALETTE["pulp"], "edgecolor": PALETTE["ink"]},
            medianprops={"color": PALETTE["ink"]},
            whiskerprops={"color": PALETTE["ink"]},
            capprops={"color": PALETTE["ink"]},
            flierprops={"marker": "o", "markerfacecolor": PALETTE["mango"], "markeredgecolor": PALETTE["ink"]},
        )
        axis.set_title(column)
        axis.set_xticks([])
    figure.tight_layout()
    return figure


def save_figures(analysis: dict, directory: Path | None = None) -> list[Path]:
    target = directory or FIGURES_DIR
    target.mkdir(parents=True, exist_ok=True)
    saved = []
    for name, builder in (
        ("elbow", plot_elbow),
        ("silhouette", plot_silhouette),
        ("clusters", plot_clusters),
        ("boxplots", plot_boxplots),
    ):
        figure = builder(analysis)
        path = target / f"{name}.png"
        figure.savefig(path, dpi=140)
        plt.close(figure)
        saved.append(path)
    return saved
