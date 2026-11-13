"""Runs at editor startup: adds Puzzle > Generate Random Block Tutorial (menu + toolbar button)."""
import unreal

CMD = "import importlib, block_tutorial_gen as g; importlib.reload(g); g.generate_from_menu()"


def _register():
    menus = unreal.ToolMenus.get()
    main = menus.find_menu('LevelEditor.MainMenu')
    if main:
        sub = main.add_sub_menu('LevelEditor.MainMenu', 'PuzzleTools', 'PuzzleTools', 'Puzzle', 'Pathfinding puzzle tools')
        e = unreal.ToolMenuEntry(name='GenBlockTutorial', type=unreal.MultiBlockType.MENU_ENTRY)
        e.set_label('Generate Random Block Tutorial')
        e.set_tool_tip('Regenerates the OPEN BlockTutorial level with a random layout (same tutorial steps)')
        e.set_string_command(unreal.ToolMenuStringCommandType.PYTHON, '', CMD)
        sub.add_menu_entry('Generate', e)
    bar = menus.find_menu('LevelEditor.LevelEditorToolBar.User')
    if bar:
        b = unreal.ToolMenuEntry(name='GenBlockTutorialBtn', type=unreal.MultiBlockType.TOOL_BAR_BUTTON)
        b.set_label('Random Level')
        b.set_tool_tip('Generate a random Block Tutorial layout into the open BlockTutorial level')
        b.set_icon('EditorStyle', 'LevelEditor.Tabs.Viewports')
        b.set_string_command(unreal.ToolMenuStringCommandType.PYTHON, '', CMD)
        bar.add_menu_entry('Puzzle', b)
    menus.refresh_all_widgets()


_register()
