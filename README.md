---
tags: [Experiment, AI, Active]
---

# mcptest

這是一個 Unreal Engine 實驗專案，用 Claude Code 透過 `unreal-mcp` 直接操作 Editor，在裡面做了一個 NavMesh 尋路解謎原型。玩家在 Play 模式中可以移動、旋轉、縮放障礙物，預覽角色從 A 點到 B 點最短的可行走路線；按下 PLAY 後，鏡頭會跟著角色走。如果路被擋住，角色會停在障礙物前，然後自動回到編輯模式。

## 開啟方式

1. 安裝 Git LFS 後 clone：`git lfs install && git clone https://github.com/gsn943314/mcptest.git`
2. 用 Unreal Editor 5.9 開啟 `mcptest.uproject`（預設會開 `Lvl_BlockTutorial`）
3. 按 Play（PIE）

## 關卡

- `Lvl_BlockTutorial`：方塊教學主關卡
- `Lvl_BlockTutorial_V2/V3/V4`：隨機生成的同概念版本
- `Lvl_Terraces`：S 型往上爬，含火 / 霧 / 水 / 船 / 聲音誘餌 / 壓力板 / 門 / 橋
- `Lvl_PathfindingPuzzle`：最早的平面原型

隨機生成：開一張 `Lvl_BlockTutorial*` 地圖，點選單 **Puzzle → Generate Random Block Tutorial** 或工具列 **Random Level**。

## 關卡總覽截圖

| | |
|---|---|
| `Lvl_BlockTutorial`<br>![](Docs/overviews/Lvl_BlockTutorial.png) | `Lvl_BlockTutorial_V2`<br>![](Docs/overviews/Lvl_BlockTutorial_V2.png) |
| `Lvl_BlockTutorial_V3`<br>![](Docs/overviews/Lvl_BlockTutorial_V3.png) | `Lvl_BlockTutorial_V4`<br>![](Docs/overviews/Lvl_BlockTutorial_V4.png) |
| `Lvl_BlockTutorial_V5`<br>![](Docs/overviews/Lvl_BlockTutorial_V5.png) | `Lvl_Terraces`<br>![](Docs/overviews/Lvl_Terraces.png) |
| `Lvl_PathfindingPuzzle`<br>![](Docs/overviews/Lvl_PathfindingPuzzle.png) | |

## 操作（PIE 編輯階段）

| 操作 | 功能 |
|------|------|
| 左鍵拖曳方塊 | 移動；綠框 = 可以放，紅框 = 不行（放開會回到原位） |
| `W` / `E` / `R` | 切換 移動 / 旋轉 / 縮放 |
| 滾輪 | 已選方塊在旋轉/縮放模式：旋轉 90° / 縮放 1U；否則縮放鏡頭 |
| 右鍵或中鍵拖曳、方向鍵 | 平移鏡頭 |
| `F` | 鏡頭回預設位置 |
| HUD ▶ PLAY / ↺ RESET | 開始 / 重來 |

## 用 AI 協作

`.mcp.json` 已設定好 `unreal-mcp`（Editor 開著時在 `http://127.0.0.1:8000/mcp`）。在專案根目錄開 Claude Code 或 Codex，AI 會讀 `CLAUDE.md` / `AGENTS.md` 了解專案規則。

## 資料夾結構

```text
Content/Project/
├── Art/            Meshes, Materials, Textures, Animations, VFX, UI
├── Programming/    Blueprints, Input, Data, AI, UI
├── Maps/           所有關卡
Content/Python/     隨機關卡生成器與 Editor 選單按鈕
```

開發紀錄放在 [devlog/](devlog/PROJECT-HUB.md)。
