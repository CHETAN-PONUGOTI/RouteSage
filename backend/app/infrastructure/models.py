from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.domain.models.enums import (
    CargoType,
    FeasibilityStatus,
    RiskCategory,
    ShipmentPriority,
    TransportMode,
)
from app.infrastructure.database import Base


class ShipmentModel(Base):
    __tablename__ = "shipments"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    origin: Mapped[str] = mapped_column(String, nullable=False)
    destination: Mapped[str] = mapped_column(String, nullable=False)
    cargo_type: Mapped[CargoType] = mapped_column(SAEnum(CargoType), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    shipment_value: Mapped[float] = mapped_column(Float, nullable=False)
    delivery_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    priority: Mapped[ShipmentPriority] = mapped_column(SAEnum(ShipmentPriority), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RouteModel(Base):
    __tablename__ = "routes"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    shipment_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("shipments.id"), nullable=False)
    route_name: Mapped[str] = mapped_column(String, nullable=False)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False)
    transit_time: Mapped[float] = mapped_column(Float, nullable=False)
    delay_probability: Mapped[float] = mapped_column(Float, nullable=False)
    reliability: Mapped[float] = mapped_column(Float, nullable=False)
    aggregate_risk: Mapped[float] = mapped_column(Float, nullable=False)
    feasibility_status: Mapped[FeasibilityStatus] = mapped_column(SAEnum(FeasibilityStatus), nullable=False)
    violated_constraints: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    legs: Mapped[list["RouteLegModel"]] = relationship("RouteLegModel", back_populates="route", cascade="all, delete-orphan", order_by="RouteLegModel.sequence")


class RouteLegModel(Base):
    __tablename__ = "route_legs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    route_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("routes.id"), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    origin: Mapped[str] = mapped_column(String, nullable=False)
    destination: Mapped[str] = mapped_column(String, nullable=False)
    transport_mode: Mapped[TransportMode] = mapped_column(SAEnum(TransportMode), nullable=False)
    duration: Mapped[float] = mapped_column(Float, nullable=False)
    cost: Mapped[float] = mapped_column(Float, nullable=False)

    route: Mapped["RouteModel"] = relationship("RouteModel", back_populates="legs")
    risk_factors: Mapped[list["RiskFactorModel"]] = relationship("RiskFactorModel", back_populates="leg", cascade="all, delete-orphan")


class RiskFactorModel(Base):
    __tablename__ = "risk_factors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    leg_id: Mapped[int] = mapped_column(Integer, ForeignKey("route_legs.id"), nullable=False)
    category: Mapped[RiskCategory] = mapped_column(SAEnum(RiskCategory), nullable=False)
    severity: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)

    leg: Mapped["RouteLegModel"] = relationship("RouteLegModel", back_populates="risk_factors")


class OptimizationProfileModel(Base):
    __tablename__ = "optimization_profiles"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    cost_weight: Mapped[float] = mapped_column(Float, nullable=False)
    time_weight: Mapped[float] = mapped_column(Float, nullable=False)
    reliability_weight: Mapped[float] = mapped_column(Float, nullable=False)
    risk_weight: Mapped[float] = mapped_column(Float, nullable=False)


class OptimizationRunModel(Base):
    __tablename__ = "optimization_runs"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    shipment_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("shipments.id"), nullable=False)
    profile_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("optimization_profiles.id"), nullable=False)
    recommended_route_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("routes.id"), nullable=True)
    
    # Store dynamic analysis fields via JSON for simpler querying without complex relational overhead
    feasible_routes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    infeasible_routes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    route_scores: Mapped[dict[str, float]] = mapped_column(JSON, nullable=False, default=dict)
    score_breakdown: Mapped[dict[str, dict[str, float]]] = mapped_column(JSON, nullable=False, default=dict)
    constraint_results: Mapped[dict[str, list[str]]] = mapped_column(JSON, nullable=False, default=dict)
    tradeoffs: Mapped[dict[str, list[str]]] = mapped_column(JSON, nullable=False, default=dict)
    sensitivity: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    
    execution_time_ms: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    shipment: Mapped["ShipmentModel"] = relationship("ShipmentModel")
    profile: Mapped["OptimizationProfileModel"] = relationship("OptimizationProfileModel")
    recommended_route: Mapped[Optional["RouteModel"]] = relationship("RouteModel")
