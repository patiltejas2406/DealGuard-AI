"""Deterministic Directed Acyclic Graph (DAG) Engine, Cycle Detection, and Critical Path Analysis."""

from collections import defaultdict, deque
from typing import Any, Dict, List, Set, Tuple
import uuid


def validate_dependency_graph(
    existing_dependencies: List[Any],
    new_predecessor_id: uuid.UUID,
    new_successor_id: uuid.UUID,
) -> None:
    """Validate that adding a dependency between predecessor and successor does not introduce cycles."""
    if new_predecessor_id == new_successor_id:
        raise ValueError(f"Self-dependency detected: milestone '{new_predecessor_id}' cannot depend on itself.")

    # Build adjacency list: pred -> list of succs
    adj: Dict[uuid.UUID, List[uuid.UUID]] = defaultdict(list)
    for dep in existing_dependencies:
        p_id = getattr(dep, "predecessor_id", None) or dep["predecessor_id"]
        s_id = getattr(dep, "successor_id", None) or dep["successor_id"]
        if isinstance(p_id, str):
            p_id = uuid.UUID(p_id)
        if isinstance(s_id, str):
            s_id = uuid.UUID(s_id)
        adj[p_id].append(s_id)

    # Add the candidate edge
    adj[new_predecessor_id].append(new_successor_id)

    # Check for cycles using DFS
    visited: Set[uuid.UUID] = set()
    rec_stack: Set[uuid.UUID] = set()

    def has_cycle(node: uuid.UUID) -> bool:
        visited.add(node)
        rec_stack.add(node)
        for neighbor in adj.get(node, []):
            if neighbor not in visited:
                if has_cycle(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True
        rec_stack.remove(node)
        return False

    all_nodes = set(adj.keys())
    for node in all_nodes:
        if node not in visited:
            if has_cycle(node):
                raise ValueError(
                    f"Circular dependency detected! Adding edge '{new_predecessor_id}' -> '{new_successor_id}' forms a loop in the integration execution DAG."
                )


def compute_critical_path(
    milestones: List[Any],
    dependencies: List[Any],
) -> Dict[str, Any]:
    """Compute deterministic Critical Path across integration milestones using longest-path DAG traversal."""
    if not milestones:
        return {
            "critical_path_milestone_ids": [],
            "critical_path_duration_days": 0,
            "longest_chain_length": 0,
            "chains": [],
        }

    milestone_map = {m.id: m for m in milestones}
    node_ids = list(milestone_map.keys())

    # Build graph and in-degrees
    adj: Dict[uuid.UUID, List[uuid.UUID]] = defaultdict(list)
    rev_adj: Dict[uuid.UUID, List[uuid.UUID]] = defaultdict(list)
    in_degree: Dict[uuid.UUID, int] = {nid: 0 for nid in node_ids}

    for dep in dependencies:
        p_id = dep.predecessor_id
        s_id = dep.successor_id
        if p_id in milestone_map and s_id in milestone_map:
            adj[p_id].append(s_id)
            rev_adj[s_id].append(p_id)
            in_degree[s_id] = in_degree.get(s_id, 0) + 1

    # Topological Sort (Kahn's algorithm)
    queue = deque([nid for nid in node_ids if in_degree[nid] == 0])
    topo_order: List[uuid.UUID] = []

    while queue:
        curr = queue.popleft()
        topo_order.append(curr)
        for nxt in adj.get(curr, []):
            in_degree[nxt] -= 1
            if in_degree[nxt] == 0:
                queue.append(nxt)

    # Longest path calculation
    # Distance is milestone target_day or sequential duration
    dist: Dict[uuid.UUID, int] = {}
    parent: Dict[uuid.UUID, Optional[uuid.UUID]] = {}

    for nid in node_ids:
        m = milestone_map[nid]
        dist[nid] = int(getattr(m, "target_day", 1) or 1)
        parent[nid] = None

    for u in topo_order:
        for v in adj.get(u, []):
            v_day = int(getattr(milestone_map[v], "target_day", 1) or 1)
            if dist[u] + v_day > dist[v]:
                dist[v] = dist[u] + v_day
                parent[v] = u

    # Find the endpoint with maximum distance
    if not dist:
        return {
            "critical_path_milestone_ids": [],
            "critical_path_duration_days": 0,
            "longest_chain_length": 0,
            "chains": [],
        }

    max_node = max(dist.keys(), key=lambda k: dist[k])
    max_duration = dist[max_node]

    # Reconstruct path
    curr_ptr: Optional[uuid.UUID] = max_node
    critical_path: List[uuid.UUID] = []
    while curr_ptr is not None:
        critical_path.append(curr_ptr)
        curr_ptr = parent.get(curr_ptr)

    critical_path.reverse()

    return {
        "critical_path_milestone_ids": [str(nid) for nid in critical_path],
        "critical_path_duration_days": max_duration,
        "longest_chain_length": len(critical_path),
        "critical_milestones": [
            {
                "id": str(nid),
                "name": milestone_map[nid].name,
                "target_day": milestone_map[nid].target_day,
                "status": milestone_map[nid].status,
                "priority": milestone_map[nid].priority,
            }
            for nid in critical_path
            if nid in milestone_map
        ],
    }
