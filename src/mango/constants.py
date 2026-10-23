"""Paths and column names. Every identifier here is English."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_CSV_PATH = PROJECT_ROOT / "data" / "raw" / "Mall_Customers.csv"
PROCESSED_CSV_PATH = PROJECT_ROOT / "data" / "processed" / "customers.csv"
MODELS_DIR = PROJECT_ROOT / "models"
ARTIFACT_PATH = MODELS_DIR / "segmentation.joblib"
FIGURES_DIR = PROJECT_ROOT / "report" / "figures"
ANALYSIS_PATH = PROJECT_ROOT / "report" / "analysis.json"
TREATMENT_REPORT_PATH = PROJECT_ROOT / "report" / "data_treatment.md"
FRONTEND_BUNDLE_PATH = PROJECT_ROOT / "frontend" / "public" / "analysis.json"

RANDOM_STATE = 42
K_RANGE = range(1, 11)
SILHOUETTE_K_RANGE = range(2, 11)
N_INIT = 10

# Source headers from the Kaggle file, renamed on load.
COLUMN_MAP = {
    "CustomerID": "customer_id",
    "Gender": "gender",
    "Age": "age",
    "Annual Income (k$)": "annual_income_k",
    "Spending Score (1-100)": "spending_score",
}

IDENTIFIER_COLUMN = "customer_id"
CATEGORICAL_COLUMNS = ("gender",)
NUMERIC_COLUMNS = ("age", "annual_income_k", "spending_score")
SEGMENT_FEATURES = ("annual_income_k", "spending_score")

FEATURE_SETS = (
    ("annual_income_k", "spending_score"),
    ("age", "spending_score"),
    ("age", "annual_income_k"),
    ("age", "annual_income_k", "spending_score"),
)

# Values outside these bounds cannot be a real mall member. They are capture errors.
HARD_BOUNDS = {
    "age": (15, 100),
    "annual_income_k": (0, 500),
    "spending_score": (1, 100),
}
ALLOWED_GENDERS = ("Female", "Male")

# Tukey fence (box-plot convention) and Iglewicz–Hoaglin modified z-score.
IQR_MULTIPLIER = 1.5
MODIFIED_Z_THRESHOLD = 3.5
MAHALANOBIS_ALPHA = 0.975

# If the preferred pair is within this silhouette gap of the best set, keep it:
# income and spending score are the variables marketing can act on.
SILHOUETTE_TOLERANCE = 0.02
# Silhouette must beat the elbow's silhouette by more than this to override it.
K_SILHOUETTE_GAP = 0.02

PROFILE_COLORS = {
    "high_value": "#C2410C",
    "potential": "#9A3412",
    "average": "#C4841D",
    "low_value": "#6B2D3C",
    "budget_constrained": "#D4673A",
}

PALETTE = {
    "ink": "#2C1210",
    "paper": "#FFF4EA",
    "surface": "#FFFBF7",
    "outline": "#F0D9C8",
    "mango": "#C2410C",
    "pulp": "#E09F3E",
    "leaf": "#3F6B2A",
}
