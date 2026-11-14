"""Random generator for the block tutorial level (v2: winding terraces).

Each seed builds a different winding path: random straight segments (3-12 cells) with turns,
corridors kept at least 3 cells apart, and ~13 stairs that climb about 10 tiers (175 cm each),
with one short descent. Tutorial modules are always placed along the path in teaching order:
  Move   - drag the block that blocks the corridor away
  Fill1  - fill a hole with a 2x2 block
  Fill2  - fill a hole with two 1x2 blocks
  Fork   - short branch passes an enemy pen, long loop is safe: block the short branch
  Seal   - seal an enemy inside its alcove
  Final  - fill a hole + rotate the corridor blocker 90 deg to seal an enemy alcove
Walls between corridors drop to the lower side, so higher corridors read as terraces.

Usage (editor): open a level whose name contains "BlockTutorial", then
  Puzzle > Generate Random Block Tutorial   (or the toolbar button)
"""
import math
import random
import unreal
import puzzle_level_tools as T

C = 350.0          # cell size (2 units)
U = 175.0          # unit / tier height
BASE = -440.0
AGGRO = 900.0
L_SCALE = (3.5, 3.5, 1.75)
M_SCALE = (1.75, 3.5, 1.75)
HINTS = {
    'Move': '1. Drag the purple block out of the way',
    'Fill1': '2. Fill the hole - blocks keep their shape',
    'Fill2': '3. Two thin blocks fill one hole',
    'Fork': '4. Shortest path is not always safe!\nBlock the branch next to the red enemy',
    'Seal': '5. Enemies need a path to reach you\nSeal them inside their alcove',
    'Final': '6. Final: fill, then ROTATE (E) the blocker\nto seal the enemy',
}

# ---------------------------------------------------------------- layout planning (pure python)
DIRS = [(0, 1), (1, 0), (0, -1), (-1, 0)]   # (dr, dc)
MODS = [('Move', 3), ('Fill1', 3), ('Fill2', 3), ('Fork', 7), ('Seal', 3), ('Final', 5)]


def _walk(rng, R, Cn, target):
    for _ in range(400):
        r, c = rng.randint(2, 4), rng.randint(2, 4)
        d = rng.choice([(0, 1), (1, 0)])
        path = [(r, c)]
        occ = {(r, c): 0}
        stuck = 0
        while len(path) < target and stuck < 30:
            L = rng.choice([3, 4, 5, 6, 7, 8, 10, 11, 12])
            if len(path) > 1:
                nd = rng.choice([(d[1], -d[0]), (-d[1], d[0])])
            else:
                nd = d
            new = []
            cr, cc = path[-1]
            ok = True
            for _i in range(L):
                cr, cc = cr + nd[0], cc + nd[1]
                if not (1 <= cr < R - 1 and 1 <= cc < Cn - 1):
                    ok = False; break
                n = len(path) + len(new)
                for (pr, pc), idx in occ.items():
                    gap = max(abs(pr - cr), abs(pc - cc))
                    if idx >= n - 4:
                        continue
                    if gap < 3:
                        ok = False; break
                if not ok:
                    break
                for (pr, pc) in new[:-2]:
                    pass
                new.append((cr, cc))
            if ok and len(new) == L:
                for p in new:
                    occ[p] = len(path); path.append(p)
                d = nd; stuck = 0
            else:
                stuck += 1
        if len(path) >= target:
            return path
    return None


def plan(seed):
    rng = random.Random(seed)
    for attempt in range(60):
        R, Cn = rng.randint(26, 30), rng.randint(26, 30)
        path = _walk(rng, R, Cn, rng.randint(125, 150))
        if not path:
            continue
        P = _place(rng, path, R, Cn)
        if P:
            P.update(seed=seed, rows=R, cols=Cn)
            return P
    raise RuntimeError('could not plan level for seed %s' % seed)


def _dir(a, b): return (b[0] - a[0], b[1] - a[1])


def _place(rng, path, R, Cn):
    n = len(path)
    pidx = {p: i for i, p in enumerate(path)}
    dirs = [None] + [_dir(path[i - 1], path[i]) for i in range(1, n)]

    def straight(i, j):  # cells i..j and the step into i and out of j share one direction
        if i < 1 or j + 1 >= n:
            return False
        d = dirs[i]
        return all(dirs[k] == d for k in range(i, j + 2))

    claimed = {}           # side cell -> module index
    runs = []              # (start, end)
    danger = []            # (r, c) of free-roaming enemies with exclusion radius
    mods = []
    total_w = sum(w for _, w in MODS)
    spacing = (n - 6 - total_w) / (len(MODS) + 1)
    cursor = 2
    for mi, (name, w) in enumerate(MODS):
        start_min = int(cursor + max(2, spacing * rng.uniform(0.5, 1.1)))
        placed = None
        for i in range(start_min, n - w - 2):
            if not straight(i, i + w - 1):
                continue
            if any(not (i + w + 1 < a or i > b + 1) for a, b in runs):
                continue
            d = dirs[i]
            for s in rng.sample((-1, 1), 2):
                perp = (d[1] * s, -d[0] * s)   # +s side
                def cell(q, k):
                    pr, pc = path[i + q]
                    return (pr + perp[0] * k, pc + perp[1] * k)
                sides = _sides(name, cell)
                if sides is None or not _claim_ok(sides, set(path[i:i + w]), path, pidx, claimed, R, Cn, danger):
                    continue
                placed = (i, s, sides, cell)
                break
            if placed:
                break
        if not placed:
            return None
        i, s, sides, cell = placed
        for c in sides:
            claimed[c] = mi
        runs.append((i, i + w - 1))
        if name == 'Fork':
            en = cell(3, -1)
            for p in path:
                k = pidx[p]
                if i + 1 <= k <= i + 5:
                    continue
                if math.dist(p, en) < 2.7:
                    return None
            danger.append(en)
        mods.append((name, i, w, s))
        cursor = i + w
    # stairs: spread over the free straight cells, mostly climbing to ~10 tiers
    cand = [j for j in range(2, n - 2) if straight(j, j) and straight(j - 1, j + 1)
            and all(j < a - 1 or j > b + 1 for a, b in runs)]
    want = rng.randint(13, 15)
    stairs = []
    if len(cand) < want:
        return None
    seg = len(cand) / want
    for k in range(want):
        lo, hi = int(k * seg), max(int(k * seg) + 1, int((k + 1) * seg) - 1)
        j = cand[rng.randint(lo, min(hi, len(cand) - 1))]
        if stairs and j - stairs[-1] < 3:
            continue
        stairs.append(j)
    if len(stairs) < want - 2:
        return None
    downs = set(rng.sample(stairs[3:-1], 1 if len(stairs) > 5 else 0))
    h, hs = 0, []
    stair_info = {}
    for j in range(n):
        if j in stairs:
            nh = h - 1 if (j in downs and h >= 1) else h + 1
            stair_info[j] = (h, nh)
            h = nh
        hs.append(h)
    return {'path': path, 'heights': hs, 'stairs': stair_info, 'mods': mods, 'dirs': dirs}


def _sides(name, cell):
    if name == 'Move':
        return [cell(2, 1)]
    if name == 'Fill1':
        return [cell(0, 1)]
    if name == 'Fill2':
        return [cell(0, 1), cell(2, -1)]
    if name == 'Fork':
        return [cell(3, -1), cell(0, -1), cell(0, 1), cell(6, 1)] + [cell(q, 2) for q in range(7)]
    if name == 'Seal':
        return [cell(1, 1), cell(1, 2), cell(1, -1)]
    if name == 'Final':
        return [cell(1, 1), cell(4, -1), cell(4, -2)]


def _claim_ok(sides, own_run, path, pidx, claimed, R, Cn, danger):
    S = set(sides)
    for (r, c) in sides:
        if not (1 <= r < R - 1 and 1 <= c < Cn - 1):
            return False
        if (r, c) in pidx or (r, c) in claimed:
            return False
        for dr, dc in DIRS:
            nb = (r + dr, c + dc)
            if nb in S or nb in own_run:
                continue
            if nb in pidx or nb in claimed:
                return False
        for e in danger:
            if math.dist((r, c), e) < 2.7:
                return False
    return True


# ---------------------------------------------------------------- building the level
def generate(seed=None):
    if seed is None:
        seed = random.randint(0, 999999)
    P = plan(seed)
    path, hs, stairs, mods, dirs = P['path'], P['heights'], P['stairs'], P['mods'], P['dirs']
    ROWS, COLS = P['rows'], P['cols']
    X0, Y0 = -COLS * C / 2, -ROWS * C / 2

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if 'BlockTutorial' not in world.get_path_name():
        raise RuntimeError('Open a BlockTutorial level first (this regenerates the open level).')
    ob = unreal.load_asset('/Game/Project/Programming/Blueprints/Pathfinding/BP_EditableObstacle').generated_class()
    en = unreal.load_asset('/Game/Project/Programming/Blueprints/Pathfinding/BP_EnemyBlock').generated_class()

    def mn(rc): return X0 + rc[1] * C, Y0 + rc[0] * C
    def ctr(rc): x, y = mn(rc); return x + C / 2, y + C / 2
    def wvec(d): return d[1], d[0]                       # (dr, dc) -> world (x, y)
    def yaw_thin(d): return 0 if d[1] != 0 else 90       # M block is thin along local X

    floor, pits, blocks, sol, hints = {}, {}, [], {}, []
    for i, rc in enumerate(path):
        if i not in stairs:
            floor[rc] = hs[i] * U

    for name, i, w, s in mods:
        d = dirs[i]
        f = wvec(d)
        perp = (d[1] * s, -d[0] * s)
        pw = wvec(perp)
        h = hs[i] * U
        def cell(q, k=0):
            r, c = path[i + q]
            return (r + perp[0] * k, c + perp[1] * k)
        def at(rc, along=0.0, side=0.0):
            x, y = ctr(rc)
            return (x + f[0] * along + pw[0] * side, y + f[1] * along + pw[1] * side, h)
        yf, yp = yaw_thin(d), yaw_thin(perp)
        hx, hy, _ = at(cell(w // 2))
        hints.append((HINTS[name], hx, hy, h + 330))
        if name == 'Move':
            floor[cell(2, 1)] = h
            blocks.append(('Block_Move_Blocker', ob, at(cell(1), 87.5), M_SCALE, yf))
            sol['Block_Move_Blocker'] = at(cell(2, 1), 87.5) + (yf,)
        elif name == 'Fill1':
            pits[cell(1)] = h
            floor[cell(0, 1)] = h
            blocks.append(('Block_Fill1_L', ob, at(cell(0, 1)), L_SCALE, 0))
            x, y, _ = at(cell(1)); sol['Block_Fill1_L'] = (x, y, h - U, 0)
        elif name == 'Fill2':
            pits[cell(1)] = h
            floor[cell(0, 1)] = h
            floor[cell(2, -1)] = h
            blocks.append(('Block_Fill2_Ma', ob, at(cell(0, 1), -87.5), M_SCALE, yf))
            blocks.append(('Block_Fill2_Mb', ob, at(cell(2, -1), 87.5), M_SCALE, yf))
            x, y, _ = at(cell(1), -87.5); sol['Block_Fill2_Ma'] = (x, y, h - U, yf)
            x, y, _ = at(cell(1), 87.5); sol['Block_Fill2_Mb'] = (x, y, h - U, yf)
        elif name == 'Fork':
            for rc in [cell(3, -1), cell(0, -1), cell(0, 1), cell(6, 1)] + [cell(q, 2) for q in range(7)]:
                floor[rc] = h
            blocks.append(('Enemy_Fork', en, at(cell(3, -1)), M_SCALE, 0))
            blocks.append(('Block_Fork_Gate', ob, at(cell(0, -1)), M_SCALE, yf))
            sol['Block_Fork_Gate'] = at(cell(1)) + (yf,)
        elif name == 'Seal':
            for rc in (cell(1, 1), cell(1, 2), cell(1, -1)):
                floor[rc] = h
            blocks.append(('Enemy_Seal', en, at(cell(1, 2)), M_SCALE, 0))
            blocks.append(('Block_Seal_L', ob, at(cell(1, -1)), L_SCALE, 0))
            sol['Block_Seal_L'] = at(cell(1, 1)) + (0,)
        elif name == 'Final':
            pits[cell(2)] = h
            for rc in (cell(1, 1), cell(4, -1), cell(4, -2)):
                floor[rc] = h
            blocks.append(('Block_Final_Blocker', ob, at(cell(0), 87.5), M_SCALE, yf))
            blocks.append(('Block_Final_L', ob, at(cell(1, 1)), L_SCALE, 0))
            blocks.append(('Enemy_Final', en, at(cell(4, -2)), M_SCALE, 0))
            x, y, _ = at(cell(2)); sol['Block_Final_L'] = (x, y, h - U, 0)
            # rotated blocker closes the half of the alcove mouth nearest the corridor
            sol['Block_Final_Blocker'] = at(cell(4, -1), 0, 87.5) + (yp,)
    for rc in pits:
        floor.pop(rc, None)

    # ---- write the editable markers, then build the geometry from them (same code as Rebuild)
    T.clear_all()
    grid = (X0, Y0)
    T.set_grid(X0, Y0)
    n = len(path)
    keep = {0, n - 1}
    for i in range(1, n - 1):
        if dirs[i] != dirs[i + 1]:
            keep.add(i)                      # corners
    for j in stairs:
        keep.update((j - 1, j + 1))          # a node on each side of a stair fixes its position
    chain_cells = set(path)
    for k, i in enumerate(sorted(keep)):
        T.spawn_node('A', k, path[i], hs[i], grid)
    for name, i, w, s in mods:
        if name != 'Fork':
            continue
        d = dirs[i]
        perp = (d[1] * s, -d[0] * s)
        pts = [path[i], (path[i][0] + 2 * perp[0], path[i][1] + 2 * perp[1]),
               (path[i + 6][0] + 2 * perp[0], path[i + 6][1] + 2 * perp[1]), path[i + 6]]
        for k, rc in enumerate(pts):
            T.spawn_node('B', k, rc, hs[i], grid)
        for p0, p1 in zip(pts, pts[1:]):
            chain_cells.update(c for c, _d in T.route(p0, p1))
    for rc, h in floor.items():
        if rc not in chain_cells:
            T.spawn_floor(rc, int(round(h / U)), grid)
    for rc, h in pits.items():
        T.spawn_hole(rc, int(round(h / U)), grid)

    for label, cls, (x, y, z), scale, yaw in blocks:
        a = eas.spawn_actor_from_class(cls, unreal.Vector(x, y, z), unreal.Rotator(0, 0, yaw))
        a.set_actor_scale3d(unreal.Vector(*scale))
        a.set_actor_label(label); a.set_folder_path('Blocks')
        a.tags = [unreal.Name('Editable')]
        if cls == en:
            a.set_editor_property('AggroRadius', AGGRO)

    actors = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
    sx, sy = ctr(path[0])

    look = unreal.Vector(sx + 1400, sy + 700, hs[0] * U)
    cam_loc = unreal.Vector(look.x - 1300, look.y - 2400, look.z + 2500)
    rot = unreal.MathLibrary.find_look_at_rotation(cam_loc, look)
    actors['OverviewCamera'].set_actor_location(cam_loc, False, False)
    actors['OverviewCamera'].set_actor_rotation(rot, False)
    unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(cam_loc, rot)

    tmat = unreal.load_asset('/Engine/EngineMaterials/DefaultTextMaterialOpaque')
    for i, (text, x, y, z) in enumerate(hints):
        t = eas.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(x, y, z),
                                       unreal.Rotator(roll=0, pitch=-rot.pitch, yaw=rot.yaw + 180))
        tr = t.text_render
        tr.set_editor_property('text', text)
        tr.set_editor_property('world_size', 70.0)
        tr.set_editor_property('horizontal_alignment', unreal.HorizTextAligment.EHTA_CENTER)
        tr.set_editor_property('text_render_color', unreal.Color(255, 235, 150, 255))
        if tmat:
            tr.set_material(0, tmat)
        t.set_actor_label(f'Hint_{i + 1}'); t.set_folder_path('Hints')

    res = T.rebuild(save=False)          # walls / floors / stairs / pits, Point A/B, NavMesh
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    unreal.log(f'[BlockTutorialGen] seed={seed} size={COLS}x{ROWS} tiers={max(hs)}')
    return {'seed': seed, 'solution': sol, 'tiers': max(hs), 'warnings': res['warnings'], 'size': (COLS, ROWS), 'length': len(path)}


def generate_from_menu():
    try:
        r = generate()
        unreal.EditorDialog.show_message('Block Tutorial', f"Generated seed {r['seed']}  ({r['size'][0]}x{r['size'][1]} cells, {r['tiers']} tiers, path {r['length']})", unreal.AppMsgType.OK)
    except Exception as e:
        unreal.EditorDialog.show_message('Block Tutorial', str(e), unreal.AppMsgType.OK)
