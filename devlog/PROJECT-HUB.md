# mcptest — Project Hub

---

## 專案目標

驗證用 Claude Code 透過 `unreal-mcp` 直接操作 Unreal Editor 的開發流程，並做出一個 NavMesh 尋路解謎原型：玩家調整障礙物，讓角色從 A 點走到 B 點。

## 目前狀態

- `/Game/Project` 美術／程式分流資料夾：完成。
- A → B 最短可行走路徑（NavMesh + AI MoveTo）：可用。
- 俯視鏡頭＋ PLANNING／RUNNING／ARRIVED 遊戲循環：可用。
- Play 模式中移動、旋轉、縮放障礙物，並即時重新計算路徑（Dynamic NavMesh）：可用。
- `Lvl_PathfindingPuzzle` 單一路徑關卡：預設會被擋住，被擋住時自動回到編輯模式。可用。
- crash 風險掃描：沒有發現邏輯層面的 crash 風險。

## 導航

### 傳統 Devlog

- [2026-11-12 — 用 unreal-mcp 做 NavMesh 尋路解謎原型](./2026-11-12.md)

## 重要檔案

| 類型 | 路徑 |
|------|------|
| 關卡 | `/Game/Project/Maps/Lvl_PathfindingPuzzle` |
| 遊戲循環 | `/Game/Project/Programming/Blueprints/Pathfinding/BP_PathfindingPlayerController` |
| 角色 | `/Game/Project/Programming/Blueprints/Pathfinding/BP_PathfindingCharacter` |
| 障礙物 | `/Game/Project/Programming/Blueprints/Pathfinding/BP_EditableObstacle` |
| HUD | `/Game/Project/Programming/UI/WBP_PathfindingHUD` |

## 注意事項

1. 用 MCP 自動化測試時，`StopPIE` 和 `StartPIE` 不要放在同一個呼叫裡，否則會觸發 `GameViewport.IsUnique()` crash。
2. 專案目前不在 `~/Documents/Projects/Active/` 底下，也還沒登錄到 Project Hub 的 `server.js`，所以 Dashboard 不會掃描到它。
3. 專案還沒有任何 git commit，所有檔案都是 untracked。
