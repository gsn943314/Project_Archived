"""Promo screenshots: grey box and final render of the same shot, with the game's real look and a free camera.

Toolbar (Puzzle section): "Promo Grey" / "Promo Final" / "Promo Shot"; also the Promo menu. Works in any level and
never changes the map: the buttons start Simulate (the game world runs: blocks amber, enemies, fox look, gouache
post process, exactly as in the game; nobody is possessed, so the camera is the normal editor camera) when it is
not running yet.

  Promo Grey / Promo Final   switch the simulated game between the grey box and the final render. Same rules as
                             BP_PathfindingPlayerController.SetViewMode (VisFinal / VisGrey / FillSlot / RevealAfterFill
                             / NoShow tags), applied by this script because Simulate has no player controller.
  Promo Shot                 pauses the game, clears the glitch, grey box screenshot -> final render screenshot from
                             the current viewport camera, then back to the view it was in.
                             Files: Saved/Promo/<Level>_<NN>_grey.png / _final.png (+ _cam.txt).
  Go To Last Shot            viewport camera back to the last shot of this level.
  Stop: the normal Stop button (or Esc) ends Simulate; nothing of it is kept.

Also works while playing (PIE): then the controller's own SetViewMode is used. HighResShot draws no UMG.
"""
import base64
import builtins
import glob
import os
import re
import time
import traceback
import unreal

MPC_GLITCH = '/Game/Dev/Materials/Glitch/MPC_Glitch'
SHOT_RES = '2'          # HighResShot argument: a multiplier of the viewport size ("2") or a size ("3840x2160")
# Simulate only: gouache pass B parameters in render pixels, scaled so the level viewport matches the game
# (measured 2026-11-16 on this PC: 0.5 made Simulate match a PIE capture of the same camera)
PIXEL_PARAMS = ('RadiusNear', 'RadiusFar', 'LineWidth')
VIEWPORT_PIXEL_SCALE = 0.5

_S = getattr(builtins, '_promo_state', None)
if _S is None:
    _S = {'tick': None, 'steps': []}
    builtins._promo_state = _S


def _saved(*p):
    return os.path.join(os.path.abspath(unreal.Paths.project_saved_dir()), *p)


def _msg(text):
    unreal.EditorDialog.show_message('Promo', text, unreal.AppMsgType.OK)


def _ues():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)


def _les():
    return unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)


def _game():
    """The running Simulate / PIE world or None."""
    return _ues().get_game_world()


def _pc(g):
    pc = unreal.GameplayStatics.get_player_controller(g, 0)
    return pc if pc and 'PathfindingPlayerController' in pc.get_class().get_name() else None


def _level_name(w):
    n = w.get_outer().get_name().split('/')[-1]
    return re.sub(r'^UEDPIE_\d+_', '', n).replace('Lvl_', '').replace('_Promo', '')


# ---------------------------------------------------------------- grey box / final render in the running game

def _tagged(g, tag):
    return unreal.GameplayStatics.get_all_actors_with_tag(g, tag)


def _enemies(g, final):
    """Enemy blocks: in the game they turn into the rock golem (BP_EnemyChaser) when the run starts. Final render:
    the block's own Activate spawns the golem, StopChase keeps it standing where the block was; grey box: Deactivate
    (golem removed, block back)."""
    fox = [a for a in unreal.GameplayStatics.get_all_actors_of_class(g, unreal.Character)
           if 'PathfindingCharacter' in a.get_class().get_name()]
    for e in unreal.GameplayStatics.get_all_actors_of_class(g, unreal.Actor):
        if 'EnemyBlock' not in e.get_class().get_name():
            continue
        if final:
            if not e.get_editor_property('Chaser'):
                e.call_method('Activate', (fox[0] if fox else None,))
            ch = e.get_editor_property('Chaser')
            if ch:
                ch.call_method('StopChase')
        else:
            e.call_method('Deactivate')


def _view(g, final):
    """SetViewMode of the game, on the game world (Simulate has no player controller to call it on)."""
    _S['final'] = bool(final)
    _enemies(g, final)
    pc = _pc(g)
    if pc:                                                   # PIE: the controller's own function
        pc.call_method('SetViewMode', (bool(final),))
        return
    for a in _tagged(g, 'VisFinal'):
        a.set_actor_hidden_in_game(not final)
    for a in _tagged(g, 'VisGrey'):
        a.set_actor_hidden_in_game(final)
    blocks = _tagged(g, 'Editable')
    for slot in _tagged(g, 'FillSlot'):
        p = slot.get_actor_location()
        filled = False
        for b in blocks:
            q = b.get_actor_location()
            if ((q.x - p.x) ** 2 + (q.y - p.y) ** 2) ** 0.5 < 120 and q.z < p.z - 50:
                filled = True
                for x in b.get_attached_actors():
                    x.set_actor_hidden_in_game(True)
        for x in slot.get_attached_actors():
            x.set_actor_hidden_in_game(not (final and filled))
    # RevealAfterFill (Level 0's far island, shown in the game once the first hole is filled): promo shots show the
    # whole level, so those keep the VisFinal / VisGrey visibility set above
    for a in _tagged(g, 'NoShow'):
        a.set_actor_hidden_in_game(True)


def _matlib():
    return getattr(unreal, 'KismetMaterialLibrary', None) or getattr(unreal, 'MaterialLibrary', None)


def _gouache_fix(g):
    """The level viewport renders the gouache pass at about half the game's resolution here, and its brush radius /
    line width are in render pixels, so strokes came out twice as thick as in the game. In Simulate only (not PIE),
    the PPVs of the temporary game world get a dynamic copy of MI_PP_GouacheB with those parameters scaled by
    VIEWPORT_PIXEL_SCALE; the asset is never changed and the copy is gone when Simulate stops."""
    if _pc(g):
        return
    lib = _matlib()
    for p in unreal.GameplayStatics.get_all_actors_of_class(g, unreal.PostProcessVolume):
        s = p.settings
        arr = list(s.weighted_blendables.array)
        changed = False
        for i, b in enumerate(arr):
            o = b.object
            if o and not isinstance(o, unreal.MaterialInstanceDynamic) and o.get_name() == 'MI_PP_GouacheB':
                mid = lib.create_dynamic_material_instance(g, o)
                for prm in PIXEL_PARAMS:
                    v = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(o, prm)
                    mid.set_scalar_parameter_value(prm, v * VIEWPORT_PIXEL_SCALE)
                arr[i] = unreal.WeightedBlendable(weight=b.weight, object=mid)
                changed = True
        if changed:
            s.weighted_blendables = unreal.WeightedBlendables(array=arr)
            p.settings = s


def _backdrop(g):
    """Maze_Backdrop (200 m plane under the level, painted with the gouache background colour) fills the game camera's
    view, but wide promo angles see past its edge (sky band). Simulate / PIE world only: scaled up 6x in X / Y."""
    for a in unreal.GameplayStatics.get_all_actors_of_class(g, unreal.StaticMeshActor):
        if 'Backdrop' in a.get_actor_label() and 'PromoScaled' not in [str(t) for t in a.tags]:
            s = a.get_actor_scale3d()
            a.set_actor_scale3d(unreal.Vector(s.x * 6, s.y * 6, s.z))
            a.tags = list(a.tags) + [unreal.Name('PromoScaled')]      # game-world copy only, once


def _prep(g):
    """No editor icons; no glitch; gouache strokes at the game's size; backdrop fills every angle."""
    _backdrop(g)
    try:
        _les().editor_set_game_view(True)
    except Exception:
        pass
    mpc = unreal.load_asset(MPC_GLITCH)
    lib = _matlib()
    if mpc and lib:
        lib.set_scalar_parameter_value(g, mpc, 'Amount', 0.0)
    _gouache_fix(g)


def _viewport_png(path):
    """Redraws the active level viewport (scene + post process, no gizmos / icons) and writes it as PNG, viewport size.
    SceneCaptureToolset.CaptureEditorViewport; its result's Image is not readable from Python, so it is taken from
    the exported text (base64 PNG)."""
    cdo = unreal.get_default_object(unreal.SceneCaptureToolset)
    r = cdo.call_method('CaptureEditorViewport', (None, None, False, unreal.Guid()))
    m = re.search(r'Image=\(MimeType="image/png",Data="([^"]+)"', r.export_text())
    if not m:
        raise RuntimeError('the level viewport could not be captured (is it visible, not in a background tab?)')
    with open(path, 'wb') as f:
        f.write(base64.b64decode(m.group(1)))


# ---------------------------------------------------------------- step runner (one step per editor frame)

def _stop():
    if _S['tick'] is not None:
        unreal.unregister_slate_post_tick_callback(_S['tick'])
        _S['tick'] = None


def _run(steps):
    _stop()
    _S['steps'] = steps
    _S['tick'] = unreal.register_slate_post_tick_callback(_tick)


def _tick(dt):
    try:
        _step()
    except Exception as e:
        unreal.log_error('[Promo] failed:\n' + traceback.format_exc())
        _S['steps'] = []
        _stop()
        g = _game()
        try:
            if g:
                unreal.GameplayStatics.set_game_paused(g, False)
                _view(g, _S.get('back', True))
        except Exception:
            pass
        if _S.get('popup', True):
            _msg('Promo failed:\n%s\n\n(details in the Output Log, search [Promo])' % e)


def _step():
    st = _S['steps']
    if not st:
        _stop()
        return
    step = st[0]
    kind = step[0]
    if kind == 'sim':                                        # start Simulate unless a game is already running
        if not _game():
            _les().editor_play_simulate()
        st[0] = ['sim_wait', time.time()]
        return
    if kind == 'sim_wait':
        g = _game()
        if g:
            _S['game'] = g
            _prep(g)
            st.pop(0)
        elif time.time() - step[1] > 30:
            raise RuntimeError('Simulate did not start')
        return
    g = _S.get('game')
    if not g or _game() != g:
        raise RuntimeError('the game / Simulate stopped')
    if kind == 'view':
        _view(g, step[1])
        st.pop(0)
    elif kind == 'pause':
        if step[1]:
            _S['was_paused'] = unreal.GameplayStatics.is_game_paused(g)
            unreal.GameplayStatics.set_game_paused(g, True)
            _prep(g)
        else:
            unreal.GameplayStatics.set_game_paused(g, bool(_S.get('was_paused')))
        st.pop(0)
    elif kind == 'wait':
        step[1] -= 1
        if step[1] <= 0:
            st.pop(0)
    elif kind == 'shot':
        if not _pc(g):
            # Simulate: no game viewport and HighResShot is refused in play mode -> redraw + read the level viewport
            _viewport_png(step[1])
            unreal.log('[Promo] saved ' + step[1])
            st.pop(0)
            return
        before = set(glob.glob(_saved('Screenshots', '**', '*.png'), recursive=True))
        unreal.SystemLibrary.execute_console_command(g, 'HighResShot ' + SHOT_RES)      # PIE: the game viewport
        st[0] = ['file', step[1], before, time.time()]
    elif kind == 'file':
        _les().editor_invalidate_viewports()
        new = sorted(set(glob.glob(_saved('Screenshots', '**', '*.png'), recursive=True)) - step[2], key=os.path.getmtime)
        if new:
            f = new[-1]
            s1 = os.path.getsize(f)
            time.sleep(0.05)
            if s1 and s1 == os.path.getsize(f):
                os.replace(f, step[1])
                unreal.log('[Promo] saved ' + step[1])
                st.pop(0)
        elif time.time() - step[3] > 20:
            raise RuntimeError('the screenshot did not appear after 20 s')
    elif kind == 'cam':                                      # file name + camera, once the game runs
        name = _level_name(g)
        os.makedirs(_saved('Promo'), exist_ok=True)
        nums = [int(m.group(1)) for f in os.listdir(_saved('Promo'))
                for m in [re.match(re.escape(name) + r'_(\d+)_', f)] if m]
        base = _saved('Promo', '%s_%02d' % (name, max(nums, default=0) + 1))
        r = _ues().get_level_viewport_camera_info()
        loc, rot = r[-2], r[-1]
        with open(base + '_cam.txt', 'w') as f:
            f.write('%f %f %f %f %f %f\n' % (loc.x, loc.y, loc.z, rot.pitch, rot.yaw, rot.roll))
        pc = _pc(g)
        _S['back'] = (int(pc.get_editor_property('Phase')) != 0) if pc else _S.get('final', True)
        grey, final = base + '_grey.png', base + '_final.png'
        st.pop(0)
        st[0:0] = [['pause', True], ['view', False], ['wait', 8], ['shot', grey], ['view', True], ['wait', 8],
                   ['shot', final], ['view', _S['back']], ['pause', False], ['done', [grey, final], step[1]]]
    elif kind == 'done':
        st.pop(0)
        _stop()
        unreal.log('[Promo] pair done: ' + ', '.join(step[1]))
        if step[2]:
            _msg('Saved to Saved/Promo:\n' + '\n'.join(os.path.basename(f) for f in step[1]))


# ---------------------------------------------------------------- buttons

def show_grey():
    _run([['sim'], ['view', False]])


def show_final():
    _run([['sim'], ['view', True]])


def capture_pair(popup=True):
    """Grey box + final render PNGs from the current viewport camera (starts Simulate when needed)."""
    _S['popup'] = popup
    starting = _game() is None
    steps = [['sim']]
    if starting:
        steps += [['view', True], ['wait', 30]]              # let the level settle (BeginPlay looks, streaming)
    _run(steps + [['cam', popup]])


def go_to_shot(n=None):
    """Viewport camera back to a saved shot (Saved/Promo/<Level>_<NN>_cam.txt)."""
    w = _game() or _ues().get_editor_world()
    name = _level_name(w)
    files = sorted(f for f in os.listdir(_saved('Promo')) if f.startswith(name + '_') and f.endswith('_cam.txt')) \
        if os.path.isdir(_saved('Promo')) else []
    if n is not None:
        files = [f for f in files if f == '%s_%02d_cam.txt' % (name, int(n))]
    if not files:
        _msg('No saved shot for %s yet.' % name)
        return
    v = [float(x) for x in open(_saved('Promo', files[-1])).read().split()]
    _ues().set_level_viewport_camera_info(unreal.Vector(v[0], v[1], v[2]), unreal.Rotator(roll=v[5], pitch=v[3], yaw=v[4]))


def open_folder():
    os.makedirs(_saved('Promo'), exist_ok=True)
    os.startfile(_saved('Promo'))
