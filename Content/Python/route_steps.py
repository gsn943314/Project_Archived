"""Route progress points for "how far did Point A get" when the goal is blocked.

The level path nodes (tag PathNode: PathA_00, PathB_03J, ...) describe the intended walkways. This spawns a TargetPoint
every half cell (175 cm) along every chain (same L-shaped route as the terrain: X first, then Y) in the Outliner folder
`Editor/Route`, tagged `RouteStep` plus one `Prog:<goal label>:<cm>` per goal = the remaining route length from that
point to the goal (Point B, and every StageGoal checkpoint) through the node graph.

BP_PathfindingCharacter.StartRun: when the goal is unreachable, Point A walks to the reachable RouteStep with the smallest
remaining length for its current TargetPoint (e.g. in front of an unturned bridge) instead of the NavMesh's partial end
(the dead end nearest the goal as the crow flies), then reports BLOCKED. Rebuilt by puzzle_level_tools.rebuild().
"""
import heapq
import unreal
import puzzle_level_tools as T

FOLDER = 'Editor/Route'
STEP = 175.0


def _nodes():
    chains = {}
    for a in T._actors():
        if 'PathNode' not in [str(t) for t in a.tags]:
            continue
        k = T._node_key(a)
        if k:
            chains.setdefault(k[0], []).append((k[1], a.get_actor_location()))
    for c in chains:
        chains[c].sort(key=lambda n: n[0])
    return chains


def _lpath(p, q):
    """Points every STEP along the walkway from p to q (X first, then Y; height blended), excluding p."""
    corner = unreal.Vector(q.x, p.y, p.z + (q.z - p.z) * (abs(q.x - p.x) / max(1.0, abs(q.x - p.x) + abs(q.y - p.y))))
    out = []
    for a, b in ((p, corner), (corner, q)):
        d = (b - a).length()
        n = max(1, int(round(d / STEP))) if d > 1 else 0
        for i in range(1, n + 1):
            out.append(a + (b - a) * (i / n))
    return out


def build():
    E = T._eas()
    for a in list(T._actors()):
        if T._folder(a) == FOLDER:
            E.destroy_actor(a)
    chains = _nodes()
    if not chains:
        return 0
    # graph over merged node positions
    pos, idx = [], {}

    def nid(v):
        for i, p in enumerate(pos):
            if (p - v).length() < 60:
                return i
        pos.append(v)
        return len(pos) - 1

    edges = {}
    segs = []
    for c, ns in chains.items():
        prev = None
        for _, v in ns:
            i = nid(v)
            if prev is not None and prev != i:
                pts = _lpath(pos[prev], pos[i])
                w = abs(pos[i].x - pos[prev].x) + abs(pos[i].y - pos[prev].y) + abs(pos[i].z - pos[prev].z)
                edges.setdefault(prev, []).append((i, w))
                edges.setdefault(i, []).append((prev, w))
                segs.append((prev, i, w, pts))
            prev = i
    goals = []
    for a in T._actors():
        tags = [str(t) for t in a.tags]
        if a.get_actor_label() == 'PointB_Target' or 'StageGoal' in tags:
            goals.append(a)
            # the goal carries its key as a tag (actor labels do not exist in packaged builds)
            key = 'Goal:' + a.get_actor_label()
            if key not in tags:
                a.tags = [t for t in a.tags if not str(t).startswith('Goal:')] + [unreal.Name(key)]
    dist = {}
    for g in goals:
        gl = g.get_actor_location()
        src = min(range(len(pos)), key=lambda i: (pos[i] - gl).length())
        d = {src: 0.0}
        h = [(0.0, src)]
        while h:
            dd, u = heapq.heappop(h)
            if dd > d.get(u, 1e18):
                continue
            for v, w in edges.get(u, []):
                if dd + w < d.get(v, 1e18):
                    d[v] = dd + w
                    heapq.heappush(h, (dd + w, v))
        dist[g.get_actor_label()] = d
    pts = [(pos[i], i, None, 0.0) for i in range(len(pos))]
    for u, v, w, ps in segs:
        for k, p in enumerate(ps[:-1]):
            t = w * (k + 1) / len(ps)
            pts.append((p, u, v, t))
    n = 0
    for p, u, v, t in pts:
        tags = [unreal.Name('RouteStep')]
        for g, d in dist.items():
            w = next((ww for vv, ww in edges.get(u, []) if vv == v), 0.0) if v is not None else 0.0
            val = min(d.get(u, 1e9) + t, d.get(v, 1e9) + (w - t)) if v is not None else d.get(u, 1e9)
            tags.append(unreal.Name(f'Prog:{g}:{int(val)}'))
        a = E.spawn_actor_from_class(unreal.TargetPoint, p + unreal.Vector(0, 0, 20))
        a.set_actor_label(f'Route_{n:03d}')
        a.set_folder_path(FOLDER)
        a.tags = tags
        n += 1
    return n
