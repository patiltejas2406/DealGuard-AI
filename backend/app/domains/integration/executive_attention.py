"""Executive Escalation and Attention Prioritization Filter."""

from typing import Any, Dict, List


def generate_executive_attention_queue(
    workstreams: List[Any],
    milestones: List[Any],
    blockers: List[Any],
    critical_path_milestone_ids: List[str],
    current_day_offset: int = 1,
) -> Dict[str, Any]:
    """Generate prioritized queue of items requiring executive oversight and steering committee decisions."""
    critical_items: List[Dict[str, Any]] = []
    high_items: List[Dict[str, Any]] = []
    medium_items: List[Dict[str, Any]] = []

    milestone_map = {str(m.id): m for m in milestones}
    workstream_map = {str(w.id): w for w in workstreams}
    cp_set = set(critical_path_milestone_ids)

    # 1. Inspect Blockers
    for b in blockers:
        if getattr(b, "status", "OPEN") == "OPEN":
            ws = workstream_map.get(str(getattr(b, "workstream_id", "")))
            ws_name = getattr(ws, "name", "Integration Workstream")
            b_sev = getattr(b, "severity", "HIGH")
            m_id = str(getattr(b, "milestone_id", "") or "")
            is_cp = m_id in cp_set

            item = {
                "source_type": "BLOCKER",
                "id": str(b.id),
                "title": b.title,
                "description": b.description,
                "workstream_name": ws_name,
                "owner": getattr(b, "owner", "Unassigned"),
                "is_critical_path": is_cp,
                "action_required": "Resolve operational blocker or reassign resources",
            }

            if b_sev == "CRITICAL" or is_cp:
                critical_items.append(item)
            elif b_sev == "HIGH":
                high_items.append(item)
            else:
                medium_items.append(item)

    # 2. Inspect Milestones for Overdue / Critical Path Risk
    for m in milestones:
        m_id = str(m.id)
        m_status = getattr(m, "status", "NOT_STARTED")
        m_day = getattr(m, "target_day", 100)
        c_pct = float(getattr(m, "completion_pct", 0.0) or 0.0)
        is_overdue = (m_day < current_day_offset and c_pct < 100.0) or m_status == "OVERDUE"
        is_cp = m_id in cp_set
        ws = workstream_map.get(str(getattr(m, "workstream_id", "")))
        ws_name = getattr(ws, "name", "Integration Workstream")

        if is_overdue and is_cp:
            critical_items.append({
                "source_type": "CRITICAL_PATH_OVERDUE",
                "id": m_id,
                "title": f"Critical Path Milestone Overdue: {m.name}",
                "description": f"Milestone is scheduled for Day {m_day} (Current Day: {current_day_offset}) and is on the integration critical path.",
                "workstream_name": ws_name,
                "owner": getattr(m, "owner", "Unassigned"),
                "is_critical_path": True,
                "action_required": "Executive intervention to accelerate critical path dependency",
            })
        elif is_overdue:
            high_items.append({
                "source_type": "MILESTONE_OVERDUE",
                "id": m_id,
                "title": f"Milestone Overdue: {m.name}",
                "description": f"Target Day {m_day} exceeded without completion ({c_pct}% complete).",
                "workstream_name": ws_name,
                "owner": getattr(m, "owner", "Unassigned"),
                "is_critical_path": False,
                "action_required": "Review delivery timeline with workstream owner",
            })
        elif m_status in ["AT_RISK", "BLOCKED"]:
            high_items.append({
                "source_type": "MILESTONE_AT_RISK",
                "id": m_id,
                "title": f"Milestone At Risk: {m.name}",
                "description": f"Workstream flagged milestone status as {m_status}.",
                "workstream_name": ws_name,
                "owner": getattr(m, "owner", "Unassigned"),
                "is_critical_path": is_cp,
                "action_required": "Evaluate resource constraints and dependencies",
            })

    # 3. Inspect Workstream Statuses
    for w in workstreams:
        w_status = getattr(w, "status", "NOT_STARTED")
        if w_status == "BLOCKED":
            critical_items.append({
                "source_type": "WORKSTREAM_BLOCKED",
                "id": str(w.id),
                "title": f"Workstream Blocked: {w.name}",
                "description": f"Workstream {w.name} ({w.category}) is completely blocked.",
                "workstream_name": w.name,
                "owner": getattr(w, "owner", "Unassigned"),
                "is_critical_path": False,
                "action_required": "Steering Committee unblocking required",
            })

    return {
        "critical_count": len(critical_items),
        "high_count": len(high_items),
        "medium_count": len(medium_items),
        "total_attention_items": len(critical_items) + len(high_items) + len(medium_items),
        "critical_items": critical_items,
        "high_items": high_items,
        "medium_items": medium_items,
    }
