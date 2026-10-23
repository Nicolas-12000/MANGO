"""The only controller. Streamlit, the notebook, and FastAPI all call this object."""

from __future__ import annotations

from typing import Any

from mango.constants import ALLOWED_GENDERS, ARTIFACT_PATH, HARD_BOUNDS
from mango.orchestration.pipeline import SegmentationOrchestrator


class CustomerValidationError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class SegmentationController:
    def __init__(self, orchestrator: SegmentationOrchestrator) -> None:
        self.orchestrator = orchestrator

    def health(self) -> dict[str, Any]:
        analysis = self.orchestrator.analysis
        return {
            "status": "ok" if analysis is not None else "empty",
            "app": "Mango",
            "model_ready": analysis is not None,
            "selected_k": None if analysis is None else analysis["selected_k"],
        }

    def analysis(self) -> dict[str, Any]:
        if self.orchestrator.analysis is None:
            self.orchestrator.fit()
        assert self.orchestrator.analysis is not None
        return self.orchestrator.analysis

    def classify(self, customer: dict[str, Any]) -> dict[str, Any]:
        self.validate_customer(customer)
        return self.orchestrator.classify(customer)

    def validate_customer(self, customer: dict[str, Any]) -> None:
        gender = customer.get("gender")
        if gender not in ALLOWED_GENDERS:
            raise CustomerValidationError("invalid_gender")
        _require_number(customer.get("age"), "age", integer=True)
        _require_number(customer.get("annual_income_k"), "annual_income_k")
        _require_number(customer.get("spending_score"), "spending_score")
        for field, (lower, upper) in HARD_BOUNDS.items():
            value = float(customer[field])
            if value < lower or value > upper:
                raise CustomerValidationError(f"{field}_out_of_bounds")


def get_controller() -> SegmentationController:
    orchestrator = SegmentationOrchestrator()
    if ARTIFACT_PATH.exists():
        orchestrator.load()
    else:
        orchestrator.fit()
    return SegmentationController(orchestrator)


def _require_number(value: Any, field: str, integer: bool = False) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CustomerValidationError(f"invalid_{field}")
    if integer and not isinstance(value, int):
        raise CustomerValidationError(f"invalid_{field}")
