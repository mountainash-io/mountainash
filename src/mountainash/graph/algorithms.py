from __future__ import annotations

from collections import deque


def topological_order(
    nodes: set[str],
    edges: set[tuple[str, str]],
    target: str | None = None,
) -> list[str]:
    """Kahn's algorithm with optional ancestor filtering.

    Args:
        nodes: All node names in the graph.
        edges: Set of (upstream, downstream) tuples. An edge (A, B) means
               A must complete before B.
        target: If given, only the target and its ancestors are included.

    Returns:
        Deterministic topological ordering (sorted ready queue).

    Raises:
        ValueError: If a cycle is detected or target is not in nodes.
    """
    if target is not None:
        if target not in nodes:
            raise ValueError(f"Target '{target}' not found in nodes")
        relevant = ancestors(edges, target) | {target}
    else:
        relevant = set(nodes)

    adj: dict[str, list[str]] = {n: [] for n in relevant}
    in_degree: dict[str, int] = {n: 0 for n in relevant}

    for upstream, downstream in edges:
        if upstream in relevant and downstream in relevant:
            adj[upstream].append(downstream)
            in_degree[downstream] += 1

    queue: deque[str] = deque(sorted(n for n, deg in in_degree.items() if deg == 0))
    order: list[str] = []

    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in sorted(adj[node]):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(order) != len(relevant):
        unordered = relevant - set(order)
        raise ValueError(f"Cycle detected: could not order {unordered}")

    return order


def ancestors(
    edges: set[tuple[str, str]],
    target: str,
) -> set[str]:
    """BFS backward from target through edges.

    Args:
        edges: Set of (upstream, downstream) tuples.
        target: Node to find ancestors of.

    Returns:
        All ancestors of target (not including target itself).
    """
    reverse: dict[str, list[str]] = {}
    for upstream, downstream in edges:
        reverse.setdefault(downstream, []).append(upstream)

    result: set[str] = set()
    queue: deque[str] = deque(reverse.get(target, []))
    while queue:
        node = queue.popleft()
        if node not in result:
            result.add(node)
            queue.extend(reverse.get(node, []))
    return result


def parallel_layers(
    edges: set[tuple[str, str]],
    order: list[str],
) -> list[list[str]]:
    """Group nodes into parallel layers from a topological order.

    Nodes in the same layer have no dependencies on each other
    and can execute concurrently.

    Args:
        edges: Set of (upstream, downstream) tuples.
        order: A valid topological ordering of the nodes.

    Returns:
        List of layers, where each layer is a list of node names.
    """
    order_set = set(order)
    upstream_of: dict[str, list[str]] = {}
    for up, down in edges:
        if up in order_set and down in order_set:
            upstream_of.setdefault(down, []).append(up)

    depth: dict[str, int] = {}
    for name in order:
        deps = upstream_of.get(name, [])
        if not deps:
            depth[name] = 0
        else:
            depth[name] = max(depth[d] for d in deps) + 1

    if not depth:
        return []

    max_depth = max(depth.values())
    layers: list[list[str]] = [[] for _ in range(max_depth + 1)]
    for name in order:
        layers[depth[name]].append(name)

    return layers
