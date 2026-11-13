---
tags: [Experiment, AI, Active]
---

# mcptest

這是一個 Unreal Engine 實驗專案，用 Claude Code 透過 `unreal-mcp` 直接操作 Editor，在裡面做了一個 NavMesh 尋路解謎原型。玩家在 Play 模式中可以移動、旋轉、縮放障礙物，預覽角色從 A 點到 B 點最短的可行走路線；按下 PLAY 後，鏡頭會跟著角色走。如果路被擋住，角色會停在障礙物前，然後自動回到編輯模式。

## 開啟方式

1. 用 Unreal Editor 開啟 `mcptest.uproject`
2. 開啟關卡 `/Game/Project/Maps/Lvl_PathfindingPuzzle`
3. 按 Play（PIE）

## 操作

| 按鍵 | 功能 |
|------|------|
| 左鍵點選紫色障礙物 | 選取（黃框標示） |
| 左鍵拖曳 | 套用目前的工具 |
| `W` / `E` / `R` | 切換 移動 / 旋轉 / 縮放 |
| 滾輪 | 旋轉 15° 或縮放 10% |
| HUD ▶ PLAY | 開始跑，鏡頭跟隨角色 |
| HUD ↺ RESET | 角色回到 A 點，鏡頭回到俯視 |

## 資料夾結構

```text
Content/Project/
├── Art/            Meshes, Materials, Textures, Animations, VFX, UI
├── Programming/    Blueprints, Input, Data, AI, UI
└── Maps/           Lvl_PathfindingPuzzle
```

開發紀錄放在 [devlog/](devlog/PROJECT-HUB.md)。
