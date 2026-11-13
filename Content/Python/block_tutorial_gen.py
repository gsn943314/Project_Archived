"""Random generator for the block tutorial level.

The layout is a snake of lanes; every lane climbs one tier (175 cm) and alternates direction.
Tutorial modules are always placed in the same teaching order, but lane length, gaps,
module sides and level length are random:
  Move   - drag the block that blocks the corridor away
  Fill1  - fill a hole with a 2x2 block
  Fill2  - fill a hole with two 1x2 blocks
  Fork   - short branch passes an enemy pen, long loop is safe: block the short branch
  Seal   - seal an enemy inside its alcove
  Final  - fill a hole + rotate the corridor blocker 90 deg to seal an enemy alcove

Usage (editor): open a level whose name contains "BlockTutorial", then
  Puzzle > Generate Random Block Tutorial   (or the toolbar button)
"""
import random
import unreal

C = 350.0          # cell size (2 units)
U = 175.0          # unit / tier height
BASE = -440.0
AGGRO = 900.0
MODULES = [('Move', 3), ('Fill1', 3), ('Fill2', 3), ('Fork', 7), ('Seal', 3), ('Final', 5)]
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


def plan(seed):
    """Pure layout planning (no Unreal calls) - returns a dict describing the level."""
    rng = random.Random(seed)
    W = rng.randint(17, 23)
    gap_lo, gap_hi = rng.choice([(1, 2), (1, 3), (2, 3), (2, 4)])
    lanes = [[]]
    pos = 2
    for name, width in MODULES:
        pos += rng.randint(gap_lo, gap_hi) if lanes[-1] else 0
        if pos + width > W - 2:
            lanes.append([])
            pos = 2 + rng.randint(0, 1)
        lanes[-1].append((name, pos, width, rng.choice((-1, 1))))
        pos += width
    nl = len(lanes)
    return {'seed': seed, 'W': W, 'lanes': lanes, 'rows': 5 * nl + 2, 'cols': W + 2}


def generate(seed=None):
    if seed is None:
        seed = random.randint(0, 999999)
    P = plan(seed)
    W, lanes, ROWS, COLS = P['W'], P['lanes'], P['rows'], P['cols']
    X0, Y0 = -COLS * C / 2, -ROWS * C / 2

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if 'BlockTutorial' not in world.get_path_name():
        raise RuntimeError('Open a BlockTutorial level first (this regenerates the open level).')
    for a in list(eas.get_all_level_actors()):
        if str(a.get_folder_path()) in ('Maze', 'Blocks', 'Gimmicks', 'Hints') and a.get_actor_label() != 'Maze_Backdrop':
            eas.destroy_actor(a)
        elif a.get_actor_label().startswith('Maze_Pillar'):
            eas.destroy_actor(a)

    cube = unreal.load_asset('/Game/LevelPrototyping/Meshes/SM_Cube')
    m_floor = unreal.load_asset('/Game/Project/Art/Materials/MI_MazeFloor')
    m_wall = unreal.load_asset('/Game/Project/Art/Materials/MI_MazeWall')
    m_pit = unreal.load_asset('/Game/Project/Art/Materials/MI_MazeBackdrop')
    ob = unreal.load_asset('/Game/Project/Programming/Blueprints/Pathfinding/BP_EditableObstacle').generated_class()
    en = unreal.load_asset('/Game/Project/Programming/Blueprints/Pathfinding/BP_EnemyBlock').generated_class()

    def mn(r, c): return X0 + c * C, Y0 + r * C
    def ctr(r, c): x, y = mn(r, c); return x + C / 2, y + C / 2

    def box(label, x0, y0, sx, sy, top, mat, tags=()):
        a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x0, y0, BASE))
        smc = a.static_mesh_component
        smc.set_static_mesh(cube)
        smc.set_material(0, mat)
        a.set_actor_scale3d(unreal.Vector(sx / 100, sy / 100, (top - BASE) / 100))
        a.set_actor_label(label)
        a.set_folder_path('Maze')
        a.tags = [unreal.Name(t) for t in tags]

    path, pits, stairs, blocks, sol, hints = {}, {}, {}, [], {}, []

    def lane_col(k, p): return 1 + p if k % 2 == 0 else W - p
    def lane_dx(k): return 1 if k % 2 == 0 else -1

    for k, mods in enumerate(lanes):
        h = k * U
        cr = 1 + 5 * k + 2
        for p in range(W):
            path[(cr, lane_col(k, p))] = h
        if k < len(lanes) - 1:
            ce = lane_col(k, W - 1)
            path[(cr + 1, ce)] = h
            stairs[(cr + 2, ce)] = (h, h + U)
            path[(cr + 3, ce)] = h + U
            path[(cr + 4, ce)] = h + U
        for idx, (name, p, width, s) in enumerate(mods):
            col = lambda q: lane_col(k, p + q)
            tag = f'{name}'
            hx, hy = ctr(cr + 2 * s, col(width // 2))
            hints.append((HINTS[name], hx, hy, h + 330))
            if name == 'Move':
                x, y = ctr(cr, col(1))
                blocks.append((f'Block_{tag}_Blocker', ob, (x + 87.5, y, h), M_SCALE, 0))
                path[(cr + s, col(2))] = h
                px, py = ctr(cr + s, col(2))
                sol[f'Block_{tag}_Blocker'] = (px + 87.5, py, h, 0)
            elif name == 'Fill1':
                pits[(cr, col(1))] = h
                path[(cr + s, col(0))] = h
                x, y = ctr(cr + s, col(0))
                blocks.append((f'Block_{tag}_L', ob, (x, y, h), L_SCALE, 0))
                hx2, hy2 = ctr(cr, col(1))
                sol[f'Block_{tag}_L'] = (hx2, hy2, h - U, 0)
            elif name == 'Fill2':
                pits[(cr, col(1))] = h
                path[(cr + s, col(0))] = h
                path[(cr - s, col(2))] = h
                xa, ya = ctr(cr + s, col(0))
                xb, yb = ctr(cr - s, col(2))
                blocks.append((f'Block_{tag}_Ma', ob, (xa - 87.5, ya, h), M_SCALE, 0))
                blocks.append((f'Block_{tag}_Mb', ob, (xb + 87.5, yb, h), M_SCALE, 0))
                hx2, hy2 = ctr(cr, col(1))
                sol[f'Block_{tag}_Ma'] = (hx2 - 87.5, hy2, h - U, 0)
                sol[f'Block_{tag}_Mb'] = (hx2 + 87.5, hy2, h - U, 0)
            elif name == 'Fork':
                # pen with the enemy on side -s, safe loop on side +s (two rows away)
                path[(cr - s, col(3))] = h
                ex, ey = ctr(cr - s, col(3))
                blocks.append(('Enemy_Fork', en, (ex, ey, h), M_SCALE, 0))
                path[(cr - s, col(0))] = h
                gx, gy = ctr(cr - s, col(0))
                blocks.append(('Block_Fork_Gate', ob, (gx, gy, h), M_SCALE, 0))
                path[(cr + s, col(0))] = h
                path[(cr + s, col(6))] = h
                for q in range(7):
                    path[(cr + 2 * s, col(q))] = h
                x1, y1 = ctr(cr, col(1))
                sol['Block_Fork_Gate'] = (x1, y1, h, 0)
            elif name == 'Seal':
                path[(cr + s, col(1))] = h
                path[(cr + 2 * s, col(1))] = h
                ex, ey = ctr(cr + 2 * s, col(1))
                blocks.append(('Enemy_Seal', en, (ex, ey, h), M_SCALE, 0))
                path[(cr - s, col(1))] = h
                lx, ly = ctr(cr - s, col(1))
                blocks.append(('Block_Seal_L', ob, (lx, ly, h), L_SCALE, 0))
                sx_, sy_ = ctr(cr + s, col(1))
                sol['Block_Seal_L'] = (sx_, sy_, h, 0)
            elif name == 'Final':
                x, y = ctr(cr, col(0))
                blocks.append(('Block_Final_Blocker', ob, (x + 87.5 * lane_dx(k), y, h), M_SCALE, 0))
                pits[(cr, col(2))] = h
                path[(cr + s, col(1))] = h
                lx, ly = ctr(cr + s, col(1))
                blocks.append(('Block_Final_L', ob, (lx, ly, h), L_SCALE, 0))
                hx2, hy2 = ctr(cr, col(2))
                sol['Block_Final_L'] = (hx2, hy2, h - U, 0)
                path[(cr - s, col(4))] = h
                path[(cr - 2 * s, col(4))] = h
                ex, ey = ctr(cr - 2 * s, col(4))
                blocks.append(('Enemy_Final', en, (ex, ey, h), M_SCALE, 0))
                ax, ay = ctr(cr - s, col(4))
                sol['Block_Final_Blocker'] = (ax, ay + 87.5 * s, h, 90)  # half of the alcove mouth nearest the corridor
    for rc in pits:
        path.pop(rc, None)

    lvl = dict(path)
    lvl.update({k: v[1] for k, v in stairs.items()})
    lvl.update(pits)
    for (r, c), h in path.items():
        x, y = mn(r, c); box(f'Maze_Path_r{r}_c{c}', x, y, C, C, h, m_floor)
    for (r, c), h in pits.items():
        x, y = mn(r, c); box(f'Maze_Pit_r{r}_c{c}', x, y, C, C, h - U, m_pit)
        tp = eas.spawn_actor_from_class(unreal.TargetPoint, unreal.Vector(x + C / 2, y + C / 2, h))
        tp.set_actor_label(f'Hole_r{r}_c{c}'); tp.tags = [unreal.Name('Hole')]; tp.set_folder_path('Maze')
    for (r, c), (h0, h1) in stairs.items():
        x, y = mn(r, c); n = 7
        for i in range(n):
            box(f'Maze_Stair_r{r}_c{c}_s{i}', x, y + i * C / n, C, C / n, h0 + (h1 - h0) * (i + 1) / n, m_floor)
    # keep the camera-facing (-X) side of every stair open
    opened = {}
    for (sr, sc), (h0, h1) in stairs.items():
        for kk in (-1, 0, 1):
            opened[(sr + kk, sc - 1)] = h0 - 60
    for r in range(ROWS):
        for c in range(COLS):
            if (r, c) in lvl:
                continue
            nb = [lvl[(r + dr, c + dc)] for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (r + dr, c + dc) in lvl]
            if nb:
                top = max(nb) + 60
            else:
                near = min(lvl.items(), key=lambda kv: (kv[0][0] - r) ** 2 + (kv[0][1] - c) ** 2)
                top = near[1] + 60
            if (r, c) in opened:
                top = min(top, opened[(r, c)])
            x, y = mn(r, c); box(f'Maze_Wall_r{r}_c{c}', x, y, C, C, top, m_wall, ('Wall',))

    for label, cls, (x, y, z), scale, yaw in blocks:
        a = eas.spawn_actor_from_class(cls, unreal.Vector(x, y, z), unreal.Rotator(0, 0, yaw))
        a.set_actor_scale3d(unreal.Vector(*scale))
        a.set_actor_label(label); a.set_folder_path('Blocks')
        a.tags = [unreal.Name('Editable')]
        if cls == en:
            a.set_editor_property('AggroRadius', AGGRO)

    actors = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
    cr0 = 3
    sx, sy = ctr(cr0, lane_col(0, 0))
    actors['PointA_PathfindingCharacter'].set_actor_location(unreal.Vector(sx, sy, 100), False, False)
    kl = len(lanes) - 1
    bx, by = ctr(1 + 5 * kl + 2, lane_col(kl, W - 1))
    actors['PointB_Target'].set_actor_location(unreal.Vector(bx, by, kl * U), False, False)
    nav = actors['NavMeshBoundsVolume_Puzzle']
    nav.set_actor_location(unreal.Vector(0, 0, 200), False, False)
    nav.set_actor_scale3d(unreal.Vector(COLS * C / 200 + 2, ROWS * C / 200 + 2, 6))

    look = unreal.Vector(sx + 1400, sy + 700, 0)
    cam_loc = unreal.Vector(look.x - 1300, look.y - 2400, 2500)
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

    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    unreal.log(f'[BlockTutorialGen] seed={seed} lanes={len(lanes)} size={COLS}x{ROWS}')
    return {'seed': seed, 'solution': sol, 'lanes': len(lanes), 'size': (COLS, ROWS)}


def generate_from_menu():
    try:
        r = generate()
        unreal.EditorDialog.show_message('Block Tutorial', f"Generated seed {r['seed']}  ({r['size'][0]}x{r['size'][1]} cells, {r['lanes']} lanes)", unreal.AppMsgType.OK)
    except Exception as e:
        unreal.EditorDialog.show_message('Block Tutorial', str(e), unreal.AppMsgType.OK)
