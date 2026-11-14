"""Grey box / final render views of one level (editor side; the game switches with the same tags in
BP_PathfindingPlayerController.SetViewMode: grey while editing, final after PLAY).

  VisFinal  final-render art (folder "Art"): generated pieces and anything placed there by hand
  VisGrey   grey-box only: "GB_" proxies (folder "Greybox") and the Maze cubes the art covers
  untagged  always visible (grey walls of the terrain, blocks, enemies, gimmicks ...)

Collision / NavMesh always come from the Maze cubes, so both views play the same.
The grey proxies are generated from the art as it is now (Sync Greybox, also run on every switch to Grey):
each art mesh gets a box of its bounds following its location / rotation / scale, or the shape set for its
mesh in DT_GreyboxProfiles (Box / Steps / Custom / None).
"""
import builtins
import unreal
import puzzle_level_tools as T

DT_PATH = '/Game/Project/Data/DT_GreyboxProfiles'
CUBE = '/Engine/BasicShapes/Cube'          # 100 cm, pivot in the centre
GREY_MAT = '/Game/Project/Art/Materials/MI_MazeWall'
FOLDER = 'Greybox'

_S = getattr(builtins, '_puzzle_view_state', None)
if _S is None:
    _S = {'final': True}
    builtins._puzzle_view_state = _S


def is_art(a):
    """Final-render art: actors in a World Outliner folder named like 'Art' / 'Camp_ArtPreview'."""
    return 'Art' in T._folder(a).split('/')[0]


def _profiles():
    """{mesh name: dict(shape, steps, axis, custom, pad)} from DT_GreyboxProfiles."""
    dt = unreal.load_asset(DT_PATH)
    out = {}
    if not dt:
        return out
    L = unreal.DataTableFunctionLibrary
    cols = {c: L.get_data_table_column_as_string(dt, c) for c in ('Mesh', 'Shape', 'Steps', 'StepAxis', 'CustomMesh', 'Padding')}
    for i in range(len(cols['Mesh'])):
        mesh = cols['Mesh'][i]
        if not mesh or mesh == 'None':
            continue
        name = mesh.split('.')[-1].strip("'\"")
        custom = cols['CustomMesh'][i]
        out[name] = {'shape': (cols['Shape'][i] or 'Box').strip(), 'steps': int(float(cols['Steps'][i] or 4)),
                     'axis': (cols['StepAxis'][i] or '+X').strip(),
                     'custom': None if not custom or custom == 'None' else custom.split("'")[1] if "'" in custom else custom,
                     'pad': float(cols['Padding'][i] or 0)}
    return out


def _proxy(label, xf, center, ext, mat):
    """Grey box of local size `ext` centred at local `center`, following the art actor's transform `xf`."""
    loc = xf.transform_location(center)
    s = xf.scale3d
    a = T._eas().spawn_actor_from_class(unreal.StaticMeshActor, loc, xf.rotation.rotator())
    smc = a.static_mesh_component
    smc.set_static_mesh(T._asset(CUBE))
    smc.set_material(0, mat)
    smc.set_collision_profile_name('NoCollision')
    smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    smc.set_editor_property('can_ever_affect_navigation', False)
    a.set_actor_enable_collision(False)
    a.set_actor_scale3d(unreal.Vector(max(ext.x * s.x, 1) / 100, max(ext.y * s.y, 1) / 100, max(ext.z * s.z, 1) / 100))
    a.set_actor_label(label)
    a.set_folder_path(FOLDER)
    a.tags = [unreal.Name('VisGrey'), unreal.Name('GreyProxy')]
    return a


def sync_greybox():
    """Rebuilds every GB_ proxy from the art as it is now. Returns the number of proxies."""
    for a in list(T._actors()):
        if T._folder(a) == FOLDER or 'GreyProxy' in [str(t) for t in a.tags]:
            T._eas().destroy_actor(a)
    prof = _profiles()
    mat = T._asset(GREY_MAT)
    n = 0
    for a in list(T._actors()):
        if not is_art(a) or not isinstance(a, unreal.StaticMeshActor):
            continue
        tags = [str(t) for t in a.tags]
        if 'VisFinal' not in tags:
            a.tags = list(a.tags) + [unreal.Name('VisFinal')]
        mesh = a.static_mesh_component.static_mesh
        if mesh is None or 'NoGreybox' in tags:
            continue
        p = prof.get(mesh.get_name(), {'shape': 'Box', 'pad': 0.0})
        shape = p['shape'].lower()
        if shape == 'none':
            continue
        xf = a.get_actor_transform()
        lab = 'GB_' + a.get_actor_label()
        if shape == 'custom' and p.get('custom'):
            g = T._eas().spawn_actor_from_class(unreal.StaticMeshActor, xf.translation, xf.rotation.rotator())
            g.static_mesh_component.set_static_mesh(unreal.load_asset(p['custom']))
            g.static_mesh_component.set_material(0, mat)
            g.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            g.set_actor_enable_collision(False)
            g.set_actor_scale3d(xf.scale3d)
            g.set_actor_label(lab)
            g.set_folder_path(FOLDER)
            g.tags = [unreal.Name('VisGrey'), unreal.Name('GreyProxy')]
            n += 1
            continue
        b = mesh.get_bounding_box()
        pad = p.get('pad', 0.0)
        mn = unreal.Vector(b.min.x - pad, b.min.y - pad, b.min.z)
        mx = unreal.Vector(b.max.x + pad, b.max.y + pad, b.max.z + pad)
        if shape == 'steps':
            k = max(1, p.get('steps', 4))
            ax = p.get('axis', '+X').upper()
            along_x = ax.endswith('X')
            lo, hi = (mn.x, mx.x) if along_x else (mn.y, mx.y)
            length = (hi - lo) / k
            for i in range(k):
                rise = (i + 1) if ax.startswith('+') else (k - i)       # step i counted from the low (min) end
                h = (mx.z - mn.z) * rise / k
                c0 = lo + length * (i + 0.5)
                if along_x:
                    center = unreal.Vector(c0, (mn.y + mx.y) / 2, mn.z + h / 2)
                    ext = unreal.Vector(length, mx.y - mn.y, h)
                else:
                    center = unreal.Vector((mn.x + mx.x) / 2, c0, mn.z + h / 2)
                    ext = unreal.Vector(mx.x - mn.x, length, h)
                _proxy(f'{lab}_{i}', xf, center, ext, mat)
                n += 1
            continue
        center = unreal.Vector((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, (mn.z + mx.z) / 2)
        _proxy(lab, xf, center, mx - mn, mat)
        n += 1
    set_view(_S['final'])
    return n


def set_view(final):
    """Editor view only (temporarily hidden: not saved, does not dirty the level)."""
    _S['final'] = bool(final)
    for a in T._actors():
        tags = [str(t) for t in a.tags]
        if 'VisFinal' in tags:
            a.set_is_temporarily_hidden_in_editor(not final)
        elif 'VisGrey' in tags:
            a.set_is_temporarily_hidden_in_editor(final)


def toggle():
    final = not _S['final']
    if not final:
        sync_greybox()
    set_view(final)
    unreal.log(f'[View] {"FINAL RENDER" if final else "GREY BOX"}')


def show_grey():
    sync_greybox()
    set_view(False)


def show_final():
    set_view(True)
