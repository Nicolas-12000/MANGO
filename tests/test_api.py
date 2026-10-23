"""HTTP adapter over the single segmentation controller."""

from fastapi.testclient import TestClient

from main import app


def test_analysis_and_classify() -> None:
    with TestClient(app) as client:
        health = client.get("/v1/health")
        assert health.status_code == 200
        assert health.json()["model_ready"] is True

        analysis = client.get("/v1/analysis")
        assert analysis.status_code == 200
        assert analysis.json()["selected_k"] == 5

        cluster = analysis.json()["clusters"][0]
        classified = client.post(
            "/v1/classify",
            json={
                "gender": "Female",
                "age": 35,
                "annual_income_k": cluster["centroid"]["annual_income_k"],
                "spending_score": cluster["centroid"]["spending_score"],
            },
        )
        assert classified.status_code == 200
        assert classified.json()["profile"] == cluster["profile"]

        rejected = client.post(
            "/v1/classify",
            json={"gender": "Female", "age": 35, "annual_income_k": 40, "spending_score": 140},
        )
        assert rejected.status_code == 422
        assert rejected.json()["detail"] == "spending_score_out_of_bounds"
