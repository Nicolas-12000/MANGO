# Mango

Segmentación de clientes del centro comercial con K-Means. Un monolito: el cálculo vive en `src/mango`, lo ordena un orquestador y lo expone un solo controller. FastAPI, Streamlit y el cuaderno son adaptadores.

El proyecto de Python salió de `uvx fastapi-new`. El frontend salió de `create-next-app`.

## Qué no entra a git

`.gitignore` deja fuera el entorno (`.venv/`), cachés de pytest y ruff, secretos (`.env`, `.streamlit/secrets.toml`) y el build de Next (`frontend/node_modules/`, `frontend/.next/`). Sí se versionan `uv.lock`, `frontend/pnpm-lock.yaml`, el modelo en `models/` y `frontend/public/analysis.json`. La plantilla está en `.env.example` y `frontend/.env.example`.

## Datos y modelo

Las columnas del CSV se renombran a `customer_id`, `gender`, `age`, `annual_income_k` y `spending_score`. El modelo usa solo ingreso y spending score. K = 5: coinciden el codo y la silueta (0.555).

```bash
uv sync
uv run python scripts/train_model.py
uv run pytest -q
```

Cuaderno: `notebooks/01_segmentacion_kmeans.ipynb`.

## API

```bash
uv run fastapi dev
```

- `GET /v1/analysis`
- `POST /v1/classify` con `gender`, `age`, `annual_income_k`, `spending_score`
- Docs: http://localhost:8000/docs

## Streamlit

```bash
uv run streamlit run streamlit_app.py
```

Muestra el codo, los clusters y clasifica un cliente nuevo.

## Web

```bash
cd frontend
pnpm install
pnpm dev
```

http://localhost:3000. Si la API no responde, la pantalla usa `frontend/public/analysis.json`. Diseño: [frontend/DESIGN.md](frontend/DESIGN.md).
