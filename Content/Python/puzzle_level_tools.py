"""Editor-time level editing tools for the block puzzle levels.

The level is described by marker actors (folder "Editor") and rebuilt from them:

  PathA_00, PathA_01 ...   yellow spheres = path nodes, walked in order. Consecutive nodes are
                           joined by a corridor (first along X, then along Y). Raise / lower a node
                           (Z, 175 cm per tier) and stairs appear on the corridor leading to it.
                           PathB_.., PathC_.. = extra corridors / branches (e.g. the safe loop of a fork).
                           Point A starts on PathA_00, Point B is placed on the last PathA node.
  Floor_* (blue tile)      one extra walkable cell (alcove / pocket) at the tile's height.
  Hole_*  (target point)   a sunken pit in the floor - fill it with a block.
  Blocks / enemies         BP_EditableObstacle / BP_EnemyBlock in folder "Blocks". If one sits on a
                           wall, rebuilding carves a pocket under it automatically.

Puzzle menu: "Rebuild Level From Markers" regenerates walls / floors / stairs / pits (folder "Maze"),
snaps blocks onto the floor, moves Point A/B, resizes the NavMesh and saves.
"""
import math
import unreal

C = 350.0
U = 175.0          # tier height of the open level (175, or 350 for art levels: Editor_Grid tag 'TierH:350')
PIT = 175.0        # hole depth = block height
OPEN_STAIR_SIDE = True   # lower the camera-side wall next to stairs (grey-box levels)
ISLAND = True            # cut the terrain away outside the rim walls (level stands like an island)
BACKDROP_Z = -1800.0     # the ground plane far below the island
RIM = 175.0              # thickness of the rim walls on the island edge (half a cell)
BASE = -440.0
AGGRO = 900.0
L_SCALE = (3.5, 3.5, 1.75)
M_SCALE = (1.75, 3.5, 1.75)
GRID_LABEL = 'Editor_Grid'
BP_DIR = '/Game/Project/Programming/Blueprints/Pathfinding/'


def _eas():
    return unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def _world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


def _cls(name):
    return unreal.load_asset(BP_DIR + name).generated_class()


def _actors():
    return _eas().get_all_level_actors()


def _folder(a):
    return str(a.get_folder_path())


# ------------------------------------------------------------------ grid
def grid_tier_height(a):
    for t in a.tags:
        t = str(t)
        if t.startswith('TierH:'):
            return float(t[6:])
    return 175.0


def use_grid(a):
    """Reads the per-level settings stored on the Editor_Grid actor."""
    global U, OPEN_STAIR_SIDE
    U = grid_tier_height(a)
    OPEN_STAIR_SIDE = 'Art' not in [str(t) for t in a.tags]   # art levels: no lowered wall beside stairs


def get_grid():
    for a in _actors():
        if a.get_actor_label() == GRID_LABEL:
            use_grid(a)
            if 'EditorGrid' not in [str(t) for t in a.tags]:   # found in the game by BP_PathfindingCharacter (SnapCell)
                a.tags = list(a.tags) + [unreal.Name('EditorGrid')]
            l = a.get_actor_location()
            return l.x, l.y
    globals()['U'] = 175.0
    globals()['OPEN_STAIR_SIDE'] = True
    for a in _actors():  # older levels: align to an existing floor tile
        if a.get_actor_label().startswith('Maze_Path_'):
            l = a.get_actor_location()
            return l.x % C - C * 40, l.y % C - C * 40
    return -C * 40, -C * 40


def set_grid(x0, y0):
    for a in _actors():
        if a.get_actor_label() == GRID_LABEL:
            a.set_actor_location(unreal.Vector(x0, y0, 0), False, False)
            return a
    a = _eas().spawn_actor_from_class(unreal.TargetPoint, unreal.Vector(x0, y0, 0))
    a.set_actor_label(GRID_LABEL)
    a.set_folder_path('Editor')
    return a


def cell_of(x, y, grid=None):
    x0, y0 = grid or get_grid()
    return (int(math.floor((y - y0) / C)), int(math.floor((x - x0) / C)))


def cell_min(rc, grid):
    return grid[0] + rc[1] * C, grid[1] + rc[0] * C


def cell_ctr(rc, grid):
    x, y = cell_min(rc, grid)
    return x + C / 2, y + C / 2


def tier_of(z):
    return int(round(z / U))


# ------------------------------------------------------------------ markers
def _marker_mesh(label, folder, loc, mesh, mat, scale, tags):
    a = _eas().spawn_actor_from_class(unreal.StaticMeshActor, loc)
    smc = a.static_mesh_component
    smc.set_static_mesh(unreal.load_asset(mesh))
    m = unreal.load_asset(mat)
    if m:
        smc.set_material(0, m)
    smc.set_editor_property('cast_shadow', False)
    make_ghost(a)
    a.set_actor_scale3d(unreal.Vector(*scale))
    a.set_actor_hidden_in_game(True)
    a.set_actor_label(label)
    a.set_folder_path(folder)
    a.tags = [unreal.Name(t) for t in tags]
    return a


def make_ghost(a):
    """Markers must never block the character or the NavMesh (editor-only helpers)."""
    smc = a.static_mesh_component
    smc.set_collision_profile_name('NoCollision')
    smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    smc.set_editor_property('can_ever_affect_navigation', False)
    a.set_actor_enable_collision(False)
    a.set_actor_hidden_in_game(True)


def spawn_node(chain, idx, rc, tier, grid):
    x, y = cell_ctr(rc, grid)
    return _marker_mesh(f'Path{chain}_{idx:02d}', 'Editor/Path', unreal.Vector(x, y, tier * U),
                        '/Engine/BasicShapes/Sphere', '/Game/Project/Art/Materials/Gimmick/MI_G_PlateOn',
                        (1.1, 1.1, 1.1), ('PathNode',))


def spawn_floor(rc, tier, grid):
    x, y = cell_ctr(rc, grid)
    return _marker_mesh(f'Floor_r{rc[0]}_c{rc[1]}', 'Editor/Floor', unreal.Vector(x, y, tier * U + 6),
                        '/Engine/BasicShapes/Cube', '/Game/Project/Art/Materials/Gimmick/MI_G_Water',
                        (2.9, 2.9, 0.08), ('FloorMark',))


def spawn_wide(rc, tier, grid):
    """Widening floor: built exactly like a floor tile (FloorMark), only to make a walkway look wider.
    One brown tile (easy to select / drag), told apart from the blue walkable pocket tiles by colour."""
    x, y = cell_ctr(rc, grid)
    return _marker_mesh(f'Wide_r{rc[0]}_c{rc[1]}', 'Editor/Wide', unreal.Vector(x, y, tier * U + 6),
                        '/Engine/BasicShapes/Cube', '/Game/Project/Art/Materials/Gimmick/MI_G_Wood',
                        (2.9, 2.9, 0.08), ('FloorMark', 'WideMark'))


def spawn_hole(rc, tier, grid):
    x, y = cell_ctr(rc, grid)
    tp = _eas().spawn_actor_from_class(unreal.TargetPoint, unreal.Vector(x, y, tier * U))
    tp.set_actor_label(f'Hole_r{rc[0]}_c{rc[1]}')
    tp.tags = [unreal.Name('Hole')]
    tp.set_folder_path('Editor/Holes')
    return tp


def spawn_mover(kind, loc, yaw=0.0, label=None):
    """kind: 'L' (2x2 block), 'M' (thin block) or 'Enemy'."""
    cls = _cls('BP_EnemyBlock') if kind == 'Enemy' else _cls('BP_EditableObstacle')
    a = _eas().spawn_actor_from_class(cls, loc, unreal.Rotator(0, 0, yaw))
    a.set_actor_scale3d(unreal.Vector(*(L_SCALE if kind == 'L' else M_SCALE)))
    if label:
        a.set_actor_label(label)
    a.set_folder_path('Blocks')
    a.tags = [unreal.Name('Editable')]
    if kind == 'Enemy':
        a.set_editor_property('AggroRadius', AGGRO)
    return a


def _node_key(a):
    lab = a.get_actor_label()  # PathA_03
    try:
        head, idx = lab[4:].split('_', 1)
        return head, int(''.join(ch for ch in idx if ch.isdigit()) or 0)
    except ValueError:
        return None


def read_markers(grid):
    nodes, floors, holes, movers = {}, {}, {}, []
    eb, ob = _cls('BP_EnemyBlock'), _cls('BP_EditableObstacle')
    for a in _actors():
        lab = a.get_actor_label()
        tags = [str(t) for t in a.tags]
        l = a.get_actor_location()
        if ('PathNode' in tags or 'FloorMark' in tags) and isinstance(a, unreal.StaticMeshActor) \
                and a.get_actor_enable_collision():
            make_ghost(a)
        if 'PathNode' in tags:
            k = _node_key(a)
            if k:
                nodes.setdefault(k[0], []).append((k[1], cell_of(l.x, l.y, grid), tier_of(l.z), lab))
        elif 'FloorMark' in tags:
            floors[cell_of(l.x, l.y, grid)] = tier_of(l.z)
        elif 'Hole' in tags and isinstance(a, unreal.TargetPoint):
            holes[cell_of(l.x, l.y, grid)] = tier_of(l.z)
        elif a.get_class() in (eb, ob):
            movers.append(a)
    for k in nodes:
        nodes[k].sort(key=lambda n: n[0])
    return nodes, floors, holes, movers


# ------------------------------------------------------------------ geometry
def route(a, b):
    """Cells from a (exclusive) to b (inclusive): first along columns (X), then rows (Y)."""
    out = []
    r, c = a
    while c != b[1]:
        d = (0, 1 if b[1] > c else -1)
        c += d[1]
        out.append(((r, c), d))
    while r != b[0]:
        d = (1 if b[0] > r else -1, 0)
        r += d[0]
        out.append(((r, c), d))
    return out


def clear_all():
    for a in list(_actors()):
        f = _folder(a)
        if (f in ('Maze', 'Blocks', 'Gimmicks', 'Hints') or f.startswith('Editor')) and a.get_actor_label() != 'Maze_Backdrop':
            _eas().destroy_actor(a)
        elif a.get_actor_label().startswith('Maze_Pillar'):
            _eas().destroy_actor(a)


_ASSETS = {}


def _asset(path):
    if path not in _ASSETS or _ASSETS[path] is None:
        _ASSETS[path] = unreal.load_asset(path)
    return _ASSETS[path]


def geometry_specs(floor, pits, stairs, grid):
    """Desired terrain boxes: {label: (x0, y0, sx, sy, top, material_path, tags)} and the cell bounds."""
    MF = '/Game/Project/Art/Materials/MI_MazeFloor'
    MW = '/Game/Project/Art/Materials/MI_MazeWall'
    MP = '/Game/Project/Art/Materials/MI_MazeBackdrop'
    specs = {}
    lvl = dict(floor)
    lvl.update(pits)
    for rc, (h0, h1, _d) in stairs.items():
        lvl[rc] = max(h0, h1)
    for rc, h in floor.items():
        x, y = cell_min(rc, grid)
        specs[f'Maze_Path_r{rc[0]}_c{rc[1]}'] = (x, y, C, C, h, MF, ())
    for rc, h in pits.items():
        x, y = cell_min(rc, grid)
        specs[f'Maze_Pit_r{rc[0]}_c{rc[1]}'] = (x, y, C, C, h - PIT, MP, ())
    opened = {}
    # 350 cm tiers make 45-degree stairs: steps must be <= 10 cm or the NavMesh (19 cm voxels) sees 50 cm jumps
    n = 7 if U <= 175 else int(round(U / 10.0))
    for rc, (h0, h1, d) in stairs.items():
        x, y = cell_min(rc, grid)
        for k in range(n):
            t = k if (d[0] + d[1]) > 0 else n - 1 - k
            top = h0 + (h1 - h0) * (k + 1) / n
            lab = f'Maze_Stair_r{rc[0]}_c{rc[1]}_s{k}'
            if d[1] != 0:
                specs[lab] = (x + t * C / n, y, C / n, C, top, MF, ())
            else:
                specs[lab] = (x, y + t * C / n, C, C / n, top, MF, ())
        side = (-1, 0) if d[1] != 0 else (0, -1)       # camera-facing (-Y / -X) side stays open
        for kk in (-1, 0, 1):
            o = (rc[0] + side[0] + d[0] * kk, rc[1] + side[1] + d[1] * kk)
            opened[o] = min(opened.get(o, 1e9), min(h0, h1) - 60)
    # walls touching a stair must rise above its top step, otherwise the middle steps line up with
    # the wall tops and the NavMesh lets the character walk off the stairs onto the walls
    stair_adj = {}
    for rc, (h0, h1, _d) in stairs.items():
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                o = (rc[0] + dr, rc[1] + dc)
                stair_adj[o] = max(stair_adj.get(o, -1e9), max(h0, h1))
    rs = [rc[0] for rc in lvl]
    cs = [rc[1] for rc in lvl]
    r0, r1, c0, c1 = min(rs) - 2, max(rs) + 2, min(cs) - 2, max(cs) + 2
    cells = list(lvl.items())
    # island edge: wall cells that don't touch the walkway and connect to the outside of the map are cut
    # away (no terrain), so the level stands like an island with straight cliffs at its rim
    def touches(r, c):
        return any((r + dr, c + dc) in lvl for dr in (-1, 0, 1) for dc in (-1, 0, 1))
    outside = set()
    stack = [(r, c) for r in range(r0, r1 + 1) for c in (c0, c1)] + [(r, c) for c in range(c0, c1 + 1) for r in (r0, r1)]
    while stack:
        rc = stack.pop()
        if rc in outside or rc in lvl or touches(*rc) or not (r0 <= rc[0] <= r1 and c0 <= rc[1] <= c1):
            continue
        outside.add(rc)
        stack += [(rc[0] + 1, rc[1]), (rc[0] - 1, rc[1]), (rc[0], rc[1] + 1), (rc[0], rc[1] - 1)]
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if (r, c) in lvl or (ISLAND and (r, c) in outside):
                continue
            nb = [lvl[(r + dr, c + dc)] for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (r + dr, c + dc) in lvl]
            if nb:
                top = min(nb) + 60                 # walls drop to the lower neighbour -> terraces
            else:
                near = min(cells, key=lambda kv: (kv[0][0] - r) ** 2 + (kv[0][1] - c) ** 2)
                top = near[1] + 60
            if (r, c) in opened and OPEN_STAIR_SIDE:
                top = min(top, opened[(r, c)])
            elif (r, c) in stair_adj:
                top = max(top, stair_adj[(r, c)] + 60)
            x, y = cell_min((r, c), grid)
            sx = sy = C
            if ISLAND:                                  # rim walls are half a cell thick on the outside
                if (r, c - 1) in outside:
                    x += C - RIM; sx -= C - RIM
                if (r, c + 1) in outside:
                    sx -= C - RIM
                if (r - 1, c) in outside:
                    y += C - RIM; sy -= C - RIM
                if (r + 1, c) in outside:
                    sy -= C - RIM
                sx, sy = max(sx, RIM), max(sy, RIM)
            specs[f'Maze_Wall_r{r}_c{c}'] = (x, y, sx, sy, top, MW, ('Wall',))
    return specs, (r0, r1, c0, c1)


def build_geometry(floor, pits, stairs, grid):
    """Incremental: keeps terrain actors whose label already exists, only moves / rescales changed ones."""
    eas = _eas()
    cube = _asset('/Game/LevelPrototyping/Meshes/SM_Cube')
    specs, bounds = geometry_specs(floor, pits, stairs, grid)
    existing = {}
    for a in list(_actors()):
        lab = a.get_actor_label()
        if _folder(a) == 'Maze' and lab != 'Maze_Backdrop':
            if lab in specs and lab not in existing:
                existing[lab] = a
            else:
                eas.destroy_actor(a)
        elif lab.startswith('Maze_Pillar'):
            eas.destroy_actor(a)
    for a in _actors():                      # ground plane drops far below so the island stands free
        if a.get_actor_label() == 'Maze_Backdrop' and ISLAND:
            l = a.get_actor_location()
            if abs(l.z - BACKDROP_Z) > 1:
                a.set_actor_location(unreal.Vector(l.x, l.y, BACKDROP_Z), False, False)
    changed = 0
    for lab, (x0, y0, sx, sy, top, mat, tags) in specs.items():
        loc = unreal.Vector(x0, y0, BASE)
        scale = unreal.Vector(sx / 100, sy / 100, max(1.0, top - BASE) / 100)
        a = existing.get(lab)
        if a is None:
            a = eas.spawn_actor_from_class(unreal.StaticMeshActor, loc)
            smc = a.static_mesh_component
            smc.set_static_mesh(cube)
            smc.set_material(0, _asset(mat))
            a.set_actor_label(lab)
            a.set_folder_path('Maze')
            a.tags = [unreal.Name(t) for t in tags]
            a.set_actor_scale3d(scale)
            changed += 1
            continue
        if (a.get_actor_location() - loc).length() > 0.5:
            a.set_actor_location(loc, False, False); changed += 1
        if (a.get_actor_scale3d() - scale).length() > 0.001:
            a.set_actor_scale3d(scale); changed += 1
        smc = a.static_mesh_component
        m = _asset(mat)
        if smc.get_material(0) != m:
            smc.set_material(0, m)
    return bounds, changed


# ------------------------------------------------------------------ rebuild
def compute_layout(grid, nodes, floor_marks, holes, movers):
    """Pure layout: returns floor / stairs / pits (cm), carved pocket cells and warnings."""
    warns = []
    floor, stairs, pits = {}, {}, {}
    for ch in sorted(nodes):
        lst = nodes[ch]
        _i, prc, pt, plab = lst[0]
        if prc not in stairs:
            floor.setdefault(prc, pt * U)
        for _i, rc, t, lab in lst[1:]:
            if lab.endswith('J'):       # 'jump' node (e.g. top of a lift): not connected to the previous node
                if rc not in stairs:
                    floor[rc] = t * U
                prc, pt, plab = rc, t, lab
                continue
            seg = route(prc, rc)
            delta = t - pt
            m = abs(delta)
            picks = set()
            if seg and m:
                cand = [k for k in range(len(seg) - 1) if seg[k][1] == seg[k + 1][1]]
                if len(cand) < m:
                    warns.append((rc, f'{plab} -> {lab}: needs {m} stair(s), only {len(cand)} straight cell(s)'))
                picks = set(cand[int((i + 0.5) * len(cand) / m)] for i in range(min(m, len(cand))))
            elif m and not seg:
                warns.append((rc, f'{plab} / {lab}: same cell, different height'))
            h = pt
            for k, (cell, d) in enumerate(seg):
                if k in picks:
                    nh = h + (1 if delta > 0 else -1)
                    stairs[cell] = (h * U, nh * U, d)
                    floor.pop(cell, None)
                    h = nh
                elif cell not in stairs:
                    floor[cell] = h * U
            prc, pt, plab = rc, t, lab
    for rc, t in floor_marks.items():
        if rc not in stairs:
            floor[rc] = t * U
    for rc, t in holes.items():
        pits[rc] = floor.pop(rc, t * U)
    carved = []
    for a in movers:
        l = a.get_actor_location()
        rc = cell_of(l.x, l.y, grid)
        if rc in floor or rc in pits or rc in stairs:
            continue
        nb = [floor[(rc[0] + dr, rc[1] + dc)] for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0))
              if (rc[0] + dr, rc[1] + dc) in floor]
        floor[rc] = min(nb, key=lambda h: abs(h - l.z)) if nb else tier_of(l.z) * U
        carved.append(rc)
    return floor, stairs, pits, carved, warns


def ground_z(rc, floor, stairs, pits):
    if rc in pits:
        return pits[rc] - PIT
    if rc in stairs:
        return max(stairs[rc][:2])
    return floor.get(rc)


def rebuild(save=True, navmesh=True):
    grid = get_grid()
    nodes, floor_marks, holes, movers = read_markers(grid)
    if not nodes.get('A'):
        raise RuntimeError('No PathA_00 node in this level. Use "Path Node" to start a path '
                           '(or Generate Random Block Tutorial, which creates the markers).')
    floor, stairs, pits, carved, warns = compute_layout(grid, nodes, floor_marks, holes, movers)
    for a in movers:
        l = a.get_actor_location()
        z = ground_z(cell_of(l.x, l.y, grid), floor, stairs, pits)
        if z is not None and abs(z - l.z) > 0.5:
            a.set_actor_location(unreal.Vector(l.x, l.y, z), False, False)
    (r0, r1, c0, c1), changed = build_geometry(floor, pits, stairs, grid)
    import storybook_skin as SK
    if SK.enabled():
        SK.apply()

    labels = {a.get_actor_label(): a for a in _actors() if a.get_actor_label() in
              ('PointA_PathfindingCharacter', 'PointB_Target', 'NavMeshBoundsVolume_Puzzle')}
    first, last = nodes['A'][0], nodes['A'][-1]

    def place(lab, loc):
        a = labels.get(lab)
        if a and (a.get_actor_location() - loc).length() > 0.5:
            a.set_actor_location(loc, False, False)
    x, y = cell_ctr(first[1], grid)
    place('PointA_PathfindingCharacter', unreal.Vector(x, y, first[2] * U + 100))
    x, y = cell_ctr(last[1], grid)
    place('PointB_Target', unreal.Vector(x, y, last[2] * U))
    hs = list(floor.values()) + [max(s[:2]) for s in stairs.values()]
    top_h = max(hs)
    nav = labels.get('NavMeshBoundsVolume_Puzzle')
    if nav:
        cx, cy = grid[0] + (c0 + c1 + 1) * C / 2, grid[1] + (r0 + r1 + 1) * C / 2
        place('NavMeshBoundsVolume_Puzzle', unreal.Vector(cx, cy, top_h / 2))
        sc = unreal.Vector((c1 - c0 + 1) * C / 200 + 2, (r1 - r0 + 1) * C / 200 + 2, (top_h + 1400) / 200)
        if (nav.get_actor_scale3d() - sc).length() > 0.001:
            nav.set_actor_scale3d(sc)
    if navmesh:
        unreal.SystemLibrary.execute_console_command(_world(), 'BUILDPATHS')
    if save:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return {'warnings': [w[1] for w in warns], 'warn_cells': warns, 'carved': len(carved), 'tiers': int(top_h / U),
            'stairs': len(stairs), 'cells': len(floor) + len(stairs) + len(pits), 'changed': changed}


# ------------------------------------------------------------------ menu actions
def _anchor():
    """Location to spawn a new marker.
    Clicked (selected) floor / wall / art: right on top of it (centre of its top face).
    Selected marker (path node, tile, hole, block): the next cell beside it (e.g. insert after a node).
    Nothing selected: where the viewport camera looks at the ground."""
    sel = _eas().get_selected_level_actors()
    if sel:
        a = sel[0]
        tags = [str(t) for t in a.tags]
        marker = _folder(a).startswith('Editor') or _folder(a) == 'Blocks' or 'PathNode' in tags or 'FloorMark' in tags
        if not marker:
            o, e = a.get_actor_bounds(False)
            return unreal.Vector(o.x, o.y, o.z + e.z), a
        l = a.get_actor_location()
        return unreal.Vector(l.x + C, l.y, l.z), a
    loc, rot = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_level_viewport_camera_info()
    f = rot.get_forward_vector()
    t = (0 - loc.z) / f.z if f.z < -0.05 else 2500
    p = loc + f * t
    return unreal.Vector(p.x, p.y, 0), None


def _snap(loc, grid):
    rc = cell_of(loc.x, loc.y, grid)
    x, y = cell_ctr(rc, grid)
    return rc, unreal.Vector(x, y, tier_of(loc.z) * U)


def _select(a):
    _eas().set_selected_level_actors([a])


def add_path_node():
    grid = get_grid()
    with unreal.ScopedEditorTransaction('Add Path Node'):
        loc, sel = _anchor()
        key = _node_key(sel) if sel is not None and 'PathNode' in [str(t) for t in sel.tags] else None
        nodes = read_markers(grid)[0]
        if key is None:  # nothing selected: start PathA or append to its end
            chain = 'A'
            idx = nodes['A'][-1][0] + 1 if nodes.get('A') else 0
        else:
            chain, i = key
            lst = nodes.get(chain, [])
            nxt = [n for n in lst if n[0] > i]
            if nxt:  # insert between the selected node and the next one
                sl, nl = sel.get_actor_location(), nxt[0][1]
                nx, ny = cell_ctr(nl, grid)
                loc = unreal.Vector((sl.x + nx) / 2, (sl.y + ny) / 2, sl.z)
                for a in sorted(_actors(), key=lambda a: -(_node_key(a) or ('', -1))[1]):
                    k = _node_key(a) if 'PathNode' in [str(t) for t in a.tags] else None
                    if k and k[0] == chain and k[1] > i:
                        a.set_actor_label(f'Path{chain}_{k[1] + 1:02d}')
            idx = i + 1
        rc, _ = _snap(loc, grid)
        a = spawn_node(chain, idx, rc, tier_of(loc.z), grid)
    _select(a)
    return a


def add_branch():
    """Start a new corridor chain (PathB, PathC ...) with two nodes next to the selection."""
    grid = get_grid()
    with unreal.ScopedEditorTransaction('Add Branch'):
        loc, _ = _anchor()
        nodes = read_markers(grid)[0]
        chain = next(ch for ch in 'BCDEFGHIJKLMNOPQRSTUVWXYZ' if ch not in nodes)
        rc, p = _snap(loc, grid)
        spawn_node(chain, 0, rc, tier_of(p.z), grid)
        a = spawn_node(chain, 1, (rc[0], rc[1] + 3), tier_of(p.z), grid)
    _select(a)
    return a


def add_floor():
    grid = get_grid()
    with unreal.ScopedEditorTransaction('Add Floor Tile'):
        loc, _ = _anchor()
        rc, p = _snap(loc, grid)
        a = spawn_floor(rc, tier_of(p.z), grid)
    _select(a)
    return a


def add_wide():
    grid = get_grid()
    with unreal.ScopedEditorTransaction('Add Widening Floor'):
        loc, _ = _anchor()
        rc, p = _snap(loc, grid)
        a = spawn_wide(rc, tier_of(p.z), grid)
    _select(a)
    return a


def add_hole():
    grid = get_grid()
    with unreal.ScopedEditorTransaction('Add Hole'):
        loc, _ = _anchor()
        rc, p = _snap(loc, grid)
        a = spawn_hole(rc, tier_of(p.z), grid)
    _select(a)
    return a


def _add_mover(kind, title):
    grid = get_grid()
    with unreal.ScopedEditorTransaction(title):
        loc, _ = _anchor()
        _rc, p = _snap(loc, grid)
        a = spawn_mover(kind, p)
        if kind != 'Enemy':
            attach_crate(a)
    _select(a)
    return a


CRATE = '/Game/Dev/Meshes/SM_Crate'


def attach_crate(blk):
    """Final-render look of a movable block: a crate fitted to the block, attached so it follows it
    (also into a hole). The purple block is grey-view only (VisGrey), the crate final-view only."""
    for c in list(_actors()):
        if c.get_actor_label() == 'ArtCrate_' + blk.get_actor_label():
            _eas().destroy_actor(c)
    mesh = unreal.load_asset(CRATE)
    mb = mesh.get_bounding_box()
    ex = mb.max - mb.min
    o, e = blk.get_actor_bounds(True)
    c = _eas().spawn_actor_from_class(unreal.StaticMeshActor, blk.get_actor_location(), blk.get_actor_rotation())
    c.root_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    smc = c.static_mesh_component
    smc.set_static_mesh(mesh)
    smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    smc.set_editor_property('can_ever_affect_navigation', False)
    c.set_actor_enable_collision(False)
    c.set_actor_scale3d(unreal.Vector(e.x * 2 / ex.x * 1.02, e.y * 2 / ex.y * 1.02, e.z * 2 / ex.z * 1.02))
    c.set_actor_label('ArtCrate_' + blk.get_actor_label())
    c.set_folder_path('Art_Blocks')
    c.tags = [unreal.Name('VisFinal'), unreal.Name('NoGreybox')]
    c.attach_to_actor(blk, '', unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD,
                      unreal.AttachmentRule.KEEP_WORLD, False)
    if 'VisGrey' not in [str(t) for t in blk.tags]:
        blk.tags = list(blk.tags) + [unreal.Name('VisGrey')]
    return c


def add_block():
    return _add_mover('L', 'Add Block')


def add_thin_block():
    return _add_mover('M', 'Add Thin Block')


def add_enemy():
    return _add_mover('Enemy', 'Add Enemy')


def renumber_path_from_selection():
    """Ctrl-click the path nodes in walking order (first = start A, last = B), then run this: they become
    PathA_00, PathA_01 ... Nodes of the same chain that were not selected stop being path nodes
    (renamed UnusedNode_NN, kept so nothing is lost). Fixes nodes duplicated with Alt-drag, whose labels
    (PathA_3 ...) break the order."""
    sel = [a for a in _eas().get_selected_level_actors() if 'PathNode' in [str(t) for t in a.tags]]
    if len(sel) < 2:
        raise RuntimeError('Select at least two path nodes, in walking order (Ctrl-click), then run this again.')
    chain = (_node_key(sel[0]) or ('A', 0))[0]
    ids = set(id(a) for a in sel)
    others = [a for a in _actors() if 'PathNode' in [str(t) for t in a.tags]
              and (_node_key(a) or ('', 0))[0] == chain and id(a) not in ids]
    if others:
        ok = unreal.EditorDialog.show_message(
            'Renumber Path', f'{len(sel)} node(s) selected. {len(others)} other Path{chain} node(s) are not selected '
            f'and will be set aside as UnusedNode.\n\nContinue?', unreal.AppMsgType.YES_NO)
        if ok != unreal.AppReturnType.YES:
            return
    with unreal.ScopedEditorTransaction('Renumber Path'):
        n = 0
        for a in _actors():
            k = _node_key(a) if 'PathNode' in [str(t) for t in a.tags] else None
            if k and k[0] == chain and id(a) not in ids:
                a.tags = [unreal.Name('UnusedNode')]
                a.set_actor_label(f'UnusedNode_{n:02d}')
                n += 1
        for i, a in enumerate(sel):
            a.set_actor_label(f'Path{chain}_{i:02d}#')          # temporary, avoids clashes
        for i, a in enumerate(sel):
            a.set_actor_label(f'Path{chain}_{i:02d}')
    r = rebuild(save=False)
    msg = f'Path{chain}: {len(sel)} nodes in selection order; {n} unused node(s) set aside.'
    if r['warnings']:
        msg += '\n\nWarnings:\n- ' + '\n- '.join(r['warnings'])
    unreal.EditorDialog.show_message('Renumber Path', msg, unreal.AppMsgType.OK)


def rebuild_from_menu():
    try:
        with unreal.ScopedEditorTransaction('Rebuild Level From Markers'):
            r = rebuild()
        msg = f"Rebuilt: {r['cells']} cells, {r['stairs']} stairs, top tier {r['tiers']}, {r['carved']} pocket(s) carved."
        if r['warnings']:
            msg += '\n\nWarnings:\n- ' + '\n- '.join(r['warnings'])
        unreal.EditorDialog.show_message('Rebuild Level', msg, unreal.AppMsgType.OK)
    except Exception as e:
        unreal.EditorDialog.show_message('Rebuild Level', str(e), unreal.AppMsgType.OK)


def _run(fn):
    try:
        fn()
    except Exception as e:
        unreal.EditorDialog.show_message('Puzzle tools', str(e), unreal.AppMsgType.OK)
