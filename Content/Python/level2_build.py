"""Builds Lvl_Level2 (The Forgotten Wilds / Hollow Shrine) from the layout below with the marker system
(path nodes -> Rebuild), then places blocks, enemies, mechanisms (BP_Mechanism) and the checkpoint and runs
Apply Art. Run with the level open:  import level2_build as L2; L2.build()

Grid: row -> +Y (away from the camera), col -> +X. The overview camera looks toward +Y, so a HIGH column is on
the LEFT of the screen. Tiers are 175 cm.

2-1  A -> junction. Right (low X): crate on the trail, fill-hole, ROTATING BRIDGE over a 2-cell river, 3-tier stairs.
     Left (high X): fill-hole, forest BEAST in a side pocket (plug its door with the crate), WATERWHEEL LIFT (3 tiers,
     starts at the top: click it down to the player's floor). Both meet at the CHECKPOINT (tier 3).
2-2  fill-hole, stairs to tier 5, RING BRIDGE over a 2-cell river, GUARDIAN on a ledge (tier 7) whose lift starts at
     the top - left there, the guardian rides down and attacks; clicked down, it is trapped -, fill-hole,
     SHRINE LIFT (3 tiers, starts at the top) up to tier 8 and B.
Lifts: a click moves the resting lift to its other stop; in PLAY a character (Point A or an enemy) that stops on it
is carried to the other stop.
"""
import unreal
import puzzle_level_tools as T

GRID = (0.0, 0.0)
# (cell, tier[, 'J' = not connected to the previous node])
CHAIN_A = [((0, 7), 0), ((2, 7), 0), ((2, 2), 0), ((6, 2), 0), ((10, 2), 3), ((10, 7), 3),
           ((12, 7), 3), ((12, 3), 3), ((16, 3), 5), ((16, 12), 5), ((16, 14), 8, 'J'), ((19, 14), 8),
           ((19, 11), 8)]
CHAIN_B = [((2, 7), 0), ((2, 12), 0), ((5, 12), 0), ((7, 12), 3, 'J'), ((10, 12), 3), ((10, 7), 3)]
FLOORS = {(6, 12): 0, (4, 13): 0, (4, 14): 0,            # waterwheel lift cell, beast door + den
          (1, 4): 0, (1, 10): 0, (13, 5): 3, (15, 11): 5,  # fill-block pockets
          (17, 8): 5, (18, 8): 7, (18, 9): 7,            # guardian lift cell (bottom), guardian ledge
          (16, 13): 5}                                   # shrine lift cell (bottom)
HOLES = {(2, 4): 0, (2, 10): 0, (12, 5): 3, (16, 11): 5,  # fill holes
         **{(r, c): 0 for r in (4, 5) for c in (1, 2, 3)},          # lower river, 2 cells wide
         **{(r, c): 5 for r in (15, 16, 17) for c in (5, 6)}}       # upper river, 2 cells wide
BLOCKS = [('Block_Crate', 'L', (2, 5), 0), ('Block_Fill_R', 'L', (1, 4), 0), ('Block_Fill_L', 'L', (1, 10), 0),
          ('Block_Fill_Shrine', 'L', (13, 5), 3), ('Block_Fill_Ledge', 'L', (15, 11), 5)]
ENEMIES = [('Enemy_Beast', (4, 14), 0), ('Enemy_Guardian', (18, 9), 7)]
# label, kind (0 lift / 1 bridge), centre (x, y) in cells (.5 = cell centre), bottom tier, yaw, scale,
# travel (cm), starts at the top
MECHS = [('Mech_Bridge_Lower', 1, (2.5, 5.0), 0, 0.0, (10.5, 3.0, 0.2), 0, False),   # spans X: turn to cross rows 4-5
         ('Mech_Bridge_Ring', 1, (6.0, 16.5), 5, 90.0, (10.5, 3.0, 0.2), 0, False),  # spans Y: turn to cross cols 5-6
         ('Mech_Lift_Waterwheel', 0, (12.5, 6.5), 0, 0.0, (3.3, 3.3, 0.2), 525, True),
         ('Mech_Lift_Guardian', 0, (8.5, 17.5), 5, 0.0, (3.3, 3.3, 0.2), 350, True),
         ('Mech_Lift_Shrine', 0, (13.5, 16.5), 5, 0.0, (3.3, 3.3, 0.2), 525, True)]
CHECKPOINT = ((10, 7), 3)
# the solution (used by the PIE test): block -> (cell, tier the block stands on), mechanisms to click
SOLUTION = {'blocks': {'Block_Crate': ((4, 13), 0), 'Block_Fill_R': ((2, 4), -1), 'Block_Fill_Shrine': ((12, 5), 2),
                       'Block_Fill_Ledge': ((16, 11), 4)},
            'clicks': ['Mech_Bridge_Lower', 'Mech_Bridge_Ring', 'Mech_Lift_Guardian', 'Mech_Lift_Shrine']}

MECH_BP = '/Game/Project/Programming/Blueprints/Pathfinding/BP_Mechanism'
MAT = '/Game/Project/Art/Materials/Gimmick/'


GREY = '/Game/Project/Art/Materials/MI_Interactable'   # path grey, a little warmer: reads as walkway, but findable


def _disguise(a):
    """Tag Disguise: in the GAME every interactable piece (block, enemy, bridge, lift) gets the same amber path-grey
    (MI_Interactable, set by the blueprints' BeginPlay) instead of purple / red / orange / yellow, and the edit mode
    highlights interactables under the cursor. The editor keeps the real colours for the level designer."""
    if 'Disguise' not in [str(t) for t in a.tags]:
        a.tags = list(a.tags) + [unreal.Name('Disguise')]


def _clear():
    T.clear_all()
    E = T._eas()
    for a in list(T._actors()):
        f = T._folder(a).split('/')[0]
        if f in ('Art', 'Art_Blocks', 'Greybox', 'Mechanisms') or a.get_actor_label() == 'Art_Registry':
            E.destroy_actor(a)


def _markers():
    for ch, lst in (('A', CHAIN_A), ('B', CHAIN_B)):
        for i, n in enumerate(lst):
            a = T.spawn_node(ch, i, n[0], n[1], GRID)
            if len(n) > 2:
                a.set_actor_label(a.get_actor_label() + 'J')
    for rc, t in FLOORS.items():
        T.spawn_floor(rc, t, GRID)
    for rc, t in HOLES.items():
        T.spawn_hole(rc, t, GRID)


def _pieces():
    E = T._eas()
    for lab, kind, rc, t in BLOCKS:
        x, y = T.cell_ctr(rc, GRID)
        b = T.spawn_mover(kind, unreal.Vector(x, y, t * T.U), 0.0, lab)
        T.attach_crate(b)
        _disguise(b)
    for lab, rc, t in ENEMIES:
        x, y = T.cell_ctr(rc, GRID)
        e = T.spawn_mover('Enemy', unreal.Vector(x, y, t * T.U), 0.0, lab)
        e.set_editor_property('AggroRadius', 0.0)
        e.set_actor_scale3d(unreal.Vector(*T.L_SCALE))           # same 2x2x1 size as the movable blocks
        _disguise(e)
    cls = unreal.load_asset(MECH_BP).generated_class()
    for lab, kind, (cx, cy), t, yaw, sc, travel, up in MECHS:
        x, y = GRID[0] + cx * T.C, GRID[1] + cy * T.C
        z = t * T.U - (18 + 0 if kind == 0 else 0) + (travel if up else 0)   # lift top flush with its floor
        a = E.spawn_actor_from_class(cls, unreal.Vector(x, y, z), unreal.Rotator(0, 0, yaw))
        a.root_component.set_mobility(unreal.ComponentMobility.MOVABLE)
        a.set_actor_scale3d(unreal.Vector(*sc))
        a.set_editor_property('Kind', kind)
        a.set_editor_property('Travel', float(travel or 350))
        a.set_editor_property('bUp', bool(up))
        _disguise(a)
        a.set_actor_label(lab)
        a.set_folder_path('Mechanisms')
        a.tags = [unreal.Name('Mechanism'), unreal.Name('Disguise')]
    (rc, t) = CHECKPOINT
    x, y = T.cell_ctr(rc, GRID)
    cp = E.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, t * T.U + 80))
    smc = cp.static_mesh_component
    smc.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cylinder'))
    smc.set_material(0, unreal.load_asset(MAT + 'MI_G_PlateOn'))
    smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    smc.set_editor_property('can_ever_affect_navigation', False)
    cp.set_actor_enable_collision(False)
    cp.set_actor_scale3d(unreal.Vector(0.5, 0.5, 1.6))
    cp.set_actor_label('Checkpoint_Shrine')
    cp.set_folder_path('Mechanisms')
    cp.tags = [unreal.Name('Checkpoint'), unreal.Name('StageGoal')]     # goal of stage 2-1, then B


STAGE_VIEWS = [((2800, 1925, 300)), ((3150, 5250, 1100))]   # look-at points: stage 2-1, stage 2-2
CAM_OFFSET = (-600, -3600, 3800)


def _cam_at(look):
    look = unreal.Vector(*look)
    cam = look + unreal.Vector(*CAM_OFFSET)
    return cam, unreal.MathLibrary.find_look_at_rotation(cam, look)


def _camera():
    """OverviewCamera frames stage 2-1; a TargetPoint tagged StageCam holds the view of 2-2 (used after the checkpoint)."""
    acts = {a.get_actor_label(): a for a in T._actors()}
    cam, rot = _cam_at(STAGE_VIEWS[0])
    if 'OverviewCamera' in acts:
        acts['OverviewCamera'].set_actor_location(cam, False, False)
        acts['OverviewCamera'].set_actor_rotation(rot, False)
    unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(cam, rot)
    for a in list(T._actors()):
        if a.get_actor_label() == 'StageCam_2_2':
            T._eas().destroy_actor(a)
    cam2, rot2 = _cam_at(STAGE_VIEWS[1])
    sc = T._eas().spawn_actor_from_class(unreal.TargetPoint, cam2, rot2)
    sc.set_actor_label('StageCam_2_2')
    sc.set_folder_path('Mechanisms')
    sc.tags = [unreal.Name('StageCam')]


def build(art=True):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if w.get_name() != 'Lvl_Level2':
        raise RuntimeError('Open Lvl_Level2 first')
    _clear()
    grid = T.set_grid(*GRID)
    grid.tags = [unreal.Name('Art')]
    T.use_grid(grid)
    _markers()
    _pieces()
    for a in T._actors():
        if isinstance(a, unreal.RecastNavMesh):
            a.set_editor_property('agent_radius', 120.0)
    r = T.rebuild(save=False)
    _camera()
    if art:
        import puzzle_art as A
        import view_mode as V
        A.apply_art()
        V.set_view(True)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return r
