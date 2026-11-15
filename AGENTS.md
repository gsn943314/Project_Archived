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
- `puzzle_art.py`（選單 **Puzzle → Apply Art**）：樓梯 → `SM_PinkStone01`、走道地板 → `SM_StonePlatform01`、走道邊緣連續的邊合成一段，用接近原尺寸的模型貼著走道拼：3 格 `SM_StoneWall01`、2 格 `SM_StoneWallDecor`、1 格 `SM_StoneWallWindow`，轉角兩道牆互相穿插；樓梯兩側用斜的 `SM_StoneWallDamaged`（平地格＋樓梯格，scale 1，位置/朝向取自手動調好的 r5_c4，常數 `RAMP_*`；樓梯腳下是轉角時不用）；牆片一律 scale 1；`Editor_Grid` 有 tag `Art` 時樓梯旁不再壓低牆（不留凹槽）；遠離走道的灰牆頂 → 少量 `SM_StoneCliff01/02`；灰色牆方塊維持原樣、外圍 → `SM_StoneWall01` 系列（3 格一段）、B 點 → `SM_Portal` 面向路徑。美術放在 `Art` 資料夾、無碰撞；被蓋住的灰盒方塊只隱藏、保留碰撞。改完標記 / Rebuild 後要再按一次 Apply Art。
- **島嶼邊緣**（`ISLAND`）：外圈只留半格（`RIM` 175 cm）貼著走道的牆，再往外的地形直接切掉；`Maze_Backdrop` 降到 `BACKDROP_Z`（-1800），整個關卡像浮在下面的島。所有用 Rebuild 的關卡都適用。
- **灰盒 / 最終畫面切換**（`view_mode.py`，工具列 **Grey / Final**）：兩套都是 StaticMeshActor，只切顯示。tag `VisFinal`＝最終美術（資料夾名含 `Art`，手動放進去的也算）、`VisGrey`＝只在灰盒顯示（`Greybox` 資料夾的 `GB_` 代理方塊、被美術蓋住的 `Maze` 地板/樓梯方塊）。碰撞與 NavMesh 永遠只來自 `Maze`。切到 Grey 時依目前美術的 transform 與 `/Game/Project/Data/DT_GreyboxProfiles`（Box / Steps / Custom / None）重新產生 `GB_`；不要手改 `GB_`。遊戲中 `BP_PathfindingPlayerController.SetViewMode`：`EnterPlanning` 灰盒、`StartRun` 最終畫面。
- **手動美術保護**：生成的美術有 `ArtAuto` + `Gen:<transform>`；Apply Art 只重建沒被動過的。被移動/旋轉/縮放的自動鎖住，被刪掉/替換的位置記在 `Art_Registry`（tag `Slot:`）不再補；**Puzzle → Reset Selected Art** 還原。
- `live_edit.py`：`init_unreal.py` 啟動時註冊 Slate tick callback；有 `Editor_Grid` 的關卡中，標記停止移動 0.35 s 後磁吸、全部靜止 0.6 s 後 `rebuild(save=False, navmesh=False)`。PIE 時不動作。用 MCP 腳本移動標記時要注意 Live Edit 會跟著改位置。

## 牆體遮擋挖空（Occlusion Cutout）

鏡頭和目標之間的美術牆 / 懸崖會挖出一個不規則的洞（撕紙邊＋暖色描邊），看得到牆後面的小狐或方塊。地板、樓梯、道具不會被挖。

- **資源**：`/Game/Dev/Materials/MPC_Occlusion`（`Enable`、`Target`、`Radius` 170、`NearMargin` 60、`FootOffset` -40、`EdgeNoise`、`RimWidth`、`RimColor`；預設 `Enable = 0`），`/Game/Dev/Materials/Functions/MF_OcclusionCutout`（HLSL 原始碼 `Tools/StorybookPP/Occlusion_Cutout.hlsl`，建置腳本 `Tools/StorybookPP/build_occlusion.py`）。挖空範圍是從鏡頭出發的圓錐，螢幕上大小不隨縮放改變；只挖「比目標更靠近鏡頭、且高於目標腳底」的像素。
- **材質**：`M_Master` 是 **Masked**；Base Color 與 Opacity Mask 前面各有 static switch `OcclusionCutout`（關閉＝遮罩恆為 1，不挖）。目前打開開關的 MI：`MI_StoneWall01/Decor/Window/Damaged`、`MI_StoneCliff01–11`、`MI_StoneArchway`、`MI_StoneArchRuined`、`MI_StoneMonument`、`MI_Portal`、`MI_MossStone01`、`MI_PinkMossStone01/02`、`MI_SmallRockSet`。**要讓新的美術也能被挖：在它的 MI 勾 `OcclusionCutout`**（並加進 `build_occlusion.py` 的 `WALL_MIS`）。
- **灰盒**：`M_PrototypeGrid` 也接了同樣的開關（`MI_MazeWall` 已勾），但母材質仍是 Opaque，所以灰盒牆目前不會被挖；要啟用就把 `M_PrototypeGrid` 改成 Masked。
- **驅動**：`BP_PathfindingPlayerController.UpdateOcclusion`（`ReceiveTick` 最後呼叫）每幀寫 MPC：Phase 1/2 目標＝小狐；Phase 0 拖曳中目標＝被拖的方塊（+90 cm）；其他時候 `Enable = 0`。
- **還沒做**：編輯階段滑鼠「穿過」被挖開的牆點到後面的方塊（拾取仍會被 `Maze` 牆的碰撞擋住）。
- 坑：
  1. **MI 的 Base Property Overrides 改成 Masked 不會生效**（能編譯但不裁切），母材質本身必須是 Masked。
  2. **`MF_OcclusionCutout` 被母材質引用後不要刪掉節點重建**：輸出會換 id，母材質的連線全部斷掉、所有用它的材質編譯失敗。`build_mf()` 對已存在的函式只更新 HLSL。
  3. Python 裡 `UKismetMaterialLibrary` 叫 `unreal.MaterialLibrary`（Kismet 前綴會被去掉）。

## 小狐外觀進度（`/Game/Dev/Blueprints/BP_FoxLook`，feature/fox-look）
- 由 `BP_PathfindingGameMode` BeginPlay 生成，不改小狐 / 控制器藍圖。Stage：0 灰模（無動畫）→ 1 白模（有動畫）→ 2 原貼圖。
- Level0 = 0；Level1 = 0，石碑（網格名含 "Monument"）→ 1：運行中小狐離出口（`NextLevel`）9 m 內時，把小狐 `Hops` 剩下的路線換成「NavMesh 走到石碑朝出口側 2.5 m 的站位點 → 直接走到路線終點」，到站位點觸發演出（算不出路時退回：離出口 5 m 內觸發；RESET 回起點會重新啟用）；Level2 = 1（`?Stage2` 為 2），走到 `StageGoal`（Checkpoint_Shrine）→ 2；其他地圖 = 2。
- 灰模：真網格隱藏，`StatueMesh`（PoseableMesh）掛在網格上，開局 0.2 s 複製待機姿勢後定格（角色 Tick 每幀重播動畫，關 Tick 壓不住）。材質 `/Game/Dev/Materials/FoxLook/M_FoxClay`、`M_FoxWhite`。
- 觸發時「資產修復」演出：小狐停下、轉向觸發物，追擊者 CustomTimeDilation 0；`WBP_Dialogue` 逐句顯示（系統行綠字、小狐白字），含 "Reloading" 的系統行帶進度條，期間新舊外觀閃爍，結束時定為新外觀並閃暖光；播完若原本在走且 Phase == 1 則繼續走。
- 台詞：觸發物上的 `Say:<文字>` tag 覆蓋預設，`Say:SYS:<文字>` 為系統行；沒有 tag 時用藍圖內英文預設。

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
- 操作：編輯時左鍵拖方塊、在空白處拖曳＝平移畫面（`StartLeftPan`）；滾輪縮放；右鍵左右拖＝繞畫面中心左右旋轉（`bOrbiting`，用 `GetInputMouseDelta`，俯角固定；右鍵按住時游標被 capture，`GetMousePosition` 不會變）；中鍵/方向鍵平移。PLAY 中沒有視角旋轉。
- 角色 `FollowCameraArm`：第三人稱（長 520、俯角 20°、有延遲平滑）。
- 坑：**DSL Write 之後不要再呼叫 `compile_blueprint`**（會重複編譯而閃退）；修改 BP 的 class defaults（例如 GameMode 的 PlayerControllerClass）後要 `compile_blueprint` 再存檔，PIE 才會生效。

## 協作規則

- `.uasset` / `.umap` 是二進位檔（Git LFS），**無法合併**。同一個檔案同一時間只能一個人改。
- 開工前先 `git pull`；動到共用藍圖（上表那些）前先在群組說一聲。
- 新關卡請複製一張現有地圖改名（例如 `Lvl_<名字>_xxx`），在自己的地圖上做實驗。
- 開發紀錄寫在 `devlog/`。
