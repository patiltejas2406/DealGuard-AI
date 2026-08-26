"""Scenario Simulation Domain Models: What-If Scenarios & Monte Carlo Runs."""

import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.domains.common.models import TenantScopedModel
from app.domains.common.types import CompatibleJSON

if TYPE_CHECKING:
    from app.domains.auth.models import User
    from app.domains.deals.models import Deal


class Scenario(TenantScopedModel):
    """Derived scenario configuration and evaluated outputs for What-If deal simulation."""
    __tablename__ = "scenarios"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scenario_type: Mapped[str] = mapped_column(String(50), default="WHAT_IF", nullable=False)  # WHAT_IF, SENSITIVITY, DOWNSIDE, UPSIDE, STRESS_TEST
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)  # DRAFT, ACTIVE, COMPLETED, ARCHIVED

    # Structured Assumption Overlays & Evaluated Outputs
    assumptions: Mapped[dict] = mapped_column(CompatibleJSON, nullable=False)  # { "revenue_growth_delta_pct": -0.05, "ebitda_margin_delta_pct": -0.03, ... }
    results: Mapped[Optional[dict]] = mapped_column(CompatibleJSON, default=dict, nullable=True)  # Snapshot of recalculated financial, valuation, and decision metrics

    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    deal: Mapped["Deal"] = relationship("Deal", backref="scenarios")
    created_by: Mapped[Optional["User"]] = relationship("User")
    simulation_runs: Mapped[List["SimulationRun"]] = relationship(
        "SimulationRun", back_populates="scenario", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_scenarios_org_deal", "organization_id", "deal_id"),
        Index("ix_scenarios_deal_type", "deal_id", "scenario_type"),
    )


class SimulationRun(TenantScopedModel):
    """Statistical Monte Carlo simulation run or multi-dimensional parameter sweep."""
    __tablename__ = "simulation_runs"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scenario_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=True, index=True
    )
    simulation_type: Mapped[str] = mapped_column(String(50), default="MONTE_CARLO", nullable=False)  # MONTE_CARLO, SENSITIVITY_2D
    parameters: Mapped[dict] = mapped_column(CompatibleJSON, nullable=False)  # Distribution parameters, ranges, seeds
    iterations_count: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    random_seed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    statistics_output: Mapped[Optional[dict]] = mapped_column(CompatibleJSON, default=dict, nullable=True)  # Mean, p5-p95, band probabilities
    status: Mapped[str] = mapped_column(String(20), default="COMPLETED", nullable=False)  # QUEUED, RUNNING, COMPLETED, FAILED

    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    deal: Mapped["Deal"] = relationship("Deal", backref="simulation_runs")
    scenario: Mapped[Optional["Scenario"]] = relationship("Scenario", back_populates="simulation_runs")
    created_by: Mapped[Optional["User"]] = relationship("User")

    __table_args__ = (
        Index("ix_sim_runs_org_deal", "organization_id", "deal_id"),
        Index("ix_sim_runs_scenario", "scenario_id", "created_at"),
        Index("ix_sim_runs_status", "deal_id", "status"),
    )
