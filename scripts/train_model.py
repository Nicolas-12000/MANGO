"""Fit the orchestrator and write the artifacts the apps load."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from mango.constants import (
    ANALYSIS_PATH,
    FIGURES_DIR,
    FRONTEND_BUNDLE_PATH,
    PROCESSED_CSV_PATH,
    TREATMENT_REPORT_PATH,
)
from mango.orchestration.pipeline import SegmentationOrchestrator
from mango.visualization import save_figures


def main() -> None:
    orchestrator = SegmentationOrchestrator()
    analysis = orchestrator.fit()
    artifact = orchestrator.save()
    PROCESSED_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    assert orchestrator.frame is not None
    orchestrator.frame.to_csv(PROCESSED_CSV_PATH, index=False)
    _write_json(ANALYSIS_PATH, analysis)
    if FRONTEND_BUNDLE_PATH.parent.parent.exists():
        _write_json(FRONTEND_BUNDLE_PATH, analysis)
    figures = save_figures(analysis)
    _publish_figures(figures)
    TREATMENT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    TREATMENT_REPORT_PATH.write_text(_treatment_markdown(analysis), encoding="utf-8")
    print(f"artifact: {artifact}")
    print(f"k={analysis['selected_k']} silhouette={analysis['model_silhouette']:.4f}")
    print(f"features={analysis['feature_selection']['selected_features']}")
    for figure in figures:
        print(f"figure: {figure}")


def _publish_figures(figures: list[Path]) -> None:
    public = FRONTEND_BUNDLE_PATH.parent / "figures"
    if not FRONTEND_BUNDLE_PATH.parent.parent.exists():
        return
    public.mkdir(parents=True, exist_ok=True)
    for figure in figures:
        shutil.copyfile(figure, public / figure.name)
    if not figures and FIGURES_DIR.exists():
        for figure in FIGURES_DIR.glob("*.png"):
            shutil.copyfile(figure, public / figure.name)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _treatment_markdown(analysis: dict) -> str:
    quality = analysis["quality"]
    sensitivity = analysis["sensitivity"]
    iqr_lines = [
        f"| `{name}` | {detail['lower']:.2f} | {detail['upper']:.2f} | {detail['count']} | {detail['customer_ids']} |"
        for name, detail in quality["iqr_fences"].items()
    ]
    return "\n".join(
        [
            "# Limpieza de datos",
            "",
            "Se etiquetan colas estadísticas y solo se eliminan valores imposibles.",
            "",
            f"- Filas de entrada: {quality['rows_raw']}",
            f"- Filas listas: {quality['rows_ready']}",
            f"- Filas eliminadas: {quality['rows_removed']}",
            f"- Duplicados exactos: {quality['duplicate_rows']}",
            f"- `customer_id` duplicados: {quality['duplicate_customer_ids']}",
            f"- Nulos: `{quality['missing_by_column']}`",
            f"- Errores de captura: `{quality['capture_errors_by_column']}`",
            "",
            "## Valla de Tukey (1.5 IQR)",
            "",
            "| Variable | Límite inferior | Límite superior | Conteo | customer_id |",
            "|---|---:|---:|---:|---|",
            *iqr_lines,
            "",
            "## Z modificada de Iglewicz y Hoaglin",
            "",
            "Umbral 3.5. Un valor por encima es una cola robusta, no un borrado automático.",
            "",
            "## Distancia de Mahalanobis",
            "",
            (
                f"Alfa {quality['mahalanobis']['alpha']}, "
                f"umbral chi-cuadrado {quality['mahalanobis']['threshold']:.3f}, "
                f"filas marcadas: {quality['mahalanobis']['count']}."
            ),
            "",
            "La nube tiene varios grupos. Una sola elipse gaussiana marca las esquinas de segmentos reales, así que esa marca no saca filas.",
            "",
            "## Sensibilidad",
            "",
            (
                f"Se reentrena sin las colas IQR de las variables del modelo "
                f"({sensitivity['rows_held_out']} filas). "
                f"Silueta completa: {sensitivity['silhouette_full']:.4f}. "
                f"Sin esas colas: {sensitivity['silhouette_without_tails']:.4f}. "
                f"Desplazamiento máximo de centroide, en unidades originales: {sensitivity['max_centroid_shift']:.4f}."
            ),
            "",
            "Esas colas siguen en el modelo publicado. En ingreso, son clientes reales de la cola alta, no un error de captura.",
            "",
        ]
    )


if __name__ == "__main__":
    main()