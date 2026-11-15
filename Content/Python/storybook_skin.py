"""Storybook "skin" of the Maze terrain (look of /Game/Dev/Lvl_StorybookPreview) for levels whose Editor_Grid has
the tag `StorybookSkin` (e.g. Lvl_Camp_Whitebox_Davidtesting).

Every Maze_Path / Maze_Wall cube (stairs: the stair art) gets a twin with the final material (walkway paving, grass-top soil
walls) in the folder `Camp_ArtSkin` (tags VisFinal + NoGreybox, no collision). The Maze cube itself is tagged
VisGrey + Skinned, so the grey box still shows the grey terrain and the final render the storybook terrain;
collision / NavMesh keep coming from the Maze cubes. Re-run automatically after every Rebuild (puzzle_level_tools).
"""
import unreal
import puzzle_level_tools as T

FOLDER = 'Camp_ArtSkin'
MAT = {'Maze_Path': '/Game/Dev/Materials/MI_PavingD',
       'Maze_Wall': '/Game/Dev/Materials/MI_GrassTopSoilSides'}


PLAZA = '/Game/Dev/Materials/MI_PavingC'   # big checker paving: cells listed in the Editor_Grid tag `PavingC:r3_c4,r4_c5,...`


def _plaza_cells():
    g = [a for a in T._actors() if a.get_actor_label() == 'Editor_Grid']
    for t in (g[0].tags if g else []):
        t = str(t)
        if t.startswith('PavingC:'):
            return set(t[8:].split(','))
    return set()


def enabled():
    g = [a for a in T._actors() if a.get_actor_label() == 'Editor_Grid']
    return bool(g) and 'StorybookSkin' in [str(t) for t in g[0].tags]


def _kind(label):
    for k in MAT:
        if label.startswith(k + '_'):
            return k
    return None


def apply():
    """Rebuilds the skin from the Maze as it is now. Returns the number of skin pieces."""
    E = T._eas()
    for a in list(T._actors()):
        if T._folder(a) == FOLDER:
            E.destroy_actor(a)
    mats = {k: unreal.load_asset(p) for k, p in MAT.items()}
    plaza, pm = _plaza_cells(), unreal.load_asset(PLAZA)
    n = 0
    for a in list(T._actors()):
        if T._folder(a) != 'Maze' or not isinstance(a, unreal.StaticMeshActor):
            continue
        if a.get_actor_label().startswith('Maze_Stair'):
            # stairs are shown by the stair art (SM_PinkStone01), not by a skin twin (they overlapped)
            if 'Skinned' in [str(t) for t in a.tags]:
                a.tags = [t for t in a.tags if str(t) not in ('Skinned', 'VisGrey')]
            continue
        k = _kind(a.get_actor_label())
        if not k:
            continue
        tags = [str(t) for t in a.tags]
        if 'Skinned' not in tags:
            tags.append('Skinned')
        if 'VisGrey' not in tags:
            tags.append('VisGrey')
        a.tags = [unreal.Name(t) for t in tags]
        src = a.static_mesh_component
        s = E.spawn_actor_from_class(unreal.StaticMeshActor, a.get_actor_location(), a.get_actor_rotation())
        c = s.static_mesh_component
        c.set_static_mesh(src.static_mesh)
        cell = '_'.join(a.get_actor_label().split('_')[2:4])
        c.set_material(0, pm if k == 'Maze_Path' and cell in plaza else mats[k])
        c.set_collision_profile_name('NoCollision')
        c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        c.set_editor_property('can_ever_affect_navigation', False)
        s.set_actor_enable_collision(False)
        s.set_actor_scale3d(a.get_actor_scale3d())
        s.set_actor_label('Skin_' + a.get_actor_label())
        s.set_folder_path(FOLDER)
        s.tags = [unreal.Name('VisFinal'), unreal.Name('NoGreybox')]
        n += 1
    import view_mode as V
    V.set_view(V._S['final'])
    return n


def maze_grey_only():
    """Editor_Grid tag `MazeGreyOnly` (hand-dressed levels whose art already shows the ground, e.g. Lvl_Level0_Davidtesting):
    every Maze cube is grey-box only (VisGrey); collision / NavMesh still come from them."""
    g = [a for a in T._actors() if a.get_actor_label() == 'Editor_Grid']
    if not g or 'MazeGreyOnly' not in [str(t) for t in g[0].tags]:
        return 0
    n = 0
    for a in T._actors():
        if T._folder(a) == 'Maze' and 'VisGrey' not in [str(t) for t in a.tags]:
            a.tags = list(a.tags) + [unreal.Name('VisGrey')]
            n += 1
    return n


def tag_reveal():
    """Editor_Grid tag `RevealAfterX:<x>` (Lvl_Level0_Davidtesting): everything of the level beyond x (Maze, art, grey
    proxies, blocks and their art) gets the tag RevealAfterFill - hidden in the game until a block fills a hole
    (BP_PathfindingPlayerController.CheckReveal / SetViewMode)."""
    g = [a for a in T._actors() if a.get_actor_label() == 'Editor_Grid']
    x0 = None
    for t in (g[0].tags if g else []):
        if str(t).startswith('RevealAfterX:'):
            x0 = float(str(t).split(':')[1])
    if x0 is None:
        return 0
    n = 0
    for a in T._actors():
        f = T._folder(a)
        if not (f == 'Maze' or f == 'Greybox' or 'Art' in f.split('/')[0] or f in ('Blocks', 'Art_Blocks')):
            continue
        if not isinstance(a, unreal.StaticMeshActor) and f != 'Blocks':
            continue
        o, e = a.get_actor_bounds(False)
        if o.x < x0:            # by centre: walls / pits of a cell belong to the side their centre is on
            continue
        if 'RevealAfterFill' not in [str(t) for t in a.tags]:
            a.tags = list(a.tags) + [unreal.Name('RevealAfterFill')]
            n += 1
    return n


def tag_gap():
    """Editor_Grid tag `GapX:<x0>:<x1>` (Lvl_Level0_Davidtesting): the Maze cubes whose centre is in that x range (pit
    floors, the walls beside the pits, the island rims at the gap) are never shown (tag NoShow, hidden in the game and
    in both editor views) but keep their collision, so the islands read as separate with an open gap; translucent
    guide boxes (folder Guides) show where blocks go."""
    g = [a for a in T._actors() if a.get_actor_label() == 'Editor_Grid']
    rng = None
    for t in (g[0].tags if g else []):
        if str(t).startswith('GapX:'):
            _, a0, a1 = str(t).split(':')
            rng = (float(a0), float(a1))
    if rng is None:
        return 0
    n = 0
    for a in T._actors():
        if T._folder(a) != 'Maze':
            continue
        o = a.get_actor_bounds(False)[0]
        if not (rng[0] < o.x < rng[1]):
            continue
        if 'NoShow' not in [str(t) for t in a.tags]:
            a.tags = list(a.tags) + [unreal.Name('NoShow')]
        a.set_actor_hidden_in_game(True)
        n += 1
    return n
