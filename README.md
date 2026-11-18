![Project Archived](Docs/itch/header.png)

# Project Archived

> A forgotten fox. A half-deleted demo. Rearrange the level and let it find its way out.

**Project Archived** is a storybook puzzle game made in four days for the **2026 Epic AI MegaJam** by *The Team With No Sleep*.

You never control the fox. You edit the level — drag blocks, rotate bridges, raise lifts — then press **Play**, and the fox follows the shortest path it can find. If the way is blocked, it walks as far as it can, and you go back to editing.

- ▶ **Play on itch.io:** https://linboxxx.itch.io/project-archived
- 🏆 **MegaJam entry:** https://itch.io/jam/2026-epic-ai-megajam/rate/5377714
- 📖 **Case study & devlog:** https://davidkuo.tech/projects/project_archived

## Trailer

[![Project Archived trailer](https://img.youtube.com/vi/G1B16CLmRtI/maxresdefault.jpg)](https://www.youtube.com/watch?v=G1B16CLmRtI)

## How it plays

1. **Edit (greybox).** The world is shown as an unfinished greybox. Drag blocks to fill pits, click mechanisms (lifts, rotating bridges, one-way gates) to change the terrain. A preview line shows the fox's current route.
2. **Play (final art).** The level switches to its finished storybook look and the fox walks the NavMesh shortest path to the exit — avoiding (or being caught by) rock beasts on the way.
3. **Blocked?** The fox walks as far as it can, stops, and the game returns to edit mode.

Over three levels the fox's own look is "restored" — from grey model to white model to full colour — as the half-deleted demo comes back together.

## Screenshots

| | |
|---|---|
| <img src="Docs/itch/shot_01.jpg" width="100%"> | <img src="Docs/itch/shot_02.jpg" width="100%"> |
| <img src="Docs/itch/shot_03.jpg" width="100%"> | <img src="Docs/itch/shot_04.jpg" width="100%"> |
| <img src="Docs/itch/shot_05.jpg" width="100%"> | <img src="Docs/itch/shot_06.jpg" width="100%"> |
| <img src="Docs/itch/shot_07.jpg" width="100%"> | <img src="Docs/itch/shot_08.jpg" width="100%"> |
| <img src="Docs/itch/shot_09.jpg" width="100%"> | <img src="Docs/itch/shot_10.jpg" width="100%"> |
| <img src="Docs/itch/shot_11.jpg" width="100%"> |  |

## Team

| Name | Role | Responsibilities |
|------|------|------------------|
| David Kuo | Gameplay Engineer | Pathfinding and puzzle systems, procedural level tools, edit and play modes, game flow from menu to ending, integrating the team's art and characters |
| Haibei Ma | 3D Artist & Animator | The fox and the rock enemy: modeling, texturing, rigging and animation |
| Yuxuan He | Technical Artist | Art direction, the storybook look, set dressing for each level, opening and ending cutscenes |

## Built with

Unreal Engine 5.9 · Blueprint · Python editor tooling · unreal-mcp — much of the Editor work was driven by AI agents (Claude Code / Codex) through the Editor's built-in MCP server.

## Running the project

1. Install Git LFS, then clone:
   ```bash
   git lfs install
   git clone https://github.com/gsn943314/Project_Archived.git
   ```
2. Open `Project_Archived.uproject` with Unreal Engine 5.9.
3. Open `Lvl_MainMenu` and press Play (PIE).

### Levels

| Map | Content |
|-----|---------|
| `Lvl_MainMenu` | Start screen, level select, settings (default packaged map) |
| `Lvl_Level0` | Two islands and a chasm: build a stone bridge with blocks |
| `Lvl_Level1` | The camp: pits, a one-way gate and a rock beast |
| `Lvl_Level2` | Forgotten Wilds / Hollow Shrine: lifts, rotating bridges, a checkpoint, and the ending |

Prototype and generator maps (`Lvl_BlockTutorial*`, `Lvl_Terraces`, `Lvl_PathfindingPuzzle`) are kept for reference.

### Controls (edit phase)

| Input | Action |
|-------|--------|
| Left-drag a block | Move it (green = valid drop, red = invalid) |
| Click a mechanism | Trigger it (lift / bridge / gate) |
| Left-drag empty space, arrow keys | Pan |
| Right-drag | Orbit |
| Mouse wheel | Zoom |
| HUD ▶ PLAY / ↺ RESET | Run / restart |
| `Esc` | Back to main menu |

## Level editing tools

Editor-side Python tools (`Content/Python/`) add a **Puzzle** menu and toolbar buttons: levels are described by markers (path nodes, holes, floor marks) and the terrain, stairs, NavMesh and greybox proxies are rebuilt live as you move them. A **Grey / Final** toggle switches between the greybox and the final art.

![Editor markers](Docs/editor_markers.png)

## Repository layout

```text
Content/Project/
├── Art/            Meshes, materials, textures, animations, VFX, UI
├── Programming/    Blueprints, input, data, AI, UI
└── Maps/           All levels
Content/Python/     Level generator, rebuild / live-edit tools, editor menus
Tools/              Asset build scripts (occlusion, glitch, highlight, audio)
devlog/en/          Development log
```

## Devlog

Day-by-day notes are in [`devlog/en/`](devlog/en/README.md); the illustrated case study is at [davidkuo.tech/projects/project_archived](https://davidkuo.tech/projects/project_archived).
