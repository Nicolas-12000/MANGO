"""FastAPI entrypoint created by `fastapi-new` and wired to the segmentation controller."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from mango.interfaces.controller import (
    CustomerValidationError,
    SegmentationController,
    get_controller,
)


def _origins() -> list[str]:
    raw = os.getenv("MANGO_CORS_ORIGINS", "http://localhost:3000")
    return [item.strip() for item in raw.split(",") if item.strip()]


def _prefix() -> str:
    return os.getenv("MANGO_API_V1_PREFIX", "/v1")


class CustomerRequest(BaseModel):
    gender: str = Field(examples=["Female"])
    age: int = Field(examples=[35])
    annual_income_k: float = Field(examples=[70])
    spending_score: float = Field(examples=[80])


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.controller = get_controller()
    yield


app = FastAPI(
    title="Mango",
    description="Customer segmentation with K-Means.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _controller(request: Request) -> SegmentationController:
    return request.app.state.controller


@app.exception_handler(CustomerValidationError)
async def validation_handler(_request: Request, exc: CustomerValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": exc.code})


@app.get("/")
def root() -> dict[str, str]:
    prefix = _prefix()
    return {"name": "Mango", "health": f"{prefix}/health", "docs": "/docs"}


@app.get("/v1/health")
def health(request: Request) -> dict[str, Any]:
    return _controller(request).health()


@app.get("/v1/analysis")
def analysis(request: Request) -> dict[str, Any]:
    return _controller(request).analysis()


@app.post("/v1/classify")
def classify(body: CustomerRequest, request: Request) -> dict[str, Any]:
    return _controller(request).classify(body.model_dump())
