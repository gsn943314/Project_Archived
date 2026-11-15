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
| `Lvl_Level2` | Level 2（Forgotten Wilds / Hollow Shrine，`level2_build.py` 生成；改版面改那支檔再 `build()`）：2-1 右邊填洞＋旋轉橋＋3 階樓梯、左邊填洞＋野獸（箱子擋門）＋水車升降梯（3 階，開場在上面）→ Checkpoint → 2-2 填洞、旋轉橋、守衛在高台（它的升降梯留在上面它就會坐下來攻擊）、填洞、升降梯（3 階）上到 B。16×20 格、8 階 |
| `Lvl_Level0_Davidtesting` | Level 0（複製自組員的 `/Game/Dev/Lvl_Level0_Storybook`，手擺美術）：開場狐狸走到佈告欄（TargetPoint `IntroSpot`）看對話，點完進灰盒；直線路徑 → 3 格斷崖坑（`FillSlot_c4/5/6`）→ 樓梯 → 傳送門。3 個方塊上掛直立的石頭（Placement1），填進坑後最終畫面換成躺平的石橋（Placement2）。`Editor_Grid` tag `MazeGreyOnly`（Maze 只在灰盒顯示，美術地台＝最終畫面）；這關走道只有一格寬，`RecastNavMesh` 半徑用 35（120 會把走道侵蝕光） |
| `Lvl_BlockTutorial_V3/V4/V5` | 新版生成器：蜿蜒折線路徑、約 10 階高低差（seed 33/55/77） |
| `Lvl_Terraces` | S 型往上爬的梯田關，含所有機關 |
| `Lvl_PathfindingPuzzle` | 最早的平面原型，含所有機關 |
| `Lvl_MainMenu` | 開始畫面（`BP_MenuGameMode` + `BP_MenuPlayerController` + `WBP_MainMenu`），打包預設地圖 |

## 核心藍圖（`/Game/Project/Programming/Blueprints/Pathfinding/`）

| 藍圖 | 職責 |
|------|------|
| `BP_PathfindingPlayerController` | 編輯操作、`DropFiller`/`ComputeDrop`（落點預覽與放置）、相機平移縮放、Phase 狀態機、HUD |
| `BP_PathfindingCharacter` | 主角，`StartRun` 用 NavMesh 走向 B。模型是狐狸 `SK_Fox`（`/Game/Project/Art/Characters/Fox/`，scale 1.8），`Tick` 裡的動畫狀態機：0 idle / 1 walk（速度 < 250）/ 2 run（跑起來後速度低於 100 持續 0.25 s 才切出，轉角交接的瞬間停頓不會讓跑步動畫重播） / 3 倒地（`KnockDown`，被抓時由 `OnCaught` 呼叫，2 秒後 `ResetToStart`）；用 `PlayAnimation` 單節點播放、動畫一律 1 倍速播放（跑步用 `A_Fox_FastRun`，步伐約 360 cm/s，角色 MaxWalkSpeed = 500；加速播放頭會狂晃），走路 / 跑步是原地版本（in place），Enable Root Motion 與 Force Root Lock 都關閉 |
| `BP_EditableObstacle` | 可拖曳方塊（紫色） |
| `BP_EnemyBlock` | 敵人方塊（紅色），PLAY 時若在路上會變成 `BP_EnemyChaser`；`AggroRadius` 0 = 永遠追 |
| `BP_EnemyChaser` | 追擊者（速度 620），碰到主角 → `OnCaught` |
| `BP_Mechanism` | Level 2 機關（tag `Mechanism`，編輯時點一下觸發、不能拖）：`Kind` 0 = 升降梯（停在上緣或下緣，`bUp` = 開場在上面；點一下換到另一端；PLAY 中角色或敵人停在上面就被送到另一端；`RideScore` 判斷搭它能不能到目標，角色和追擊者走不到目標時會自動去搭），1 = 旋轉橋（每點一次轉 90°；河要 2 格寬，沒轉就過不去），2 = 單向旋轉門（鉸鍊在 actor 位置、門板沿 local +X；`Mesh` 相對位置設 (0,-50,0)；三下一輪：關、轉 90° 仍關、再轉 90° 開，再轉 180° 回到關；例：Davidtesting 的 `Gate_Pocket` + 美術 `SM_WoodFence` attach 在上面，口袋其餘開口用隱形牆 `GateWall_Pocket` 封住） |
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
- **加寬地板**（工具列 **Wide**，`add_wide`）：單一棕色方塊標記（`Editor/Wide`，tag `FloorMark` + `WideMark`），地形和一般 Floor 一樣，用來讓走道看起來更寬。
- **不相連的節點**：路徑點名稱結尾加 `J`（例如 `PathA_07J`）＝不和上一個節點連成走道（升降台頂端用）。
- **偽裝 / hover**：Level 2 的方塊、敵人、橋、升降梯帶 tag `Disguise`：編輯器裡保留原本顏色（紫 / 紅 / 木頭橘 / 黃），遊戲中由各藍圖的 `BeginPlay` 換成琥珀色的 `MI_Interactable`（和路面區隔）；編輯模式滑鼠移到 tag `Editable` / `Mechanism` 的東西上會畫白框（`ReceiveTick`）。敵人大小 = 方塊 2×2×1（`L_SCALE`）。
- **分段關卡**：tag `StageGoal` 的 actor 是第一段的終點（Level 2 的 checkpoint）。走到後回到灰盒編輯，鏡頭移到 tag `StageCam` 的 TargetPoint，目標換成 Point B（`BP_PathfindingCharacter.FinalTarget`，`BP_PathfindingPlayerController.OnStageCleared`）。注意 `OverviewCamera` 是用 `GetActorOfClass(CameraActor)` 找的，關卡裡只能有一台 CameraActor。
- **開場對話**（`BP_PathfindingPlayerController.PlayIntro` / `ShowIntroDialogue` / `NextLine`）：關卡裡有 tag `IntroSpot` 的 TargetPoint 時，BeginPlay 不直接進灰盒：Phase 3、隱藏 HUD、最終畫面，Point A 走到該點並轉成它的朝向，畫面下方 `WBP_Dialogue` 依序顯示它的 tag `Say:<文字>`，左鍵下一句，最後一句後回起點並 `EnterPlanning`。
- **填坑換美術**（`SetViewMode`）：tag `FillSlot` 的 TargetPoint（放在坑的格子中心），attach 在它上面的美術只在「最終畫面且有方塊填進這個坑」時顯示，填坑方塊自己 attach 的美術則隱藏。
- **Checkpoint**：tag `Checkpoint` 的 actor；角色經過（2D 260 cm 內）時把它存成新的起點，被抓或 RESET 後從這裡重來（`BP_PathfindingCharacter` Tick）。
- 相鄰兩個節點高度不同 → 中間自動放樓梯（需要足夠的直線格，不夠會出現警告）。方塊/敵人在牆上 → 自動挖凹槽。
- 格子原點存在 `Editor_Grid` actor。生成器也是先放標記再呼叫 `rebuild()`，所以 V3/V4/V5 與新生成的關卡都能直接編輯；`Lvl_BlockTutorial`、`V2` 沒有標記。
- 地形 actor（`Maze` 資料夾）由 Rebuild 管理（依 label 增量更新），不要手動改它們，改標記就好。
- **每階高度**：預設 175 cm；`Editor_Grid` 加 tag `TierH:350` 的關卡每階 350 cm（樓梯 = 2×2×2 格，碰撞用 35 階 10 cm 的隱形方塊，太粗的階梯 NavMesh 爬不上去）。洞的深度固定 175（`PIT`）。
- `puzzle_art.py`（只在選單 **Puzzle → Apply Art**，工具列已移除，避免誤按）：樓梯 → `SM_PinkStone01`、走道地板 → `SM_StonePlatform01`、走道邊緣連續的邊合成一段，用接近原尺寸的模型貼著走道拼：3 格 `SM_StoneWall01`、2 格 `SM_StoneWallDecor`、1 格 `SM_StoneWallWindow`，轉角兩道牆互相穿插；樓梯兩側用斜的 `SM_StoneWallDamaged`（平地格＋樓梯格，scale 1，位置/朝向取自手動調好的 r5_c4，常數 `RAMP_*`；樓梯腳下是轉角時不用）；牆片一律 scale 1；`Editor_Grid` 有 tag `Art` 時樓梯旁不再壓低牆（不留凹槽）；遠離走道的灰牆頂 → 少量 `SM_StoneCliff01/02`；灰色牆方塊維持原樣、外圍 → `SM_StoneWall01` 系列（3 格一段）、B 點 → `SM_Portal` 面向路徑。美術放在 `Art` 資料夾、無碰撞；被蓋住的灰盒方塊只隱藏、保留碰撞。改完標記 / Rebuild 後要再按一次 Apply Art。
- **島嶼邊緣**（`ISLAND`）：外圈只留半格（`RIM` 175 cm）貼著走道的牆，再往外的地形直接切掉；`Maze_Backdrop` 降到 `BACKDROP_Z`（-1800），整個關卡像浮在下面的島。所有用 Rebuild 的關卡都適用。
- **灰盒 / 最終畫面切換**（`view_mode.py`，工具列 **Grey / Final**）：兩套都是 StaticMeshActor，只切顯示。tag `VisFinal`＝最終美術（資料夾名含 `Art`，手動放進去的也算）、`VisGrey`＝只在灰盒顯示（`Greybox` 資料夾的 `GB_` 代理方塊、被美術蓋住的 `Maze` 地板/樓梯方塊）。碰撞與 NavMesh 永遠只來自 `Maze`。切到 Grey 時依目前美術的 transform 與 `/Game/Project/Data/DT_GreyboxProfiles`（Box / Steps / Custom / None）重新產生 `GB_`；不要手改 `GB_`。`Editor_Grid` 有 tag `GreyMaze` 的手擺美術關卡（Camp）樓梯與地板不產生 `GB_`（灰盒＝`Maze` 樓梯，最終畫面隱藏被 `SM_PinkStone01` 蓋住的 `Maze_Stair`），牆、門等其他美術照常產生 `GB_`；拱門（mesh 名含 `Arch`）預設產生兩柱＋橫樑的 `GB_`。Live Edit 偵測到美術移動 / 新增 / 刪除後會自動重產 `GB_`。可拖曳方塊上的美術（例如 `ArtCrate_`）要設 Movable 並 attach 到方塊上才會跟著移動。遊戲中 `BP_PathfindingPlayerController.SetViewMode`：`EnterPlanning` 灰盒、`StartRun` 最終畫面。
- **Storybook 外皮**（`storybook_skin.py`，`Editor_Grid` 有 tag `StorybookSkin` 的關卡，目前是 `Lvl_Camp_Whitebox_Davidtesting`）：每個 `Maze_Path/Wall` 複製一份最終材質的分身（走道 `MI_PavingD`、牆 `MI_GrassTopSoilSides`；樓梯不做分身，一律用 `SM_PinkStone01` 樓梯模型，避免重疊，資料夾 `Camp_ArtSkin`，tag `VisFinal`+`NoGreybox`），原本的 Maze 方塊加 `VisGrey`+`Skinned`。每次 Rebuild 後自動重產。從 `/Game/Dev/Lvl_StorybookPreview` 複製來的包邊物件在 `Camp_ArtPreview/Storybook`（tag `NoGreybox`，不產生灰盒）。
- **手動美術保護**：生成的美術有 `ArtAuto` + `Gen:<transform>`；Apply Art 只重建沒被動過的。被移動/旋轉/縮放的自動鎖住，被刪掉/替換的位置記在 `Art_Registry`（tag `Slot:`）不再補；**Puzzle → Reset Selected Art** 還原。
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
13. **走在路中間**：角色不再用 `AIMoveTo` 一段段走（每段結束會停一下），改在 `Tick` 用 `AddMovementInput` 沿 `Hops` 連續前進（轉角 70 cm 內換下一點、最後一點 40 cm），0.6 s 沒前進＝路斷了 → BLOCKED；`can_walk_off_ledges` 關閉，不會走進坑裡。`BP_PathfindingCharacter.StartRun` 把 NavMesh 路徑的每個轉角用 `SnapCell` 移到所在 350 cm 格子的正中央（只在平地：格子中心的 NavMesh 高度和原點不同＝在樓梯上，就只對齊橫越樓梯的那一軸，並在後面補上 NavMesh 原本的轉角＝樓梯腳，免得在樓梯半途轉彎走下樓梯側邊）（格子原點 = tag `EditorGrid` 的 `Editor_Grid`，`get_grid()` 會自動加 tag；沒有就不對齊）。
12. **導航半徑 AgentRadius = 120**（`DefaultEngine.ini` 與各關卡的 `RecastNavMesh-Default`）：讓角色走在路中間、不貼著牆和模型邊緣。舊關卡的 RecastNavMesh 仍是 35，要改那個 actor 的 agent_radius 再 BUILDPATHS。
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
