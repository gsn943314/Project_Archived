"""Runs at editor startup: adds the Puzzle menu and toolbar buttons (random level + marker editing tools)
and starts Live Edit (magnetic snapping + automatic terrain rebuild)."""
import unreal

GEN = "import importlib, puzzle_level_tools as T, block_tutorial_gen as g; importlib.reload(T); importlib.reload(g); g.generate_from_menu()"


def _tool(fn):
    return f"import importlib, puzzle_level_tools as T; importlib.reload(T); T._run(T.{fn})"


LIVE = "import importlib, puzzle_level_tools as T, live_edit as L; importlib.reload(T); importlib.reload(L); L.toggle()"

ICONS = {  # toolbar icons (AppStyle)
    'GenBlockTutorial': 'Icons.Refresh',
    'RebuildFromMarkers': 'LevelEditor.Build',
    'LiveEdit': 'Icons.Visible',
    'ViewToggle': 'LevelEditor.Tabs.Viewports',
    'PathToggle': 'Icons.Visible',
    'ApplyArt': 'ClassIcon.StaticMeshActor',
    'AddPathNode': 'ClassIcon.Sphere',
    'AddFloor': 'ClassIcon.Plane',
    'AddWide': 'Icons.Plus',
    'AddHole': 'ClassIcon.TargetPoint',
    'AddBlock': 'ClassIcon.Cube',
    'AddEnemy': 'ClassIcon.Character',
}

ENTRIES = [
    # name, label, tooltip, command, toolbar label (None = menu only)
    ('GenBlockTutorial', 'Generate Random Block Tutorial',
     'Regenerates the OPEN BlockTutorial level with a random layout (duplicate the map first!)', GEN, None),
    ('RebuildFromMarkers', 'Rebuild Level From Markers',
     'Rebuilds walls / floors / stairs / holes from the path nodes, floor tiles, holes and blocks, then saves',
     "import importlib, puzzle_level_tools as T; importlib.reload(T); T.rebuild_from_menu()", None),
    ('ApplyArt', 'Apply Art (MegaJam meshes)',
     'Dresses the open level with the /Game/Dev/Meshes art: stairs, wall caps, edge walls, portal at B (folder Art)',
     "import importlib, puzzle_level_tools as T, view_mode as V, puzzle_art as A; importlib.reload(T); importlib.reload(V); importlib.reload(A); A.apply_from_menu()", None),
    ('ResetArt', 'Reset Selected Art',
     'Selected art pieces go back to the automatically generated version',
     "import importlib, puzzle_level_tools as T, view_mode as V, puzzle_art as A; importlib.reload(T); importlib.reload(V); importlib.reload(A); T._run(A.reset_selected_art)",
     None),
    ('LiveEdit', 'Live Edit On / Off',
     'Live Edit: markers snap to the grid and the terrain rebuilds automatically while you edit',
     LIVE, None),
    None,
    ('AddPathNode', 'Add Path Node',
     'Adds a yellow path node. With a node selected it is inserted right after it; otherwise appended to PathA',
     _tool('add_path_node'), 'Path Node'),
    ('RenumberPath', 'Renumber Path (selection order)',
     'Ctrl-click the path nodes in walking order (start first), then run: they become PathA_00, 01 ... and the level rebuilds',
     _tool('renumber_path_from_selection'), None),
    ('AddBranch', 'Add Branch (new corridor)', 'Starts a new corridor chain PathB / PathC ... with two nodes',
     _tool('add_branch'), None),
    ('AddFloor', 'Add Floor Tile (pocket)', 'Adds a blue floor tile = one extra walkable cell / alcove',
     _tool('add_floor'), None),
    ('AddHole', 'Add Hole', 'Adds a sunken hole in the floor that must be filled with a block',
     _tool('add_hole'), 'Hole'),
    ('AddWide', 'Add Widening Floor', 'Adds a brown tile: extra floor that only makes a walkway look wider',
     _tool('add_wide'), 'Wide'),
    ('AddBlock', 'Add Movable Block (2x2)', 'Adds a purple movable block (fills one hole)',
     _tool('add_block'), None),
    ('AddThinBlock', 'Add Thin Movable Block (1x2)', 'Adds a thin purple block (two of them fill one hole)',
     _tool('add_thin_block'), None),
    ('AddEnemy', 'Add Enemy', 'Adds a red enemy block', _tool('add_enemy'), None),
    ('ViewToggle', 'Toggle Grey Box / Final Render',
     'Switches the editor view between the grey box and the final art (grey proxies are rebuilt from the art)',
     "import importlib, puzzle_level_tools as T, view_mode as V; importlib.reload(T); importlib.reload(V); V.toggle()",
     'Grey / Final'),
    ('PathToggle', 'Path Preview On / Off',
     'Shows or hides the live shortest-path line in the game (BP_PathfindingPlayerController.bShowPath, saved; also applies to a running PIE)',
     "import importlib, view_mode as V; importlib.reload(V); V.toggle_path()",
     'Path On / Off'),
]


def _promo(fn):
    return f"import importlib, view_mode as V, promo_shots as P; importlib.reload(V); importlib.reload(P); P.{fn}"


PROMO = [  # Promo menu: screenshots for promo art with the game's real look (Simulate), promo_shots.py
    ('PromoGrey', 'Grey Box View', 'Starts Simulate (game look, free editor camera) and shows the grey box view',
     _promo('show_grey()'), 'Promo Grey'),
    ('PromoFinal', 'Final Render View', 'Starts Simulate (game look, free editor camera) and shows the final render',
     _promo('show_final()'), 'Promo Final'),
    ('PromoShot', 'Capture Grey + Final Pair',
     'One grey box and one final render PNG of the current viewport camera -> Saved/Promo (starts Simulate if needed)',
     _promo('capture_pair()'), 'Promo Shot'),
    ('PromoLast', 'Go To Last Shot', 'Level viewport camera back where the last promo shot of this level was taken',
     _promo('go_to_shot()'), None),
    ('PromoFolder', 'Open Promo Folder', 'Opens Saved/Promo', _promo('open_folder()'), None),
]


def _register_promo(menus, main, bar):
    sub = main.add_sub_menu('LevelEditor.MainMenu', 'PromoTools', 'PromoTools', 'Promo', 'Promo screenshots') if main else None
    for name, label, tip, cmd, btn in PROMO:
        if sub:
            e = unreal.ToolMenuEntry(name=name, type=unreal.MultiBlockType.MENU_ENTRY)
            e.set_label(label)
            e.set_tool_tip(tip)
            e.set_string_command(unreal.ToolMenuStringCommandType.PYTHON, '', cmd)
            sub.add_menu_entry('Promo', e)
        if bar and btn:
            b = unreal.ToolMenuEntry(name=name + 'Btn', type=unreal.MultiBlockType.TOOL_BAR_BUTTON)
            b.set_label(btn)
            b.set_tool_tip(tip)
            b.set_icon('EditorStyle', 'LevelEditor.Tabs.Viewports')
            b.style_name_override = 'CalloutToolbar'
            b.set_string_command(unreal.ToolMenuStringCommandType.PYTHON, '', cmd)
            bar.add_menu_entry('Puzzle', b)


def _register():
    menus = unreal.ToolMenus.get()
    main = menus.find_menu('LevelEditor.MainMenu')
    bar = menus.find_menu('LevelEditor.LevelEditorToolBar.User')
    sub = main.add_sub_menu('LevelEditor.MainMenu', 'PuzzleTools', 'PuzzleTools', 'Puzzle', 'Pathfinding puzzle tools') if main else None
    section = 'Generate'
    for item in ENTRIES:
        if item is None:
            section = 'Edit'
            continue
        name, label, tip, cmd, btn = item
        if sub:
            e = unreal.ToolMenuEntry(name=name, type=unreal.MultiBlockType.MENU_ENTRY)
            e.set_label(label)
            e.set_tool_tip(tip)
            e.set_string_command(unreal.ToolMenuStringCommandType.PYTHON, '', cmd)
            if name in ICONS:
                e.set_icon('EditorStyle', ICONS[name])
            sub.add_menu_entry(section, e)
        if bar and btn:
            b = unreal.ToolMenuEntry(name=name + 'Btn', type=unreal.MultiBlockType.TOOL_BAR_BUTTON)
            b.set_label(btn)
            b.set_tool_tip(tip)
            b.set_icon('EditorStyle', ICONS.get(name, 'LevelEditor.Tabs.Viewports'))
            b.style_name_override = 'CalloutToolbar'      # show the text label next to the icon
            b.set_string_command(unreal.ToolMenuStringCommandType.PYTHON, '', cmd)
            bar.add_menu_entry('Puzzle', b)
    _register_promo(menus, main, bar)
    menus.refresh_all_widgets()



def _start_live():
    try:
        import live_edit
        live_edit.start()
    except Exception as e:
        unreal.log_warning(f'[LiveEdit] could not start: {e}')


_register()
_start_live()
