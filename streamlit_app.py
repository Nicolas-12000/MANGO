"""Streamlit deployment. It only talks to the segmentation controller."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from mango.constants import FIGURES_DIR
from mango.interfaces.controller import CustomerValidationError, get_controller
from mango.visualization import plot_boxplots, plot_clusters, plot_elbow, plot_silhouette

ERROR_COPY = {
    "invalid_gender": "El género tiene que ser Female o Male.",
    "invalid_age": "La edad tiene que ser un entero.",
    "invalid_annual_income_k": "El ingreso tiene que ser un número.",
    "invalid_spending_score": "El spending score tiene que ser un número.",
    "age_out_of_bounds": "La edad queda fuera de 15 a 100.",
    "annual_income_k_out_of_bounds": "El ingreso queda fuera de 0 a 500.",
    "spending_score_out_of_bounds": "El spending score queda fuera de 1 a 100.",
}


@st.cache_resource
def load_controller():
    return get_controller()


def main() -> None:
    st.set_page_config(page_title="Mango", page_icon="🥭", layout="wide")
    controller = load_controller()
    analysis = controller.analysis()
    _css()
    st.markdown('<p class="mango-kicker">Centro comercial</p>', unsafe_allow_html=True)
    st.title("Mango")
    st.caption("Mira qué tipos de cliente tienes y prueba a cuál se parece alguien nuevo.")

    metrics = st.columns(4)
    metrics[0].metric("Clientes", analysis["dataset"]["rows"], help="Personas en la base.")
    metrics[1].metric("Grupos", analysis["selected_k"], help="El número donde los grupos quedan más claros.")
    metrics[2].metric("Qué tan claros", f"{analysis['model_silhouette']:.2f}", help="1 sería una separación perfecta.")
    metrics[3].metric("Dónde crecer", "Con potencial", help="Ingreso alto y pocas compras. Ahí hay más margen por ganar.")

    exploration, elbow_tab, segments, classify_tab = st.tabs(
        ["Exploración", "Codo y silueta", "Segmentos", "Clasificar"]
    )
    with exploration:
        _exploration(analysis)
    with elbow_tab:
        _saved(analysis, "elbow", "Método del codo, figura del análisis.")
        _saved(analysis, "silhouette", "Coeficiente de silueta, figura del análisis.")
        rule = analysis["k_selection"]["rule"]
        agreed = analysis["k_selection"]["methods_agree"]
        st.write(
            "La curva se dobla en "
            f"{analysis['k_selection']['elbow_k']} grupos y la separación más nítida está en "
            f"{analysis['k_selection']['silhouette_k']}. "
            + ("Las dos cuentas coinciden." if agreed else f"Se usa la regla {rule}.")
        )
    with segments:
        _saved(analysis, "clusters", "Segmentos, figura del análisis.")
        st.dataframe(_cluster_table(analysis), use_container_width=True, hide_index=True)
    with classify_tab:
        _classify(controller)


def _exploration(analysis: dict) -> None:
    summary = pd.DataFrame(analysis["dataset"]["numeric_summary"]).T
    st.subheader("Resumen numérico")
    st.dataframe(summary, use_container_width=True)
    left, right = st.columns(2)
    with left:
        st.subheader("Género")
        st.write(analysis["dataset"]["gender_counts"])
        st.subheader("Correlación de Pearson")
        st.dataframe(pd.DataFrame(analysis["dataset"]["correlations"]), use_container_width=True)
    with right:
        _saved(analysis, "boxplots", "Diagramas de caja, figura del análisis.")
        quality = analysis["quality"]
        st.subheader("Anomalías")
        st.write(
            f"Colas estadísticas etiquetadas: {quality['statistical_tail_count']}. "
            f"Política: `{quality['removal_policy']}`."
        )
        st.json(
            {
                "iqr": {name: detail["count"] for name, detail in quality["iqr_fences"].items()},
                "modified_z": {name: detail["count"] for name, detail in quality["modified_z"].items()},
                "mahalanobis": quality["mahalanobis"]["count"],
            }
        )


def _classify(controller) -> None:
    history = st.session_state.setdefault("classification_history", [])
    with st.form("classify_customer"):
        gender = st.selectbox("Género", ["Female", "Male"], format_func=lambda value: "Mujer" if value == "Female" else "Hombre")
        age = st.number_input("Edad", min_value=15, max_value=100, value=35, step=1, help="No cambia el grupo.")
        annual_income_k = st.number_input(
            "Ingreso anual (miles de dólares)",
            min_value=0.0,
            max_value=500.0,
            value=70.0,
            help="70 significa unos 70.000 dólares al año.",
        )
        spending_score = st.number_input(
            "Ganas de comprar (1 a 100)",
            min_value=1.0,
            max_value=100.0,
            value=50.0,
            help="100 es quien más compra.",
        )
        submitted = st.form_submit_button("Ver a qué grupo pertenece")
    if submitted:
        try:
            result = controller.classify(
                {
                    "gender": gender,
                    "age": int(age),
                    "annual_income_k": float(annual_income_k),
                    "spending_score": float(spending_score),
                }
            )
        except CustomerValidationError as exc:
            st.error(ERROR_COPY.get(exc.code, exc.code))
        else:
            st.subheader(result["headline"])
            st.write(result["description"])
            st.write("Qué hacer: " + result["strategy"])
            distance = result["distance_to_centroid"]
            if distance < 0.35:
                st.write("Encaja de lleno en este grupo.")
            elif distance < 1:
                st.write("Está cerca del cliente típico de este grupo.")
            else:
                st.write("Queda hacia el borde del grupo. Conviene mirarlo con calma.")
            if result["outside_training_range"]:
                st.warning("Este cliente se sale de lo que ya hemos visto. El grupo es una aproximación.")
            history.insert(
                0,
                {
                    "Género": "Mujer" if gender == "Female" else "Hombre",
                    "Edad": int(age),
                    "Ingreso (miles)": float(annual_income_k),
                    "Ganas de comprar": float(spending_score),
                    "Grupo": result["headline"],
                },
            )
            del history[12:]
    if history:
        st.subheader("Historial de esta sesión")
        st.caption("Se guarda en la sesión de Streamlit. Si cierras la pestaña, se borra.")
        st.dataframe(pd.DataFrame(history), use_container_width=True, hide_index=True)


def _cluster_table(analysis: dict) -> pd.DataFrame:
    rows = []
    for cluster in analysis["clusters"]:
        rows.append(
            {
                "Grupo": cluster["headline"],
                "Clientes": cluster["size"],
                "Ingreso (miles)": round(cluster["centroid"]["annual_income_k"], 1),
                "Ganas de comprar": round(cluster["centroid"]["spending_score"], 1),
                "Edad media": round(cluster["mean_age"], 1),
            }
        )
    return pd.DataFrame(rows)


def _saved(analysis: dict, name: str, caption: str) -> None:
    path = FIGURES_DIR / f"{name}.png"
    if path.exists():
        st.image(str(path), caption=caption, use_container_width=True)
        return
    fallback = {
        "elbow": plot_elbow,
        "silhouette": plot_silhouette,
        "clusters": plot_clusters,
        "boxplots": plot_boxplots,
    }[name]
    _show(fallback(analysis))


def _show(figure) -> None:
    st.pyplot(figure)
    plt.close(figure)


def _css() -> None:
    st.markdown(
        """
        <style>
          .stApp { background: #FFF4EA; color: #2C1210; }
          .mango-kicker {
            color: #C2410C; font-size: 0.75rem; letter-spacing: 0.08em;
            text-transform: uppercase; margin-bottom: 0;
          }
          div[data-testid="stMetric"] {
            background: #FFFBF7; border: 1px solid #F0D9C8; border-radius: 14px; padding: 8px 12px;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
else:
    main()
