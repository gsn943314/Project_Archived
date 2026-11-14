"""Live editing for the marker-based puzzle levels (runs in the editor, not in Play).

While Live Edit is on (default), every editor tick:
  * Magnetic snap - when a path node / floor tile / hole / block / enemy stops moving for a moment it
    snaps onto the 350 cm cell grid and the 175 cm tier height. Blocks also snap their rotation to 90
    degrees, thin blocks snap to half cells, and blocks drop onto the floor below them.
  * Live rebuild - shortly after the last change the terrain is rebuilt from the markers, so walls,
    stairs, holes and carved pockets update without pressing Rebuild.
Warnings (e.g. two nodes too close for the stairs they need) are drawn as red text in the viewport.
Only levels that contain the Editor_Grid marker are touched. Toggle with Puzzle > Live Edit.
"""
import builtins
import math
import time
import unreal
import puzzle_level_tools as T

SNAP_DELAY = 0.35      # s an actor must be still before it snaps
REBUILD_DELAY = 0.6    # s everything must be still before the terrain is rebuilt
TICK = 0.1

_S = getattr(builtins, '_puzzle_live_state', None)
if _S is None:
    _S = {'enabled': True, 'handle': None}
    builtins._puzzle_live_state = _S
_S.update(last=0.0, refresh=0.0, world=None, grid=None, tracked=[], sig={}, moved={}, dirty=False,
          layout=None, warns=[], warn_drawn=0.0, busy=False, nav_check=0.0, nav_fixes=0)


def _now():
    return time.time()


def _in_pie():
    try:
        return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is not None
    except Exception:
        return False


def _sig(a):
    l, r, s = a.get_actor_location(), a.get_actor_rotation(), a.get_actor_scale3d()
    return (round(l.x, 1), round(l.y, 1), round(l.z, 1), round(r.yaw, 1), round(s.x, 3), round(s.y, 3), round(s.z, 3))


def _kind(a, ob, eb):
    tags = [str(t) for t in a.tags]
    if 'PathNode' in tags:
        return 'node'
    if 'FloorMark' in tags:
        return 'floor'
    if 'Hole' in tags and isinstance(a, unreal.TargetPoint):
        return 'hole'
    c = a.get_class()
    if c == ob or c == eb:
        return 'mover'
    return None


def _refresh(world):
    _S['world'] = world
    grid_actor = None
    ob = T._cls('BP_EditableObstacle')
    eb = T._cls('BP_EnemyBlock')
    tracked = []
    for a in T._actors():
        if a.get_actor_label() == T.GRID_LABEL:
            grid_actor = a
            continue
        k = _kind(a, ob, eb)
        if k:
            tracked.append((a, k))
    if grid_actor is None:
        _S['grid'] = None
        _S['tracked'] = []
        return
    T.use_grid(grid_actor)
    l = grid_actor.get_actor_location()
    _S['grid'] = (l.x, l.y)
    old = set(id(a) for a, _ in _S['tracked'])
    new = set(id(a) for a, _ in tracked)
    if old != new:
        _S['dirty'] = True
        _S['moved']['__set__'] = _now()
    _S['tracked'] = tracked


def _snap_axis(v, origin, size):
    """Centre of a box of `size` cm snapped so its edges sit on the 175 cm half-cell lines."""
    step = T.C if size >= T.C - 1 else T.C / 2
    return origin + size / 2 + round((v - origin - size / 2) / step) * step


def _snap_target(a, kind):
    grid = _S['grid']
    l = a.get_actor_location()
    r = a.get_actor_rotation()
    if kind in ('node', 'floor', 'hole'):
        rc = T.cell_of(l.x, l.y, grid)
        x, y = T.cell_ctr(rc, grid)
        z = T.tier_of(l.z - (6 if kind == 'floor' else 0)) * T.U + (6 if kind == 'floor' else 0)
        return unreal.Vector(x, y, z), None
    # blocks / enemies: rotation to 90 deg, footprint onto the grid, drop onto the ground
    yaw = round(r.yaw / 90.0) * 90.0
    s = a.get_actor_scale3d()
    lx, ly = s.x * 100, s.y * 100
    sx, sy = (lx, ly) if int(round(yaw / 90.0)) % 2 == 0 else (ly, lx)
    x = _snap_axis(l.x, grid[0], sx)
    y = _snap_axis(l.y, grid[1], sy)
    z = l.z
    lay = _S['layout']
    if lay:
        floor, stairs, pits = lay
        rc = T.cell_of(x, y, grid)
        gz = T.ground_z(rc, floor, stairs, pits)
        if gz is not None:
            z = gz
    return unreal.Vector(x, y, z), yaw


def _apply_snap(a, kind):
    loc, yaw = _snap_target(a, kind)
    moved = False
    if kind in ('floor', 'hole'):  # keep the label in sync with the cell it now sits on
        rc = T.cell_of(loc.x, loc.y, _S['grid'])
        lab = f"{'Floor' if kind == 'floor' else 'Hole'}_r{rc[0]}_c{rc[1]}"
        if a.get_actor_label() != lab:
            a.set_actor_label(lab)
    if (a.get_actor_location() - loc).length() > 0.5:
        a.set_actor_location(loc, False, False)
        moved = True
    if yaw is not None and abs(((a.get_actor_rotation().yaw - yaw) + 180) % 360 - 180) > 0.5:
        a.set_actor_rotation(unreal.Rotator(0, 0, yaw), False)
        moved = True
    return moved


def _draw_warnings(world):
    if not _S['warns'] or _now() - _S['warn_drawn'] < 1.0:
        return
    _S['warn_drawn'] = _now()
    grid = _S['grid']
    for rc, text in _S['warns']:
        x, y = T.cell_ctr(rc, grid)
        try:
            unreal.SystemLibrary.draw_debug_string(world, unreal.Vector(x, y, 2500), text, None,
                                                   unreal.LinearColor(1, 0.15, 0.1, 1), 1.1)
        except Exception:
            pass


def _rebuild():
    r = T.rebuild(save=False, navmesh=False)
    grid = _S['grid']
    nodes, floor_marks, holes, movers = T.read_markers(grid)
    floor, stairs, pits, _c, _w = T.compute_layout(grid, nodes, floor_marks, holes, movers)
    _S['layout'] = (floor, stairs, pits)
    _S['warns'] = r['warn_cells']
    for a, _k in _S['tracked']:
        try:
            _S['sig'][id(a)] = _sig(a)
        except Exception:
            pass
    if r['warnings']:
        unreal.log_warning('[LiveEdit] ' + ' | '.join(r['warnings']))


def _nav_watchdog(world):
    """An empty NavMesh (stale data, or a BUILDPATHS skipped while the level was loading) leaves the
    character with a 0-point path. Every few seconds check a short path from Point A and rebuild if empty."""
    t = _now()
    if t - _S['nav_check'] < 3.0:
        return
    _S['nav_check'] = t
    nodes = T.read_markers(_S['grid'])[0].get('A', [])
    if len(nodes) < 2:
        return
    x0, y0 = T.cell_ctr(nodes[0][1], _S['grid'])
    x1, y1 = T.cell_ctr(nodes[1][1], _S['grid'])
    a = unreal.Vector(x0, y0, nodes[0][2] * T.U + 90)
    b = unreal.Vector(x1, y1, nodes[1][2] * T.U + 90)
    p = unreal.NavigationSystemV1.find_path_to_location_synchronously(world, a, b)
    if p is None or len(p.path_points) == 0:
        if _S['nav_fixes'] < 5:
            _S['nav_fixes'] += 1
            unreal.log_warning('[LiveEdit] NavMesh is empty - rebuilding paths')
            unreal.SystemLibrary.execute_console_command(world, 'BUILDPATHS')
    else:
        _S['nav_fixes'] = 0


def _art_watch(t):
    """Final-render art moved / rotated / scaled / added / deleted -> regenerate the GB_ grey boxes once it
    has been still for a moment, so the grey view (and PLAY's edit phase) always matches the art."""
    if t - _S.get('art_check', 0.0) < 0.5:
        return
    _S['art_check'] = t
    import view_mode as V
    for a in T._actors():                 # block art (ArtCrate_*) always sits exactly on its block
        if a.get_actor_label().startswith('ArtCrate_'):
            b = a.get_attach_parent_actor()
            if b and (a.get_actor_location() - b.get_actor_location()).length() > 1.0:
                a.set_actor_location(b.get_actor_location(), False, False)
                a.set_actor_rotation(b.get_actor_rotation(), False)
    sig = tuple(sorted((a.get_actor_label(),) + _sig(a) for a in T._actors()
                       if isinstance(a, unreal.StaticMeshActor) and V.is_art(a)))
    if _S.get('art_sig') is None or _S.get('art_world') != _S['world']:
        _S['art_sig'], _S['art_world'], _S['art_moved'] = sig, _S['world'], None
        return
    if sig != _S['art_sig']:
        _S['art_sig'], _S['art_moved'] = sig, t
    elif _S.get('art_moved') and t - _S['art_moved'] >= REBUILD_DELAY:
        _S['art_moved'] = None
        n = V.sync_greybox()
        unreal.log(f'[LiveEdit] art changed - {n} grey boxes regenerated')


def _tick(dt):
    if not _S['enabled'] or _S['busy']:
        return
    t = _now()
    if t - _S['last'] < TICK:
        return
    _S['last'] = t
    if _in_pie():
        return
    _S['busy'] = True
    try:
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        if world is None:
            return
        if world != _S['world'] or t - _S['refresh'] > 1.0:
            first = world != _S['world']
            _S['refresh'] = t
            _refresh(world)
            if first:
                _S['sig'] = {id(a): _sig(a) for a, _k in _S['tracked']}
                _S['moved'] = {}
                _S['dirty'] = False
                _S['layout'] = None
        if not _S['grid']:
            return
        if _S['layout'] is None:
            nodes, fm, holes, movers = T.read_markers(_S['grid'])
            if nodes.get('A'):
                f, st, p, _c, _S_w = T.compute_layout(_S['grid'], nodes, fm, holes, movers)
                _S['layout'] = (f, st, p)
        sel = set(id(a) for a in T._eas().get_selected_level_actors())
        for a, kind in _S['tracked']:
            try:
                sg = _sig(a)
            except Exception:
                continue
            k = id(a)
            if _S['sig'].get(k) != sg:
                _S['sig'][k] = sg
                _S['moved'][k] = t
                _S['dirty'] = True
            elif k in _S['moved'] and t - _S['moved'][k] >= SNAP_DELAY:
                del _S['moved'][k]
                if _apply_snap(a, kind):
                    _S['sig'][k] = _sig(a)
                    _S['dirty'] = True
                    _S['moved']['__snap__'] = t
        quiet = all(t - v >= REBUILD_DELAY for v in _S['moved'].values())
        if _S['dirty'] and quiet:
            _S['dirty'] = False
            _S['moved'] = {}
            _rebuild()
        _art_watch(t)
        _draw_warnings(world)
        if not _S['dirty']:
            _nav_watchdog(world)
    except Exception as e:
        unreal.log_warning(f'[LiveEdit] {e}')
    finally:
        _S['busy'] = False


def start():
    stop()
    _S['handle'] = unreal.register_slate_post_tick_callback(_tick)
    _S['world'] = None


def stop():
    h = _S.get('handle')
    if h is not None:
        try:
            unreal.unregister_slate_post_tick_callback(h)
        except Exception:
            pass
    _S['handle'] = None


def set_enabled(on):
    _S['enabled'] = bool(on)
    if on and _S['handle'] is None:
        start()
    unreal.log(f'[LiveEdit] {"ON" if on else "OFF"}')


def toggle():
    set_enabled(not _S['enabled'])
    try:
        import init_unreal_menus
        init_unreal_menus.update_live_label(_S['enabled'])
    except Exception:
        pass
    unreal.EditorDialog.show_message('Live Edit', 'Live Edit is now ' + ('ON: markers snap and the terrain rebuilds automatically.' if _S['enabled'] else 'OFF: press Rebuild Level to apply changes.'), unreal.AppMsgType.OK)


def is_enabled():
    return _S['enabled']
