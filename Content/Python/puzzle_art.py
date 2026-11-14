"""Art pass: dresses a marker-built puzzle level with the MegaJam meshes (/Game/Dev/Meshes).

The grey-box cubes in folder "Maze" stay as the collision / NavMesh geometry; where an art mesh covers a
cube, the cube is only made invisible. Art actors live in folder "Art", have no collision and never affect
navigation, so they are rebuilt from scratch every time (Puzzle > Apply Art, or automatically after
Rebuild on levels whose Editor_Grid has the tag "Art").

  stairs        -> SM_PinkStone01 (2x2x2 cells, the tier height must be 350: Editor_Grid tag TierH:350)
  inner walls   -> SM_StonePlatform01 stacked per tier on wall cells that touch the walkway
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


def _place(label, path, cx, cy, z, size, yaw, folder='Art'):
    """Spawns `path` so its bounds fill `size` (sx, sy, sz in cm, before yaw), centred on cx, cy, bottom at z."""
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
    return a


def _set_visible(a, on):
    smc = a.static_mesh_component
    if smc.is_visible() != on:
        smc.set_visibility(on, False)


def clear_art():
    for a in list(T._actors()):
        if T._folder(a) == 'Art':
            T._eas().destroy_actor(a)
    for a in T._actors():
        if T._folder(a) == 'Maze' and isinstance(a, unreal.StaticMeshActor):
            _set_visible(a, True)


def apply_art(seed=7):
    rng = random.Random(seed)
    grid = T.get_grid()
    C, U = T.C, T.U
    nodes, fm, holes, movers = T.read_markers(grid)
    floor, stairs, pits, _c, _w = T.compute_layout(grid, nodes, fm, holes, movers)
    specs, (r0, r1, c0, c1) = T.geometry_specs(floor, pits, stairs, grid)
    clear_art()
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
        _place(f'Art_Stair_r{rc[0]}_c{rc[1]}', STAIR, x, y, min(h0, h1), (C, C, abs(h1 - h0)), yaw)
        for lab, a in maze.items():
            if lab.startswith(f'Maze_Stair_r{rc[0]}_c{rc[1]}_'):
                _set_visible(a, False)
        n += 1
    # inner walls: stone platforms stacked tier by tier on wall cells that touch the walkway
    for lab, (x0, y0, sx, sy, top, _m, tags) in specs.items():
        if not lab.startswith('Maze_Wall_'):
            continue
        r, c = (int(v[1:]) for v in lab[len('Maze_Wall_'):].split('_'))
        nb = [walk[(r + dr, c + dc)] for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (r + dr, c + dc) in walk]
        if not nb:
            continue
        low = min(nb) - U                         # visible from one tier below the lowest neighbour
        z = top
        k = 0
        while z > low and k < 4:
            h = min(U, z - low) if k else min(U, top - T.BASE)
            _place(f'Art_Wall_r{r}_c{c}_{k}', PLATFORM, x0 + C / 2, y0 + C / 2, z - h, (C, C, h),
                   rng.choice((0, 90, 180, 270)))
            z -= h
            k += 1
        if k and lab in maze:
            _set_visible(maze[lab], False)
        n += k
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
    _place('Art_Portal', PORTAL, x, y, b_t * U, (C * 1.4, C * 0.6, C * 1.0), face)
    n += 1
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return n


def apply_from_menu():
    try:
        n = apply_art()
        unreal.EditorDialog.show_message('Apply Art', f'Placed {n} art meshes (folder "Art").', unreal.AppMsgType.OK)
    except Exception as e:
        unreal.EditorDialog.show_message('Apply Art', f'Failed: {e}', unreal.AppMsgType.OK)
