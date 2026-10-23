"""Streamlit deployment. Same screen as the Next dashboard, talking only to the controller."""

from __future__ import annotations

import textwrap
from html import escape

import matplotlib.pyplot as plt
import streamlit as st

from mango.constants import FIGURES_DIR, PROFILE_COLORS
from mango.content.assignment_guide import SECTIONS
from mango.interfaces.controller import CustomerValidationError, get_controller
from mango.visualization import plot_boxplots, plot_clusters, plot_elbow, plot_silhouette

ERROR_COPY = {
    "invalid_gender": "Elige mujer u hombre.",
    "invalid_age": "La edad tiene que ser un número entero.",
    "invalid_annual_income_k": "El ingreso tiene que ser un número.",
    "invalid_spending_score": "Las ganas de comprar tienen que ser un número.",
    "age_out_of_bounds": "La edad queda fuera de 15 a 100.",
    "annual_income_k_out_of_bounds": "El ingreso queda fuera de 0 a 500.",
    "spending_score_out_of_bounds": "Las ganas de comprar van de 1 a 100.",
}

@st.cache_resource
def load_controller():
    return get_controller()


def main() -> None:
    st.set_page_config(page_title="Mango", page_icon="🥭", layout="wide", initial_sidebar_state="collapsed")
    _css()
    controller = load_controller()
    analysis = controller.analysis()
    _header()
    _metrics(analysis)
    _method_figures(analysis)
    _figure(
        analysis,
        "boxplots",
        "Cómo se reparte cada variable",
        "Muestra el ingreso, las ganas de comprar y la edad, y marca los extremos.",
    )
    _clusters(analysis)
    _assignment_guide()
    _classify(controller)


def _html(markup: str) -> None:
    st.markdown(textwrap.dedent(markup).strip(), unsafe_allow_html=True)


def _header() -> None:
    emoji_col, text_col = st.columns([0.1, 0.9], gap="small", vertical_alignment="center")
    with emoji_col:
        _html('<p class="mango-emoji" aria-hidden="true">🥭</p>')
    with text_col:
        st.title("Mango")
        st.markdown(
            "Mira qué tipos de cliente tienes y prueba a cuál se parece alguien nuevo, "
            "antes de mandarle una campaña."
        )


def _metrics(analysis: dict) -> None:
    silhouette = f"{analysis['model_silhouette']:.2f}".replace(".", ",")
    cards = [
        ("Clientes", str(analysis["dataset"]["rows"]), "personas en la base", False),
        ("Grupos", str(analysis["selected_k"]), "así se separan mejor", False),
        ("Qué tan claros", silhouette, "1 sería una separación perfecta", False),
        ("Dónde crecer", analysis["growth_headline"], "el grupo con más margen por ganar", True),
    ]
    columns = st.columns(4)
    for column, (label, value, hint, compact) in zip(columns, cards, strict=True):
        with column:
            _html(
                f"""
                <article class="card metric">
                  <p class="label">{escape(label)}</p>
                  <p class="{'value-compact' if compact else 'value'}">{escape(value)}</p>
                  <p class="note">{escape(hint)}</p>
                </article>
                """
            )


def _method_figures(analysis: dict) -> None:
    selection = analysis["k_selection"]
    if selection["methods_agree"]:
        silhouette_note = (
            "Con 5 grupos la separación es la mejor, y coincide con la curva de al lado."
        )
    else:
        silhouette_note = f"La separación más alta está en {selection['silhouette_k']} grupos."
    left, right = st.columns(2)
    with left:
        _figure(
            analysis,
            "elbow",
            "Cuántos grupos conviene usar",
            "La curva baja rápido y luego se aplana. El doblez, en 5, es donde partir más ya no aporta.",
        )
    with right:
        _figure(analysis, "silhouette", "Qué tan nítido queda cada corte", silhouette_note)


def _clusters(analysis: dict) -> None:
    with st.container(border=True):
        _html(
            """
            <h2 class="panel-title">Los cinco tipos de cliente</h2>
            <p class="note">Cada punto es una persona. A la derecha, quién compra más. Arriba en ingreso, quién puede gastar más. La cruz marca el cliente típico del grupo.</p>
            """
        )
        _image(analysis, "clusters")
    legend = "".join(
        f'<li><span style="background:{PROFILE_COLORS[cluster["profile"]]}"></span>{escape(cluster["headline"])}</li>'
        for cluster in analysis["clusters"]
    )
    st.markdown(f'<ul class="legend">{legend}</ul>', unsafe_allow_html=True)
    columns = st.columns(2)
    for index, cluster in enumerate(analysis["clusters"]):
        income = _money(cluster["centroid"]["annual_income_k"])
        score = round(cluster["centroid"]["spending_score"])
        color = PROFILE_COLORS[cluster["profile"]]
        with columns[index % 2]:
            _html(
                f"""
                <article class="card profile" style="border-left-color:{color}">
                  <h3>{escape(cluster["headline"])}</h3>
                  <p class="note">{cluster["size"]} clientes · {escape(income)} al año · compran {score} de 100</p>
                  <p class="note">{escape(cluster["description"])}</p>
                  <p class="action"><strong>Qué hacer: </strong>{escape(cluster["strategy"])}</p>
                </article>
                """
            )


def _assignment_guide() -> None:
    st.markdown("## Preguntas del análisis")
    st.markdown(
        "Si estás mirando los grupos y quieres saber **cómo llegamos aquí**, estas son las respuestas "
        "del taller de segmentación con K-Means."
    )
    for section in SECTIONS:
        label = f"{section['part']} — {section['title']}"
        with st.expander(label, expanded=False):
            for item in section["items"]:
                st.markdown(f"**{item['question']}**")
                st.markdown(item["answer"])
                st.divider()


def _classify(controller) -> None:
    history = st.session_state.setdefault("classification_history", [])
    form_col, result_col = st.columns(2)
    with form_col:
        with st.container(border=True):
            st.markdown('<h2 class="panel-title">Probar un cliente</h2>', unsafe_allow_html=True)
            st.markdown(
                '<p class="note">La edad y el género nos ayudan a imaginarlo. El grupo lo deciden el ingreso y las ganas de comprar.</p>',
                unsafe_allow_html=True,
            )
            with st.form("classify_customer"):
                gender = st.selectbox(
                    "Género",
                    ["Female", "Male"],
                    format_func=lambda value: "Mujer" if value == "Female" else "Hombre",
                )
                age = st.number_input("Edad", min_value=15, max_value=100, value=35, step=1, help="Años cumplidos.")
                annual_income_k = st.number_input(
                    "Ingreso anual",
                    min_value=0.0,
                    max_value=500.0,
                    value=70.0,
                    help="En miles de dólares. 70 significa unos US$ 70.000 al año.",
                )
                spending_score = st.number_input(
                    "Ganas de comprar",
                    min_value=1.0,
                    max_value=100.0,
                    value=50.0,
                    help="De 1 a 100. 100 es quien más compra en la tienda.",
                )
                submitted = st.form_submit_button("Ver a qué grupo pertenece", type="primary", use_container_width=True)
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
                st.session_state["classification_error"] = ERROR_COPY.get(exc.code, exc.code)
            else:
                st.session_state["classification_error"] = None
                st.session_state["last_classification"] = result
                history.insert(
                    0,
                    {
                        "gender": "Mujer" if gender == "Female" else "Hombre",
                        "age": int(age),
                        "annual_income_k": float(annual_income_k),
                        "spending_score": float(spending_score),
                        "headline": result["headline"],
                        "profile": result["profile"],
                    },
                )
                del history[12:]
        if st.session_state.get("classification_error"):
            st.error(st.session_state["classification_error"])

    with result_col:
        result = st.session_state.get("last_classification")
        if result:
            color = PROFILE_COLORS[result["profile"]]
            outside = ""
            if result["outside_training_range"]:
                outside = (
                    f'<p class="warn">{escape(_outside_range(result["outside_training_range"]))} '
                    "El grupo es una aproximación.</p>"
                )
            _html(
                f"""
                <article class="card result">
                  <h2>Su grupo</h2>
                  <p class="result-name" style="color:{color}">{escape(result["headline"])}</p>
                  <p class="body">{escape(result["description"])}</p>
                  <p class="body"><strong>Qué hacer: </strong>{escape(result["strategy"])}</p>
                  <p class="note">{escape(_fit_label(result["distance_to_centroid"]))}</p>
                  {outside}
                </article>
                """
            )
        else:
            _html(
                """
                <article class="card result">
                  <h2>Su grupo</h2>
                  <p class="body">Escribe a alguien que todavía no está en la base. Te diremos a quién se parece y qué campaña le queda mejor.</p>
                </article>
                """
            )

    if history:
        rows = "".join(
            f"""
            <li>
              <span>{escape(item["gender"])}, {item["age"]} años · ingreso {item["annual_income_k"]:g} mil · compra {item["spending_score"]:g}</span>
              <strong style="color:{PROFILE_COLORS[item["profile"]]}">{escape(item["headline"])}</strong>
            </li>
            """
            for item in history
        )
        _html(
            f"""
            <section class="card history">
              <h2>Consultas guardadas</h2>
              <p class="note">Quedan en esta sesión. Si cierras la pestaña, se borra.</p>
              <ul>{rows}</ul>
            </section>
            """
        )


def _figure(analysis: dict, name: str, title: str, note: str) -> None:
    with st.container(border=True):
        st.markdown(f'<p class="label">{escape(title)}</p>', unsafe_allow_html=True)
        _image(analysis, name)
        st.markdown(f'<p class="note">{escape(note)}</p>', unsafe_allow_html=True)


def _image(analysis: dict, name: str) -> None:
    path = FIGURES_DIR / f"{name}.png"
    if path.exists():
        st.image(str(path), use_container_width=True)
        return
    fallback = {
        "elbow": plot_elbow,
        "silhouette": plot_silhouette,
        "clusters": plot_clusters,
        "boxplots": plot_boxplots,
    }[name]
    figure = fallback(analysis)
    st.pyplot(figure)
    plt.close(figure)


def _money(thousands: float) -> str:
    amount = round(thousands * 1000)
    grouped = f"{amount:,}".replace(",", ".")
    return f"US$ {grouped}"


def _fit_label(distance: float) -> str:
    if distance < 0.35:
        return "Encaja de lleno en este grupo."
    if distance < 1:
        return "Está cerca del cliente típico de este grupo."
    return "Queda hacia el borde del grupo. Conviene mirarlo con calma."


def _outside_range(fields: list[str]) -> str:
    names = ["el ingreso" if field == "annual_income_k" else "las ganas de comprar" for field in fields]
    return f"No tenemos clientes con {' ni '.join(names)} tan extremos."


def _css() -> None:
    st.markdown(
        """
        <style>
          @import url("https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=IBM+Plex+Mono:wght@500&family=IBM+Plex+Sans:wght@400;600&display=swap");
          html, body, [class*="css"] { font-family: "IBM Plex Sans", system-ui, sans-serif; }
          .stApp { background: #FFF4EA; color: #2C1210; }
          header[data-testid="stHeader"], #MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none; }
          .block-container { max-width: 72rem; padding-top: 2rem; padding-bottom: 4rem; }
          h1, h2, h3, .panel-title {
            font-family: Fraunces, Georgia, serif;
            font-weight: 600;
            letter-spacing: -0.02em;
            color: #2C1210;
            margin: 0;
          }
          .mango-emoji { font-size: 3.25rem; line-height: 1; margin: 0; }
          h1 { font-size: 2.75rem !important; line-height: 1 !important; letter-spacing: -0.03em !important; padding-top: 0 !important; }
          .block-container p { color: #5C3A2E; }
          .body { color: #5C3A2E; font-size: 1rem; line-height: 1.6; max-width: 36rem; margin: 0.75rem 0 0; }
          .card {
            background: #FFFBF7;
            border: 1px solid #F0D9C8;
            border-radius: 14px;
            padding: 1rem 1.1rem 1.15rem;
            margin-bottom: 0.75rem;
          }
          .label {
            font-family: "IBM Plex Mono", ui-monospace, monospace;
            font-size: 0.6875rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #5C3A2E;
            margin: 0;
          }
          .value, .value-compact {
            font-family: "IBM Plex Mono", ui-monospace, monospace;
            color: #2C1210;
            margin: 0.45rem 0 0;
            line-height: 1;
          }
          .value { font-size: 2.5rem; }
          .value-compact { font-family: Fraunces, Georgia, serif; font-size: 1.5rem; font-weight: 600; }
          .note { color: #5C3A2E; font-size: 0.875rem; line-height: 1.5; margin: 0.55rem 0 0; }
          .figure { margin-bottom: 0.35rem; padding-bottom: 0.4rem; }
          .figure-note { margin-top: 0; margin-bottom: 1rem; }
          .cluster-intro h2, .profile h3, .result h2, .history h2 { font-size: 1.5rem; }
          .profile { border-left: 4px solid #C2410C; min-height: 11rem; }
          .action { font-size: 0.875rem; margin: 0.55rem 0 0; }
          .legend { display: flex; flex-wrap: wrap; gap: 0.75rem 1.25rem; list-style: none; padding: 0.25rem 0 1rem; margin: 0; }
          .legend li { display: flex; align-items: center; gap: 0.45rem; color: #5C3A2E; font-size: 0.875rem; }
          .legend span { width: 0.7rem; height: 0.7rem; border-radius: 999px; display: inline-block; }
          .result-name {
            font-family: "IBM Plex Mono", ui-monospace, monospace;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-size: 0.8rem;
            margin: 1rem 0 0;
          }
          .warn { color: #9F1239; font-size: 0.875rem; margin-top: 0.75rem; }
          .history ul { list-style: none; padding: 0; margin: 0.8rem 0 0; }
          .history li {
            display: flex; justify-content: space-between; gap: 1rem; flex-wrap: wrap;
            border-bottom: 1px solid #F0D9C8; padding: 0.55rem 0; font-size: 0.875rem;
          }
          div[data-testid="stVerticalBlockBorderWrapper"] {
            background: #FFFBF7;
            border: 1px solid #F0D9C8 !important;
            border-radius: 14px;
            padding: 0.4rem 0.8rem 0.8rem;
          }
          div[data-testid="stForm"] { border: 0; padding: 0; }
          .stTextInput input, .stNumberInput input, div[data-baseweb="select"] > div {
            background: #FFFBF7;
            border-color: #F0D9C8;
            color: #2C1210;
            min-height: 3rem;
            border-radius: 8px;
          }
          .stFormSubmitButton button {
            background: #C2410C;
            color: #FFFFFF;
            border: 0;
            border-radius: 8px;
            min-height: 3rem;
            font-weight: 600;
          }
          .stFormSubmitButton button:hover { background: #9A3412; color: #FFFFFF; }
          [data-testid="stImage"] img { border-radius: 8px; background: #FFF4EA; }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
else:
    main()
