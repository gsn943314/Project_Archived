# mcptest — AI 協作指南

給在這個專案裡工作的 AI 助手（Claude Code / Codex）與組員看的規則。回覆一律使用繁體中文。

## 專案概要

NavMesh 尋路解謎原型。編輯階段（灰盒）玩家拖曳方塊與機關，按 PLAY 後切換成最終畫面，角色自動走最短路線到 B 點。

- 引擎：Unreal Engine 5.9，專案檔 `mcptest.uproject`
- AI 透過 `unreal-mcp`（Editor 內建 MCP server，`http://127.0.0.1:8000/mcp`，設定在 `.mcp.json`）操作 Editor
- 預設地圖：`/Game/Project/Maps/Lvl_BlockTutorial`

## 關卡

| 地圖 | 內容 |
|------|------|
| `Lvl_BlockTutorial` | 方塊教學（主關卡，手工設計） |
| `Lvl_BlockTutorial_V2` | 舊版生成器（3 條來回走道、爬 2 階，seed 11） |
| `Lvl_BlockTutorial_V5_Art` | V5 套用 MegaJam 美術（`/Game/Dev/Meshes`），每階 175 cm（樓梯模型高度壓成 0.5） |
| `Lvl_BlockTutorial_V3/V4/V5` | 新版生成器：蜿蜒折線路徑、約 10 階高低差（seed 33/55/77） |
| `Lvl_Terraces` | S 型往上爬的梯田關，含所有機關 |
| `Lvl_PathfindingPuzzle` | 最早的平面原型，含所有機關 |
| `Lvl_MainMenu` | 開始畫面（`BP_MenuGameMode` + `BP_MenuPlayerController` + `WBP_MainMenu`），打包預設地圖 |

## 核心藍圖（`/Game/Project/Programming/Blueprints/Pathfinding/`）

| 藍圖 | 職責 |
|------|------|
| `BP_PathfindingPlayerController` | 編輯操作、`DropFiller`/`ComputeDrop`（落點預覽與放置）、相機平移縮放、Phase 狀態機、HUD |
| `BP_PathfindingCharacter` | 主角，`StartRun` 用 NavMesh 走向 B |
| `BP_EditableObstacle` | 可拖曳方塊（紫色） |
| `BP_EnemyBlock` | 敵人方塊（紅色），PLAY 時若在路上會變成 `BP_EnemyChaser`；`AggroRadius` 0 = 永遠追 |
| `BP_EnemyChaser` | 追擊者（速度 620），碰到主角 → `OnCaught` |
| `BP_Gimmick` | 機關，`Kind`: 0 火 / 1 霧 / 2 水 / 3 聲音誘餌 / 4 壓力板 / 5 門 / 6 橋；壓力板與門/橋用相同 `LinkId` 連動 |

Phase：0 = PLANNING（灰盒）、1 = RUNNING（最終畫面）、2 = FINISHED。

## 必須遵守的規格

- **單位 U = 175 cm**。方塊尺寸、落點都對齊 175 cm 格；地圖格子 = 2U = 350 cm；樓層高度 1U。
- `SM_Cube` 是 100 cm、樞紐在角落；方塊 actor 樞紐在底部中心，scale 1.75 = 1U。
- Actor tag：`Editable`（可拖曳）、`Wall`（牆，方塊不能放上去）、`Hole`、`Gimmick`、`Boat`（只有它能浮在水上）。
- 地形 actor 放在 Outliner 資料夾 `Maze`，方塊 `Blocks`，機關 `Gimmicks`，提示文字 `Hints`。
- 樓梯靠鏡頭那一側（-X/-Y）不可以有牆擋住。

## 隨機關卡生成器

- 程式：`Content/Python/block_tutorial_gen.py`（`generate(seed)` 回傳 seed、尺寸、階數與解答）
- 版面：隨機折線路徑（直線段 3–12 格、走道間至少隔 3 格）、約 13 座樓梯（含 1 座下坡）爬到約 10 階；牆高取相鄰較低的一側，呈梯田感。`plan(seed)` 是純 Python，可在 Unreal 外測試。
- 按鈕：Editor 選單 **Puzzle → Generate Random Block Tutorial** 或工具列 **Random Level**（由 `Content/Python/init_unreal.py` 在啟動時註冊）
- 只會覆寫「目前開著、名稱含 BlockTutorial」的關卡。要新版本請先複製一張地圖再生成。

## 關卡編輯工具（標記 → Rebuild）

- `Content/Python/puzzle_level_tools.py`：`rebuild()` 讀取 `Editor` 資料夾的標記（`PathNode` tag 的 `Path<鏈>_<編號>` 球、`FloorMark` 藍片、`Hole` TargetPoint、`Blocks` 裡的方塊/敵人）重建 `Maze` 資料夾的地形，並移動 Point A/B、調整 NavMesh、`BUILDPATHS`、存檔。
- 相鄰兩個節點高度不同 → 中間自動放樓梯（需要足夠的直線格，不夠會出現警告）。方塊/敵人在牆上 → 自動挖凹槽。
- 格子原點存在 `Editor_Grid` actor。生成器也是先放標記再呼叫 `rebuild()`，所以 V3/V4/V5 與新生成的關卡都能直接編輯；`Lvl_BlockTutorial`、`V2` 沒有標記。
- 地形 actor（`Maze` 資料夾）由 Rebuild 管理（依 label 增量更新），不要手動改它們，改標記就好。
- **每階高度**：預設 175 cm；`Editor_Grid` 加 tag `TierH:350` 的關卡每階 350 cm（樓梯 = 2×2×2 格，碰撞用 35 階 10 cm 的隱形方塊，太粗的階梯 NavMesh 爬不上去）。洞的深度固定 175（`PIT`）。
- `puzzle_art.py`（選單 **Puzzle → Apply Art**）：樓梯 → `SM_PinkStone01`、走道地板 → `SM_StonePlatform01`、走道邊緣連續的邊合成一段，用接近原尺寸的模型貼著走道拼：3 格 `SM_StoneWall01`、2 格 `SM_StoneWallDecor`、1 格 `SM_StoneWallWindow`，轉角兩道牆互相穿插；樓梯兩側用斜的 `SM_StoneWallDamaged`（平地格＋樓梯格）；`Editor_Grid` 有 tag `Art` 時樓梯旁不再壓低牆（不留凹槽）；遠離走道的灰牆頂 → 少量 `SM_StoneCliff01/02`；灰色牆方塊維持原樣、外圍 → `SM_StoneWall01` 系列（3 格一段）、B 點 → `SM_Portal` 面向路徑。美術放在 `Art` 資料夾、無碰撞；被蓋住的灰盒方塊只隱藏、保留碰撞。改完標記 / Rebuild 後要再按一次 Apply Art。
- `live_edit.py`：`init_unreal.py` 啟動時註冊 Slate tick callback；有 `Editor_Grid` 的關卡中，標記停止移動 0.35 s 後磁吸、全部靜止 0.6 s 後 `rebuild(save=False, navmesh=False)`。PIE 時不動作。用 MCP 腳本移動標記時要注意 Live Edit 會跟著改位置。

## 用 MCP 改東西時的經驗（踩過的坑）

1. **不要在 `execute_python` 裡切換關卡**（`load_level`）— 會讓 Editor 閃退。改用 `EditorToolset.LevelToolset.LoadLevel` 工具，且單獨一次呼叫。
2. 改藍圖用 `BlueprintDslToolset.Write` 重寫**整個事件**；避免對大型圖表用 `Edit` 局部替換（曾讓 Editor 卡死）。
3. **每完成一步就存檔**（`save_asset` / `save_current_level`），Editor 可能隨時當掉。
4. 純函式節點會在每次使用時重新計算；`SetActorEnableCollision(false)` 之後 `GetActorBounds(onlyColliding)` 會變 0。
5. 建構腳本對元件碰撞的修改，會被 instance data 蓋回去；要改既有 actor 的元件碰撞請直接在 actor 上設。
6. 驗證要進 PIE 實測（移動方塊後至少等 2 秒讓 NavMesh 重建再 `StartRun`），不要只看程式邏輯。
7. 長時間的 PIE 測試分成多次呼叫，單次呼叫太久會逾時。
8. **標記不能有碰撞**：`PathNode`/`FloorMark` 標記用 `make_ghost()` 關掉碰撞（`set_actor_enable_collision(False)` + NoCollision profile）；只設元件 collision 不會保存，曾讓轉角的路徑點球擋住角色 → BLOCKED。`read_markers()` 會自動修正。
9. **牆不能和樓梯中段同高**：樓梯周圍的牆高度要高於最高一階（`stair_adj`），否則 NavMesh 會從樓梯接到牆頂。
10. **剛 LoadLevel 後 BUILDPATHS 會被鎖住**（log：`navigation build is locked`）而略過；等一下再執行。Live Edit 的 NavMesh watchdog 會在路徑為 0 點時自動重跑。
11. **角色不走 / 路徑是 0 個點**：通常是關卡裡的 `RecastNavMesh-Default` 壞掉（log 出現 `Unable to find RecastNavMesh instance`）。修法：刪掉該 actor → 稍微移動 `NavMeshBoundsVolume` → 執行 `BUILDPATHS`（有時要做兩次）→ 存檔。改動地形或 NavMesh 範圍後都要重建。

## 選單 / 設定（`/Game/Project/Programming/Blueprints/Menu/`）

- `BP_PuzzleGameInstance`：MasterVolume / MusicVolume / SfxVolume / Language（0 英文、1 繁中、2 簡中，語言按鈕循環切換），`LoadSettings`、`SaveSettings`（slot `PuzzleSettings`）、`ApplyAudio`。
- `BP_MenuPlayerController`：建立 `WBP_MainMenu`、綁定按鈕、`ShowPanel`、`UpdateTexts`（中英文字串都在這裡）。新增關卡要加按鈕 `BtnLvlN` 與事件 `OnLvlN`。
- `BP_PathfindingPlayerController` BeginPlay 會套用音量；`Esc` 回主選單。
- 角色 `FollowCameraArm`：第三人稱（長 520、俯角 20°、有延遲平滑）。
- 坑：**DSL Write 之後不要再呼叫 `compile_blueprint`**（會重複編譯而閃退）；修改 BP 的 class defaults（例如 GameMode 的 PlayerControllerClass）後要 `compile_blueprint` 再存檔，PIE 才會生效。

## 協作規則

- `.uasset` / `.umap` 是二進位檔（Git LFS），**無法合併**。同一個檔案同一時間只能一個人改。
- 開工前先 `git pull`；動到共用藍圖（上表那些）前先在群組說一聲。
- 新關卡請複製一張現有地圖改名（例如 `Lvl_<名字>_xxx`），在自己的地圖上做實驗。
- 開發紀錄寫在 `devlog/`。
