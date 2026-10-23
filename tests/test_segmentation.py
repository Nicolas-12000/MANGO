"""Pipeline, quality policy, and the single controller."""

import pandas as pd
import pytest

from mango.data.quality import load_customers, screen_customers
from mango.interfaces.controller import CustomerValidationError, SegmentationController
from mango.orchestration.pipeline import SegmentationOrchestrator


@pytest.fixture(scope="module")
def controller() -> SegmentationController:
    return SegmentationController(SegmentationOrchestrator())


def test_capture_error_is_removed_and_real_tail_stays() -> None:
    raw = load_customers()
    extra = raw.iloc[[0]].copy()
    extra["customer_id"] = 9999
    extra["spending_score"] = 500
    ready, report = screen_customers(pd.concat([raw, extra], ignore_index=True))

    assert report["rows_removed"] == 1
    assert 9999 not in set(ready["customer_id"])
    assert 200 in set(ready["customer_id"])
    income_fence = report["iqr_fences"]["annual_income_k"]
    assert income_fence["count"] >= 1
    assert ready.loc[ready["annual_income_k"] > income_fence["upper"], "customer_id"].tolist()


def test_mall_file_has_no_capture_errors(controller: SegmentationController) -> None:
    analysis = controller.analysis()
    quality = analysis["quality"]

    assert quality["rows_ready"] == 200
    assert quality["rows_removed"] == 0
    assert quality["duplicate_rows"] == 0
    assert quality["removal_policy"] == "capture_errors_only"
    assert analysis["feature_selection"]["selected_features"] == ["annual_income_k", "spending_score"]
    assert "customer_id" not in analysis["scaling"]["features"]
    assert "gender" not in analysis["scaling"]["features"]


def test_k_and_profiles(controller: SegmentationController) -> None:
    analysis = controller.analysis()

    assert analysis["k_selection"]["methods_agree"] is True
    assert analysis["selected_k"] == 5
    assert analysis["model_silhouette"] > 0.5
    assert {cluster["profile"] for cluster in analysis["clusters"]} == {
        "high_value",
        "potential",
        "average",
        "budget_constrained",
        "low_value",
    }
    assert analysis["growth_opportunity"] == "potential"


def test_centroid_classifies_as_its_own_profile(controller: SegmentationController) -> None:
    for cluster in controller.analysis()["clusters"]:
        result = controller.classify(
            {
                "gender": "Female",
                "age": 35,
                "annual_income_k": cluster["centroid"]["annual_income_k"],
                "spending_score": cluster["centroid"]["spending_score"],
            }
        )
        assert result["profile"] == cluster["profile"]
        assert result["features_ignored"] == ["gender", "age"]


def test_rejects_impossible_spending_score(controller: SegmentationController) -> None:
    with pytest.raises(CustomerValidationError) as caught:
        controller.classify(
            {"gender": "Male", "age": 30, "annual_income_k": 60, "spending_score": 140}
        )
    assert caught.value.code == "spending_score_out_of_bounds"
