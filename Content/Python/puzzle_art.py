"""Art pass: dresses a marker-built puzzle level with the MegaJam meshes (/Game/Dev/Meshes).

Two views of one level (see view_mode.py): the grey box (folder "Maze" = collision / NavMesh, plus "GB_"
proxies in "Greybox" generated from the art) and the final render (folder "Art", no collision).
Generated art carries the tags VisFinal + ArtAuto + Gen:<transform>. Apply Art regenerates only untouched
ArtAuto pieces: a piece a designer moved / rotated / scaled is locked automatically, a slot whose piece was
deleted or replaced by hand is never filled again (remembered on the Art_Registry actor), and anything placed
by hand in "Art" is left alone. Puzzle > Reset Selected Art brings a slot back to the automatic version.

  stairs        -> SM_PinkStone01 (2x2x2 cells, the tier height must be 350: Editor_Grid tag TierH:350)
  path floor    -> SM_StonePlatform01 under every walkable cell
  path sides    -> every edge next to a wall cell; runs of 3 / 2 / 1 cells use SM_StoneWall01 / StoneWallDecor /
                   StoneWallWindow at ~native scale, flush with the walkway; runs overlap at corners
  stair sides   -> SM_StoneWallDamaged (sloped) over the flat cell + stair cell, outside the stair
  wall tops far from the path get a few SM_StoneCliff01/02
  outer edge    -> SM_StoneWall01 / Damaged / Decor / Window segments, 3 cells long
  point B       -> SM_Portal facing the path
"""
import random
import unreal
import puzzle_level_tools as T

M = '/Game/Dev/Meshes/'
STAIR = M + 'SM_PinkStone01'
PLATFORM = M + 'SM_StonePlatform01'
WALLS = [M + 'SM_StoneWall01', M + 'SM_StoneWall01', M + 'SM_StoneWallDamaged', M + 'SM_StoneWallDecor',
         M + 'SM_StoneWallWindow']
PORTAL = M + 'SM_Portal'
PIECES = {3: M + 'SM_StoneWall01', 1: M + 'SM_StoneWallWindow'}   # wall piece per run length (cells)
PIECES_2 = [M + 'SM_StoneWallDecor']
RAMP = M + 'SM_StoneWallDamaged'   # sloped wall: the side of a stair (flat cell + stair cell), unscaled
RAMP_YAW = 180.0      # relative to the climb direction
RAMP_ALONG = -140.0   # pivot offset from the stair cell centre along the climb (towards the flat cell)
RAMP_LAT_C = -11.5    # pivot offset to the right of the climb (mesh is not symmetric)
RAMP_LAT = 254.5      # distance of each side's pivot from the centre line
OVERLAP = 60          # runs reach into the corner so two perpendicular walls intersect
CLIFFS = [M + 'SM_StoneCliff01', M + 'SM_StoneCliff02']
STAIR_YAW = -90.0     # SM_PinkStone01 climbs towards +Y at yaw 0
PORTAL_YAW = 90.0     # SM_Portal faces -Y at yaw 0
WALL_YAW = 0.0        # SM_StoneWall01 runs along X

_SIZE = {}


def _mesh(path):
    m = T._asset(path)
    if path not in _SIZE:
        b = m.get_bounding_box()
        _SIZE[path] = (b.min, b.max)
    return m


_CTX = {'skip': set(), 'made': []}


def _sig(a):
    l, r, s = a.get_actor_location(), a.get_actor_rotation(), a.get_actor_scale3d()
    return f'{l.x:.0f},{l.y:.0f},{l.z:.0f},{r.yaw % 360:.0f},{s.x:.3f},{s.y:.3f},{s.z:.3f}'


def _tag_auto(a, label, extra=()):
    """Generated art: VisFinal (shown in the final view), ArtAuto (may be regenerated) and the generated
    transform, so a later Apply Art can tell whether a designer has touched it."""
    a.tags = [unreal.Name(t) for t in ('VisFinal', 'ArtAuto', 'Gen:' + _sig(a)) + tuple(extra)]
    _CTX['made'].append(label)


def _place(label, path, cx, cy, z, size, yaw, folder='Art', extra=()):
    """Spawns `path` so its bounds fill `size` (sx, sy, sz in cm, before yaw), centred on cx, cy, bottom at z."""
    if label in _CTX['skip']:
        return None
    m = _mesh(path)
    mn, mx = _SIZE[path]
    ex, ey, ez = mx.x - mn.x, mx.y - mn.y, mx.z - mn.z
    s = unreal.Vector(size[0] / ex, size[1] / ey, size[2] / ez)
    # offset of the bounds centre from the pivot, scaled and rotated
    ox, oy = (mn.x + mx.x) / 2 * s.x, (mn.y + mx.y) / 2 * s.y
    q = int(round(yaw / 90.0)) % 4
    rx, ry = [(ox, oy), (-oy, ox), (-ox, -oy), (oy, -ox)][q]
    a = T._eas().spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(cx - rx, cy - ry, z - mn.z * s.z),
                                        unreal.Rotator(0, 0, yaw))
    smc = a.static_mesh_component
    smc.set_static_mesh(m)
    smc.set_collision_profile_name('NoCollision')
    smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    smc.set_editor_property('can_ever_affect_navigation', False)
    a.set_actor_enable_collision(False)
    a.set_actor_scale3d(s)
    a.set_actor_label(label)
    a.set_folder_path(folder)
    _tag_auto(a, label, extra)
    return a


def _place_raw(label, path, x, y, z, yaw, folder='Art'):
    """Spawns `path` unscaled with its pivot at x, y, z."""
    if label in _CTX['skip']:
        return None
    a = T._eas().spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, z), unreal.Rotator(0, 0, yaw))
    smc = a.static_mesh_component
    smc.set_static_mesh(_mesh(path))
    smc.set_collision_profile_name('NoCollision')
    smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    smc.set_editor_property('can_ever_affect_navigation', False)
    a.set_actor_enable_collision(False)
    a.set_actor_label(label)
    a.set_folder_path(folder)
    _tag_auto(a, label)
    return a


def _set_visible(a, on):
    smc = a.static_mesh_component
    if smc.is_visible() != on:
        smc.set_visibility(on, False)


REGISTRY = 'Art_Registry'


def _registry():
    for a in T._actors():
        if a.get_actor_label() == REGISTRY:
            return a
    a = T._eas().spawn_actor_from_class(unreal.TargetPoint, unreal.Vector(0, 0, -5000))
    a.set_actor_label(REGISTRY)
    a.set_folder_path('Editor')
    return a


def _grey_only(a):
    """A grey-box cube covered by art: shown in the grey view only (collision stays on)."""
    _set_visible(a, True)
    if 'VisGrey' not in [str(t) for t in a.tags]:
        a.tags = list(a.tags) + [unreal.Name('VisGrey')]


def prepare_art():
    """Before regenerating: generated pieces a designer moved / rotated / scaled lose ArtAuto (locked, kept);
    untouched generated pieces are removed to be rebuilt; slots that were generated before but whose piece
    is gone (deleted or replaced by hand) are remembered and not filled again. Returns the registry actor."""
    reg = _registry()
    slots = set(str(t)[5:] for t in reg.tags if str(t).startswith('Slot:'))
    present, locked, regen = set(), [], set()
    for a in list(T._actors()):
        if T._folder(a) != 'Art':
            continue
        lab = a.get_actor_label()
        tags = [str(t) for t in a.tags]
        if 'ArtAuto' in tags:
            gen = next((t[4:] for t in tags if t.startswith('Gen:')), None)
            if gen is not None and gen != _sig(a):    # touched by a designer: lock it
                a.tags = [unreal.Name(t) for t in tags if t != 'ArtAuto' and not t.startswith('Gen:')]
                locked.append(lab)
                present.add(lab)
            else:                                     # untouched: rebuild it
                regen.add(lab)
                T._eas().destroy_actor(a)
            continue
        present.add(lab)
        if 'VisFinal' not in tags:                    # anything placed by hand in "Art" is final-view art
            a.tags = list(a.tags) + [unreal.Name('VisFinal')]
    removed = slots - present - regen                 # generated before, now gone: deleted / replaced by hand
    _CTX['skip'] = (slots & present) | removed
    _CTX['made'] = []
    for a in T._actors():                          # grey-only tags are recomputed below
        if T._folder(a) == 'Maze' and 'VisGrey' in [str(t) for t in a.tags]:
            a.tags = [t for t in a.tags if str(t) != 'VisGrey']
            _set_visible(a, True)
    return reg, locked, removed


def apply_art(seed=7):
    rng = random.Random(seed)
    grid = T.get_grid()
    C, U = T.C, T.U
    nodes, fm, holes, movers = T.read_markers(grid)
    floor, stairs, pits, _c, _w = T.compute_layout(grid, nodes, fm, holes, movers)
    specs, (r0, r1, c0, c1) = T.geometry_specs(floor, pits, stairs, grid)
    reg, locked, removed = prepare_art()
    maze = {a.get_actor_label(): a for a in T._actors() if T._folder(a) == 'Maze'}
    walk = dict(floor)
    walk.update(pits)
    for rc, (h0, h1, _d) in stairs.items():
        walk[rc] = max(h0, h1)
    n = 0
    # stairs: one 2x2x2 stone staircase per stair cell
    for rc, (h0, h1, d) in stairs.items():
        x, y = T.cell_ctr(rc, grid)
        up = d if h1 > h0 else (-d[0], -d[1])          # direction the stair climbs (row, col)
        yaw = {(0, 1): 0, (1, 0): 90, (0, -1): 180, (-1, 0): 270}[up] + STAIR_YAW
        _place(f'Art_Stair_r{rc[0]}_c{rc[1]}', STAIR, x, y, min(h0, h1), (C, C, abs(h1 - h0)), yaw, extra=('NoGreybox',))
        for lab, a in maze.items():
            if lab.startswith(f'Maze_Stair_r{rc[0]}_c{rc[1]}_'):
                _grey_only(a)
        n += 1
    # path blocks: a stone platform under every walkable floor cell (grey cube stays below for collision)
    # (the cube is hidden but keeps its collision; platforms stack down to the lowest neighbouring ground)
    for rc, h in floor.items():
        x, y = T.cell_ctr(rc, grid)
        nb = [walk[(rc[0] + dr, rc[1] + dc)] for dr in (-1, 0, 1) for dc in (-1, 0, 1)
              if (rc[0] + dr, rc[1] + dc) in walk]
        low = min(nb + [h]) - U
        z, k = h, 0
        while z > low and k < 4:
            _place(f'Art_Path_r{rc[0]}_c{rc[1]}_{k}', PLATFORM, x, y, z - U, (C, C, U), rng.choice((0, 90, 180, 270)),
                   extra=('NoGreybox',))
            z -= U
            k += 1
        cube = maze.get(f'Maze_Path_r{rc[0]}_c{rc[1]}')
        if cube:
            _grey_only(cube)
        n += k
    # stone walls only on the open (lower) side of the walkway, like the reference layout: the high side
    # is already closed by the grey terrace. Consecutive edges become one run, filled with unscaled
    # pieces: 3 cells -> SM_StoneWall01, 2 -> SM_StoneWallDecor / Damaged, 1 -> SM_StoneWallWindow.
    ortho = ((0, 1), (1, 0), (0, -1), (-1, 0))
    wall_tops = {}
    for lab, sp in specs.items():
        if lab.startswith('Maze_Wall_'):
            r, c = (int(v[1:]) for v in lab[len('Maze_Wall_'):].split('_'))
            wall_tops[(r, c)] = sp[4]
    portal_edge = None
    lst = nodes['A']
    _seg = T.route(lst[-2][1], lst[-1][1])
    if _seg:
        portal_edge = (lst[-1][1], _seg[-1][1])
    runs = {}
    ramp_cover = set()                                  # (cell, side) already covered by a stair ramp wall
    for rc, (h0, h1, sd) in stairs.items():
        up = sd if h1 > h0 else (-sd[0], -sd[1])
        low_cell = (rc[0] - up[0], rc[1] - up[1])
        for side in ((up[1], up[0]), (-up[1], -up[0])):      # the two sides perpendicular to the climb
            if (rc[0] + side[0], rc[1] + side[1]) not in wall_tops:
                continue
            if (low_cell[0] + side[0], low_cell[1] + side[1]) not in wall_tops:
                continue                                # path turns at the foot of the stair: plain walls there
            ramp_cover.add((rc, side))
            ramp_cover.add((low_cell, side))
            # placement measured from the ramp the level designer adjusted by hand (stair r5_c4, scale 1)
            ux, uy = up[1], up[0]                       # climb direction in world X / Y
            rx, ry = uy, -ux                            # right of the climb
            sgn = side[1] * rx + side[0] * ry
            x, y = T.cell_ctr(rc, grid)
            lat = RAMP_LAT_C + sgn * RAMP_LAT
            cx = x + ux * RAMP_ALONG + rx * lat
            cy = y + uy * RAMP_ALONG + ry * lat
            yaw = {(1, 0): 0, (0, 1): 90, (-1, 0): 180, (0, -1): 270}[(ux, uy)] + RAMP_YAW
            m = _place_raw(f'Art_Ramp_r{rc[0]}_c{rc[1]}_{side[0]}{side[1]}', RAMP, cx, cy, min(h0, h1), yaw)
            n += 1
    for rc, h in walk.items():
        if rc in stairs:
            continue
        base = h
        for d in ortho:
            o = (rc[0] + d[0], rc[1] + d[1])
            if o not in wall_tops or (rc, d) == portal_edge or (rc, d) in ramp_cover:
                continue
            if d[0]:
                key = ('H', rc[0] + (1 if d[0] > 0 else 0), d[0], base)
                pos = rc[1]
            else:
                key = ('V', rc[1] + (1 if d[1] > 0 else 0), d[1], base)
                pos = rc[0]
            runs.setdefault(key, []).append(pos)
    for (axis, b, sign, base), ps in runs.items():
        ps.sort()
        groups, cur = [], [ps[0]]
        for q in ps[1:]:
            if q == cur[-1] + 1:
                cur.append(q)
            else:
                groups.append(cur)
                cur = [q]
        groups.append(cur)
        for g in groups:
            ln = len(g)
            parts = [3] * (ln // 3) + ([ln % 3] if ln % 3 else [])
            if parts[-1] == 1 and len(parts) > 1:      # 4 = 2 + 2 instead of 3 + 1
                parts[-2:] = [2, 2]
            a = g[0]
            for i, k in enumerate(parts):
                path = PIECES[k] if k != 2 else rng.choice(PIECES_2)
                _mesh(path)
                mn, mx = _SIZE[path]
                ex, ey, ez = mx.x - mn.x, mx.y - mn.y, mx.z - mn.z
                s = 1.0                                            # native size, no scaling
                length = ex
                along = (a + k / 2) * C + ((-OVERLAP if i == 0 else 0) + (OVERLAP if i == len(parts) - 1 else 0)) / 2
                across = b * C + sign * (ey * s / 2 - 10)       # flush against the walkway edge
                if axis == 'H':
                    x, y, yaw = grid[0] + along, grid[1] + across, 0
                else:
                    x, y, yaw = grid[0] + across, grid[1] + along, 90
                _place(f'Art_Side_{axis}{b}_{sign}_{a}_{int(base)}', path, x, y, base, (length, ey * s, ez * s),
                       yaw + rng.choice((0, 180)))
                a += k
                n += 1
    # a few cliffs as decoration on wall tops away from the walkway
    for (r, c), top in wall_tops.items():
        if any((r + dr, c + dc) in walk for dr in (-2, -1, 0, 1, 2) for dc in (-2, -1, 0, 1, 2)):
            continue
        if rng.random() < 0.12:
            x, y = T.cell_ctr((r, c), grid)
            _place(f'Art_Cliff_r{r}_c{c}', rng.choice(CLIFFS), x, y, top - 20, (C * 0.9, C * 0.9, 200),
                   rng.choice((0, 90, 180, 270)))
            n += 1
    # outer edge: decorated stone walls along the border, 3 cells per segment
    def edge(side, cells, fixed):
        nonlocal n
        for i in range(0, len(cells), 3):
            seg = cells[i:i + 3]
            if side in ('N', 'S'):
                r = fixed
                tops = [specs.get(f'Maze_Wall_r{r}_c{c}', (0, 0, 0, 0, 0))[4] for c in seg]
                x = grid[0] + (seg[0] + len(seg) / 2) * C
                y = grid[1] + (r + (0 if side == 'N' else 1)) * C
                yaw = WALL_YAW
            else:
                c = fixed
                tops = [specs.get(f'Maze_Wall_r{r}_c{c}', (0, 0, 0, 0, 0))[4] for r in seg]
                x = grid[0] + (c + (0 if side == 'W' else 1)) * C
                y = grid[1] + (seg[0] + len(seg) / 2) * C
                yaw = WALL_YAW + 90
            _place(f'Art_Edge_{side}_{fixed}_{i}', rng.choice(WALLS), x, y, max(tops), (len(seg) * C, 120, U), yaw)
            n += 1
    if not T.ISLAND:                                # island levels: terrain is cut away at the rim
        edge('N', list(range(c0, c1 + 1)), r0)
        edge('S', list(range(c0, c1 + 1)), r1)
        edge('W', list(range(r0, r1 + 1)), c0)
        edge('E', list(range(r0, r1 + 1)), c1)
    # portal at point B, one cell past the end of the path, facing back along it
    lst = nodes['A']
    (_i, b_rc, b_t, _l), prev = lst[-1], lst[-2][1]
    seg = T.route(prev, b_rc)
    d = seg[-1][1] if seg else (0, 1)
    pr = (b_rc[0] + d[0], b_rc[1] + d[1])
    x, y = T.cell_ctr(pr, grid)
    face = {(0, 1): 180, (1, 0): 270, (0, -1): 0, (-1, 0): 90}[d] + PORTAL_YAW  # face -d (towards the path)
    for a in list(T._actors()):                   # keep the way into the portal open
        if a.get_actor_label() == f'Art_Side_r{b_rc[0]}_c{b_rc[1]}_{d[0]}{d[1]}':
            T._eas().destroy_actor(a)
    _place('Art_Portal', PORTAL, x, y, b_t * U, (C * 1.4, C * 0.6, C * 1.0), face)
    n += 1
    known = set(str(t) for t in reg.tags)
    reg.tags = list(reg.tags) + [unreal.Name('Slot:' + l) for l in _CTX['made'] if 'Slot:' + l not in known]
    _CTX['last'] = {'placed': len(_CTX['made']), 'locked': locked, 'removed': sorted(removed)}
    import view_mode
    view_mode.sync_greybox()
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return len(_CTX['made'])


def reset_selected_art():
    """Selected generated pieces (or the slots they came from) go back to the automatic version."""
    reg = _registry()
    sel = [a for a in T._eas().get_selected_level_actors() if T._folder(a) == 'Art']
    labs = set(a.get_actor_label() for a in sel)
    for a in sel:
        T._eas().destroy_actor(a)
    reg.tags = [t for t in reg.tags if str(t)[5:] not in labs]   # forget them -> regenerated as new
    return apply_art()


def apply_from_menu():
    try:
        n = apply_art()
        info = _CTX['last']
        msg = f'Placed {n} generated art meshes (folder "Art").'
        if info['locked']:
            msg += f"\n\nNewly locked (you edited them, kept as they are): {len(info['locked'])}"
        if info['removed']:
            msg += f"\nSlots you deleted / replaced (not filled again): {len(info['removed'])}"
        unreal.EditorDialog.show_message('Apply Art', msg, unreal.AppMsgType.OK)
    except Exception as e:
        unreal.EditorDialog.show_message('Apply Art', f'Failed: {e}', unreal.AppMsgType.OK)
