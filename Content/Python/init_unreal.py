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
    'AddPathNode': 'ClassIcon.Sphere',
    'AddFloor': 'ClassIcon.Plane',
    'AddHole': 'ClassIcon.TargetPoint',
    'AddBlock': 'ClassIcon.Cube',
    'AddEnemy': 'ClassIcon.Character',
}

ENTRIES = [
    # name, label, tooltip, command, toolbar label (None = menu only)
    ('GenBlockTutorial', 'Generate Random Block Tutorial',
     'Regenerates the OPEN BlockTutorial level with a random layout (duplicate the map first!)', GEN, 'Random Level'),
    ('RebuildFromMarkers', 'Rebuild Level From Markers',
     'Rebuilds walls / floors / stairs / holes from the path nodes, floor tiles, holes and blocks, then saves',
     "import importlib, puzzle_level_tools as T; importlib.reload(T); T.rebuild_from_menu()", 'Rebuild Level'),
    ('LiveEdit', 'Live Edit On / Off',
     'Live Edit: markers snap to the grid and the terrain rebuilds automatically while you edit',
     LIVE, 'Live'),
    None,
    ('AddPathNode', 'Add Path Node',
     'Adds a yellow path node. With a node selected it is inserted right after it; otherwise appended to PathA',
     _tool('add_path_node'), 'Path Node'),
    ('AddBranch', 'Add Branch (new corridor)', 'Starts a new corridor chain PathB / PathC ... with two nodes',
     _tool('add_branch'), None),
    ('AddFloor', 'Add Floor Tile (pocket)', 'Adds a blue floor tile = one extra walkable cell / alcove',
     _tool('add_floor'), 'Floor'),
    ('AddHole', 'Add Hole', 'Adds a sunken hole in the floor that must be filled with a block',
     _tool('add_hole'), 'Hole'),
    ('AddBlock', 'Add Movable Block (2x2)', 'Adds a purple movable block (fills one hole)',
     _tool('add_block'), 'Block'),
    ('AddThinBlock', 'Add Thin Movable Block (1x2)', 'Adds a thin purple block (two of them fill one hole)',
     _tool('add_thin_block'), None),
    ('AddEnemy', 'Add Enemy', 'Adds a red enemy block', _tool('add_enemy'), 'Enemy'),
]


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
    menus.refresh_all_widgets()



def _start_live():
    try:
        import live_edit
        live_edit.start()
    except Exception as e:
        unreal.log_warning(f'[LiveEdit] could not start: {e}')


_register()
_start_live()
