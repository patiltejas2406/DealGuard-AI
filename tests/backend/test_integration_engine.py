"""Comprehensive Test Suite for Phase 11: 100-Day Integration Execution & Workstream Planning Engine."""

import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token, hash_password
from app.domains.auth.models import Organization, OrganizationMembership, Role, User
from app.domains.deals.models import Deal, DealMember, TargetCompany
from app.domains.integration.config import (
    IntegrationHealthBand,
    WorkstreamStatus,
    get_100day_stage,
    validate_workstream_transition,
)
from app.domains.integration.dag import compute_critical_path, validate_dependency_graph
from app.domains.integration.executive_attention import generate_executive_attention_queue
from app.domains.integration.health import calculate_integration_health_score


# ==========================================
# 1. Deterministic DAG & Algorithm Tests
# ==========================================

def test_dag_cycle_and_self_dependency_detection():
    """Verify DAG engine blocks self-dependencies and circular dependency loops."""
    m1 = uuid.uuid4()
    m2 = uuid.uuid4()
    m3 = uuid.uuid4()

    # Self-dependency
    with pytest.raises(ValueError, match="Self-dependency detected"):
        validate_dependency_graph([], m1, m1)

    # Valid chain: m1 -> m2 -> m3
    deps = [
        {"predecessor_id": m1, "successor_id": m2},
        {"predecessor_id": m2, "successor_id": m3},
    ]
    validate_dependency_graph(deps, m1, m2)  # already in, no cycle

    # Circular loop: adding m3 -> m1
    with pytest.raises(ValueError, match="Circular dependency detected"):
        validate_dependency_graph(deps, m3, m1)


def test_deterministic_critical_path():
    """Verify longest-path critical path identification on milestone graphs."""
    class MockMilestone:
        def __init__(self, mid, name, day, status="NOT_STARTED"):
            self.id = mid
            self.name = name
            self.target_day = day
            self.status = status
            self.priority = "HIGH"

    class MockDep:
        def __init__(self, pred, succ):
            self.predecessor_id = pred
            self.successor_id = succ

    m1 = uuid.uuid4()  # Day 10
    m2 = uuid.uuid4()  # Day 30
    m3 = uuid.uuid4()  # Day 60 (Long branch)
    m4 = uuid.uuid4()  # Day 15 (Short branch)

    milestones = [
        MockMilestone(m1, "Day 1 Close", 10),
        MockMilestone(m2, "ERP Data Migration", 30),
        MockMilestone(m3, "Consolidated Reporting", 60),
        MockMilestone(m4, "Branding Launch", 15),
    ]

    dependencies = [
        MockDep(m1, m2),
        MockDep(m2, m3),
        MockDep(m1, m4),
    ]

    cp = compute_critical_path(milestones, dependencies)
    assert cp["longest_chain_length"] == 3
    assert cp["critical_path_duration_days"] == 10 + 30 + 60
    assert str(m1) in cp["critical_path_milestone_ids"]
    assert str(m2) in cp["critical_path_milestone_ids"]
    assert str(m3) in cp["critical_path_milestone_ids"]


def test_integration_health_score_calculation():
    """Verify deterministic health score formula, penalty deductions, and health bands."""
    class MockWorkstream:
        status = "IN_PROGRESS"

    class MockMilestone:
        def __init__(self, day, status, comp, syn_id=None):
            self.target_day = day
            self.status = status
            self.completion_pct = comp
            self.linked_synergy_id = syn_id

    class MockBlocker:
        def __init__(self, status, sev):
            self.status = status
            self.severity = sev

    # 1. Clean on-track execution
    clean_ms = [
        MockMilestone(20, "COMPLETED", 100.0),
        MockMilestone(40, "IN_PROGRESS", 40.0),
    ]
    h1 = calculate_integration_health_score([MockWorkstream()], clean_ms, [], current_day_offset=25)
    assert h1["health_score"] == 100.0
    assert h1["health_band"] == IntegrationHealthBand.HEALTHY.value

    # 2. Overdue + Critical Blocker penalties
    troubled_ms = [
        MockMilestone(15, "OVERDUE", 20.0),
        MockMilestone(20, "BLOCKED", 0.0),
    ]
    troubled_blockers = [
        MockBlocker("OPEN", "CRITICAL"),
    ]
    h2 = calculate_integration_health_score([MockWorkstream()], troubled_ms, troubled_blockers, current_day_offset=25)
    # Deductions: overdue (6.0) + critical blocker (15.0) + blocked milestone (5.0) = 26.0 -> 74.0 score
    assert h2["health_score"] <= 75.0
    assert h2["health_band"] == IntegrationHealthBand.WATCH.value


def test_workstream_lifecycle_state_machine():
    """Verify valid and invalid workstream state transitions."""
    # Valid
    validate_workstream_transition(WorkstreamStatus.NOT_STARTED.value, WorkstreamStatus.PLANNED.value)
    validate_workstream_transition(WorkstreamStatus.PLANNED.value, WorkstreamStatus.IN_PROGRESS.value)
    validate_workstream_transition(WorkstreamStatus.IN_PROGRESS.value, WorkstreamStatus.COMPLETED.value)

    # Invalid
    with pytest.raises(ValueError, match="Illegal workstream transition"):
        validate_workstream_transition(WorkstreamStatus.NOT_STARTED.value, WorkstreamStatus.COMPLETED.value)


def test_executive_attention_queue():
    """Verify prioritization of critical path bottlenecks and open blockers."""
    class MockWS:
        id = uuid.uuid4()
        name = "Finance Integration"
        category = "FINANCE_ACCOUNTING"
        status = "IN_PROGRESS"

    class MockMS:
        id = uuid.uuid4()
        name = "General Ledger Cutover"
        workstream_id = MockWS.id
        status = "OVERDUE"
        target_day = 20
        completion_pct = 30.0
        owner = "Sarah Jenkins"

    class MockBlocker:
        id = uuid.uuid4()
        title = "ERP Database Access Denied"
        description = "Target vendor has not provided root DB credentials"
        workstream_id = MockWS.id
        milestone_id = MockMS.id
        severity = "CRITICAL"
        status = "OPEN"
        owner = "Dave Miller"

    queue = generate_executive_attention_queue(
        workstreams=[MockWS()],
        milestones=[MockMS()],
        blockers=[MockBlocker()],
        critical_path_milestone_ids=[str(MockMS.id)],
        current_day_offset=30,
    )

    assert queue["critical_count"] >= 1
    assert queue["total_attention_items"] >= 2


# ==========================================
# 2. Database & API Integration Tests
# ==========================================

@pytest_asyncio.fixture
async def seed_integration_env(db_session: AsyncSession):
    """Seed deal workspace with target company and integration manager."""
    org = Organization(name="Blackstone Flagship", slug="blackstone-flagship", tier="ENTERPRISE")
    db_session.add(org)
    await db_session.flush()

    role = Role(name="ANALYST", description="Integration Lead", permissions={"all": True})
    db_session.add(role)
    await db_session.flush()

    user = User(
        email="integration.director@blackstone.demo",
        hashed_password=hash_password("SecurePass123!"),
        full_name="Steve Schwarzman",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    membership = OrganizationMembership(
        organization_id=org.id,
        user_id=user.id,
        role_id=role.id,
    )
    db_session.add(membership)
    await db_session.flush()

    target = TargetCompany(
        organization_id=org.id,
        name="Nexus Systems",
        industry="Enterprise Cybersecurity",
    )
    db_session.add(target)
    await db_session.flush()

    deal = Deal(
        organization_id=org.id,
        target_company_id=target.id,
        title="Project Nexus 100-Day Integration",
        target_ev=120000000.0,
        currency="USD",
        created_by_id=user.id,
    )
    db_session.add(deal)
    await db_session.flush()

    db_session.add(DealMember(
        organization_id=org.id,
        deal_id=deal.id,
        user_id=user.id,
        deal_role="LEAD",
    ))
    await db_session.commit()

    token = create_access_token(subject=str(user.id), org_id=str(org.id), role="ANALYST")
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org.id)}

    return {
        "org": org,
        "user": user,
        "deal": deal,
        "headers": headers,
    }


@pytest.mark.asyncio
async def test_integration_api_full_workflow(seed_integration_env, async_client: AsyncClient):
    """Verify complete 100-Day Integration API workflow: program init, workstreams, milestones, DAG, blockers, health."""
    env = seed_integration_env
    deal_id = env["deal"].id
    headers = env["headers"]

    # 1. Initialize 100-Day Program
    init_res = await async_client.post(
        f"/api/v1/deals/{deal_id}/integration",
        headers=headers,
        json={
            "name": "Project Nexus 100-Day Value Plan",
            "current_day_offset": 15,
            "executive_sponsor": "Steve Schwarzman",
            "objectives": {"key_goal": "Consolidate ERP and retain top 50 accounts"},
        },
    )
    assert init_res.status_code == 201
    prog_data = init_res.json()
    assert prog_data["health_score"] == 100.0
    assert prog_data["current_day_offset"] == 15

    # 2. Create Workstream
    ws_res = await async_client.post(
        f"/api/v1/deals/{deal_id}/integration/workstreams",
        headers=headers,
        json={
            "name": "Technology & Cybersecurity Integration",
            "category": "CYBERSECURITY",
            "priority": "CRITICAL",
            "owner": "Alex Rivera (CISO)",
            "start_day": 1,
            "target_day": 60,
        },
    )
    assert ws_res.status_code == 201
    ws_data = ws_res.json()
    ws_id = ws_data["id"]
    assert ws_data["category"] == "CYBERSECURITY"

    # 3. Create Milestones
    m1_res = await async_client.post(
        f"/api/v1/deals/{deal_id}/integration/milestones",
        headers=headers,
        json={
            "workstream_id": ws_id,
            "name": "Single Sign-On (SSO) & IAM Rollout",
            "target_day": 20,
            "priority": "CRITICAL",
            "owner": "Alex Rivera",
            "deliverable": "Okta federation across all acquired employees",
        },
    )
    assert m1_res.status_code == 201
    m1_id = m1_res.json()["id"]

    m2_res = await async_client.post(
        f"/api/v1/deals/{deal_id}/integration/milestones",
        headers=headers,
        json={
            "workstream_id": ws_id,
            "name": "SOC2 Compliance Harmonization",
            "target_day": 45,
            "priority": "HIGH",
            "owner": "Alex Rivera",
        },
    )
    assert m2_res.status_code == 201
    m2_id = m2_res.json()["id"]

    # 4. Link Dependency: m1 -> m2 (DAG validated)
    dep_res = await async_client.post(
        f"/api/v1/deals/{deal_id}/integration/dependencies",
        headers=headers,
        json={
            "predecessor_id": m1_id,
            "successor_id": m2_id,
            "dependency_type": "FINISH_TO_START",
        },
    )
    assert dep_res.status_code == 201
    dep_id = dep_res.json()["id"]

    # 5. Report Blocker
    blocker_res = await async_client.post(
        f"/api/v1/deals/{deal_id}/integration/blockers",
        headers=headers,
        json={
            "workstream_id": ws_id,
            "milestone_id": m1_id,
            "title": "Legacy LDAP schema mismatch",
            "description": "Custom attribute mapping requires vendor hotfix",
            "severity": "CRITICAL",
            "owner": "Alex Rivera",
        },
    )
    assert blocker_res.status_code == 201
    blocker_id = blocker_res.json()["id"]

    # 6. Check Health Score and Deductions
    health_res = await async_client.get(f"/api/v1/deals/{deal_id}/integration/health", headers=headers)
    assert health_res.status_code == 200
    h_data = health_res.json()
    assert h_data["health_score"] < 100.0  # Critical blocker deduction
    assert h_data["penalties"]["critical_blockers_penalty"] > 0

    # 7. Check Critical Path
    cp_res = await async_client.get(f"/api/v1/deals/{deal_id}/integration/critical-path", headers=headers)
    assert cp_res.status_code == 200
    cp_data = cp_res.json()
    assert cp_data["critical_path_duration_days"] == 20 + 45

    # 8. Check Timeline Stages
    timeline_res = await async_client.get(f"/api/v1/deals/{deal_id}/integration/timeline", headers=headers)
    assert timeline_res.status_code == 200
    t_data = timeline_res.json()
    assert len(t_data["stages"]["DAYS_1_30_STABILIZE"]) >= 1
    assert len(t_data["stages"]["DAYS_31_60_INTEGRATE"]) >= 1

    # 9. Check Executive Attention Escalations
    att_res = await async_client.get(f"/api/v1/deals/{deal_id}/integration/executive-attention", headers=headers)
    assert att_res.status_code == 200
    att_data = att_res.json()
    assert att_data["critical_count"] >= 1

    # 10. Resolve Blocker
    resolve_res = await async_client.patch(
        f"/api/v1/deals/{deal_id}/integration/blockers/{blocker_id}/resolve",
        headers=headers,
        json={"resolution_notes": "LDAP transformer script deployed"},
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "RESOLVED"

    # 11. Complete Milestone
    comp_res = await async_client.patch(
        f"/api/v1/deals/{deal_id}/integration/milestones/{m1_id}/status",
        headers=headers,
        json={"status": "COMPLETED", "completion_pct": 100.0},
    )
    assert comp_res.status_code == 200
    assert comp_res.json()["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_integration_tenant_isolation(seed_integration_env, async_client: AsyncClient):
    """Verify cross-tenant requests to access integration plans are rejected."""
    env = seed_integration_env
    deal_id = env["deal"].id

    foreign_org_id = uuid.uuid4()
    foreign_user_id = uuid.uuid4()

    foreign_token = create_access_token(
        subject=str(foreign_user_id), org_id=str(foreign_org_id), role="ANALYST"
    )
    foreign_headers = {
        "Authorization": f"Bearer {foreign_token}",
        "X-Organization-ID": str(foreign_org_id),
    }

    # Attempt to list or create workstreams from unauthorized tenant
    res = await async_client.get(f"/api/v1/deals/{deal_id}/integration", headers=foreign_headers)
    assert res.status_code in [401, 403, 404]

    post_res = await async_client.post(
        f"/api/v1/deals/{deal_id}/integration/workstreams",
        headers=foreign_headers,
        json={"name": "Hacked Workstream", "category": "EXECUTIVE_GOVERNANCE"},
    )
    assert post_res.status_code in [401, 403, 404]
