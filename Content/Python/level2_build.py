"""Builds Lvl_Level2 (The Forgotten Wilds / Hollow Shrine) from the layout below with the marker system
(path nodes -> Rebuild), then places blocks, enemies, mechanisms (BP_Mechanism) and the checkpoint and runs
Apply Art. Run with the level open:  import level2_build as L2; L2.build()

Grid: row -> +Y (away from the camera), col -> +X. The overview camera looks toward +Y, so a HIGH column is on
the LEFT of the screen. Tiers are 175 cm.

2-1  A -> junction. Right (low X): crate on the trail, fill-hole, ROTATING BRIDGE over the river, stairs up.
     Left (high X): fill-hole, forest BEAST in a side pocket (plug its door with the crate), WATERWHEEL LIFT.
     Both meet at the CHECKPOINT.
2-2  fill-hole, stairs, RING BRIDGE over a river, GUARDIAN pocket (plug with the monolith), SHRINE PLATFORM
     (lift) up to B.
"""
import unreal
import puzzle_level_tools as T

GRID = (0.0, 0.0)
# (cell, tier[, 'J' = not connected to the previous node])
CHAIN_A = [((0, 7), 0), ((2, 7), 0), ((2, 2), 0), ((5, 2), 0), ((8, 2), 2), ((9, 2), 2), ((9, 7), 2),
           ((11, 7), 2), ((11, 3), 2), ((13, 3), 2), ((16, 3), 3), ((16, 11), 3), ((16, 13), 5, 'J'),
           ((14, 13), 5)]
CHAIN_B = [((2, 7), 0), ((2, 12), 0), ((5, 12), 0), ((7, 12), 2, 'J'), ((9, 12), 2), ((9, 7), 2)]
FLOORS = {(6, 12): 0, (4, 13): 0, (4, 14): 0,            # waterwheel lift cell, beast door + den
          (1, 4): 0, (1, 10): 0, (12, 5): 2,             # fill-block pockets
          (16, 12): 3, (15, 9): 3, (14, 9): 3, (17, 8): 3}  # shrine platform, guardian door + den, monolith spot
HOLES = {(2, 4): 0, (2, 10): 0, (11, 5): 2,              # fill holes
         (4, 1): 0, (4, 2): 0, (4, 3): 0,                # lower river (bridge on (4, 2))
         (15, 6): 3, (16, 6): 3, (17, 6): 3}             # upper river (ring bridge on (16, 6))
BLOCKS = [('Block_Crate', 'L', (2, 5), 0), ('Block_Fill_R', 'L', (1, 4), 0), ('Block_Fill_L', 'L', (1, 10), 0),
          ('Block_Fill_Shrine', 'L', (12, 5), 2), ('Block_Monolith', 'L', (17, 8), 3)]
ENEMIES = [('Enemy_Beast', (4, 14), 0), ('Enemy_Guardian', (14, 9), 3)]
# label, kind (0 lift / 1 bridge), cell, tier, yaw, scale
MECHS = [('Mech_Bridge_Lower', 1, (4, 2), 0, 0.0, (6.0, 3.0, 0.2)),      # long axis X: needs a turn to span Y
         ('Mech_Bridge_Ring', 1, (16, 6), 3, 90.0, (6.0, 3.0, 0.2)),      # long axis Y: needs a turn to span X
         ('Mech_Lift_Waterwheel', 0, (6, 12), 0, 0.0, (3.3, 3.3, 0.2)),
         ('Mech_Platform_Shrine', 0, (16, 12), 3, 0.0, (3.3, 3.3, 0.2))]
CHECKPOINT = ((9, 7), 2)
# the solution (used by the PIE test): block -> cell / tier, mechanisms to click
SOLUTION = {'blocks': {'Block_Crate': ((4, 13), 0), 'Block_Fill_R': ((2, 4), -1), 'Block_Fill_Shrine': ((11, 5), 1),
                       'Block_Monolith': ((15, 9), 3)},
            'clicks': ['Mech_Bridge_Lower', 'Mech_Bridge_Ring', 'Mech_Platform_Shrine']}

MECH_BP = '/Game/Project/Programming/Blueprints/Pathfinding/BP_Mechanism'
MAT = '/Game/Project/Art/Materials/Gimmick/'


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
        T.attach_crate(T.spawn_mover(kind, unreal.Vector(x, y, t * T.U), 0.0, lab))
    for lab, rc, t in ENEMIES:
        x, y = T.cell_ctr(rc, GRID)
        T.spawn_mover('Enemy', unreal.Vector(x, y, t * T.U), 0.0, lab).set_editor_property('AggroRadius', 0.0)
    cls = unreal.load_asset(MECH_BP).generated_class()
    for lab, kind, rc, t, yaw, sc in MECHS:
        x, y = T.cell_ctr(rc, GRID)
        z = t * T.U - (18 if kind == 0 else 0)          # lift top flush with the floor (walls stay out of step reach)
        a = E.spawn_actor_from_class(cls, unreal.Vector(x, y, z), unreal.Rotator(0, 0, yaw))
        a.root_component.set_mobility(unreal.ComponentMobility.MOVABLE)
        a.set_actor_scale3d(unreal.Vector(*sc))
        a.set_editor_property('Kind', kind)
        a.set_editor_property('Travel', 350.0)
        m = unreal.load_asset(MAT + ('MI_G_Wood' if kind == 1 else 'MI_G_Plate'))
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            c.set_material(0, m)
        a.set_actor_label(lab)
        a.set_folder_path('Mechanisms')
        a.tags = [unreal.Name('Mechanism')]
    (rc, t) = CHECKPOINT
    x, y = T.cell_ctr(rc, GRID)
    cp = E.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x + 110, y + 110, t * T.U + 80))
    smc = cp.static_mesh_component
    smc.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cylinder'))
    smc.set_material(0, unreal.load_asset(MAT + 'MI_G_PlateOn'))
    smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    smc.set_editor_property('can_ever_affect_navigation', False)
    cp.set_actor_enable_collision(False)
    cp.set_actor_scale3d(unreal.Vector(0.5, 0.5, 1.6))
    cp.set_actor_label('Checkpoint_Shrine')
    cp.set_folder_path('Mechanisms')
    cp.tags = [unreal.Name('Checkpoint')]


def _camera():
    acts = {a.get_actor_label(): a for a in T._actors()}
    cols = [n[0][1] for n in CHAIN_A + CHAIN_B]
    rows = [n[0][0] for n in CHAIN_A + CHAIN_B]
    look = unreal.Vector((min(cols) + max(cols) + 1) * T.C / 2, (min(rows) + max(rows) + 1) * T.C / 2 - 600, 350)
    cam = unreal.Vector(look.x - 2000, look.y - 6200, look.z + 6400)
    rot = unreal.MathLibrary.find_look_at_rotation(cam, look)
    if 'OverviewCamera' in acts:
        acts['OverviewCamera'].set_actor_location(cam, False, False)
        acts['OverviewCamera'].set_actor_rotation(rot, False)
    unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(cam, rot)


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
