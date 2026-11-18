# Project Archived (Project_Archived) — AI 協作指南

給在這個專案裡工作的 AI 助手（Claude Code / Codex）與組員看的規則。回覆一律使用繁體中文。

## 專案概要

NavMesh 尋路解謎原型。編輯階段（灰盒）玩家拖曳方塊與機關，按 PLAY 後切換成最終畫面，角色自動走最短路線到 B 點。

- 引擎：Unreal Engine 5.9，專案檔 `Project_Archived.uproject`（原 `mcptest.uproject` → `project_archive.uproject`）
- AI 透過 `unreal-mcp`（Editor 內建 MCP server，`http://127.0.0.1:8000/mcp`，設定在 `.mcp.json`）操作 Editor
- 預設地圖：`/Game/Project/Maps/Lvl_BlockTutorial`

## 關卡

| 地圖 | 內容 |
|------|------|
| `Lvl_BlockTutorial` | 方塊教學（主關卡，手工設計） |
| `Lvl_BlockTutorial_V2` | 舊版生成器（3 條來回走道、爬 2 階，seed 11） |
| `Lvl_BlockTutorial_V5_Art` | V5 套用 MegaJam 美術（`/Game/Dev/Meshes`），每階 175 cm（樓梯模型高度壓成 0.5） |
| `Lvl_Level2` | Level 2（Forgotten Wilds / Hollow Shrine，`level2_build.py` 生成；改版面改那支檔再 `build()`）：2-1 右邊填洞＋旋轉橋＋3 階樓梯、左邊填洞＋野獸（箱子擋門）＋水車升降梯（3 階，開場在上面）→ Checkpoint → 2-2 填洞、旋轉橋、守衛在高台（它的升降梯留在上面它就會坐下來攻擊）、填洞、升降梯（3 階）上到 B。16×20 格、8 階。美術（`Art` / `Art_L2Terrain` / `Art_L2Cliff` / `Art_Registry`）與佈景 `Art_L2Setdress`（散放的樹叢、藤蔓、岩石，無碰撞）整合自組員的 `/Game/Dev/Lvl_Level2Setdress_Lindatesting`；玩法（Maze、方塊、機關、終點 tag、相機、燈光）仍以這張為準，再整合時照同樣分法。2-1 與 2-2 之間的存檔點 `Checkpoint_Shrine` 的圓柱已隱藏（tag 照舊、仍是 StageGoal；位置移到轉角格靠北的 (2625, 3780)，小狐停在水晶前約 2 m，不會疊到水晶，2-2 也從這裡出發），外觀：灰盒＝圓錐 `Checkpoint_Cone`（`/Engine/BasicShapes/Cone`，原圓柱的綠色材質 `MI_G_PlateOn`，tag `VisGrey`），最終畫面＝組員的水晶 `Checkpoint_Crystal`（tag `VisFinal`；兩者都在資料夾 `Mechanisms`，不是 Art 資料夾，所以 Sync Greybox 不會替它產生 `GB_`；`/Game/Dev/Meshes/SM_SaveCrystal`，0.5 倍；圓錐 1.1×1.1×1.4；兩者都在同一格靠南牆那側 (2625, 3570)，無碰撞），小狐不會站進水晶裡 |
| `Lvl_Level0` | Level 0（原 `Lvl_Level0_Davidtesting`，改名後舊檔仍保留、選單與打包已改用 `Lvl_Level0`；複製自組員的 `/Game/Dev/Lvl_Level0_Storybook`，手擺美術）：兩座島（草地範圍全用 Wide 鋪成灰盒地板，中間 3 格斷崖）；佈告欄在原位原朝向（路中間、正面朝起點，`NoticeBoard_Blocker` 隱形碰撞讓角色繞過），開場狐狸走到它前面（TargetPoint `IntroSpot`）看對話，點完進灰盒；起點 → 繞過佈告欄 → 3 格斷崖坑（`FillSlot_c4/5/6`）→ 樓梯 → 傳送門。3 個方塊上掛直立的石頭（Placement1），填進坑後最終畫面換成躺平的石橋（Placement2）。`Editor_Grid` tag `MazeGreyOnly`（Maze 只在灰盒顯示，美術地台＝最終畫面）；這關走道只有一格寬，`RecastNavMesh` 半徑用 35（120 會把走道侵蝕光）。灰盒總覽鏡頭是「接近 isometric 的窄視角透視」（`OverviewCamera` FOV 30°、pitch -45°、yaw -45°、距離約 5600 cm；純正交鏡頭和跟拍鏡頭混合時會飛很遠、看起來也怪，已改回透視；`ZoomCamera` 仍支援正交鏡頭＝改 OrthoWidth），PLAY 跟拍仍是第三人稱 |
| `Lvl_Level1` | Level 1（原 `Lvl_Camp_Whitebox_Davidtesting` 改名）Camp 手擺美術關（Storybook 外皮，Level 0 的下一關）：灰盒總覽鏡頭和 Level 0 一樣用俯角 45° 的窄視角（FOV 60°、距離約 5600 cm；更窄要放更遠，Storybook 後製會讓遠處整片發白），終點傳送門 `SM_StoneArchway` 產生拱門形 `GB_` |
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
| `BP_Mechanism` | Level 2 機關（tag `Mechanism`，編輯時點一下觸發、不能拖；點了還沒動完就按 PLAY 時，Phase 1 的第一幀直接跳到目標高度 / 角度（搭乘中 `bRiding` 除外），小狐 0.6 s 後算路線時用的是完成後的地形，不會原地不動）：`Kind` 0 = 升降梯（停在上緣或下緣，`bUp` = 開場在上面；點一下換到另一端；PLAY 中角色或敵人停在上面就被送到另一端；`RideScore` 判斷搭它能不能到目標，角色和追擊者走不到目標時會自動去搭），1 = 旋轉橋（每點一次轉 90°；河要 2 格寬，沒轉就過不去），2 = 單向旋轉門（鉸鍊在 actor 位置、門板沿 local +X；`Mesh` 相對位置設 (0,-50,0)；三下一輪：關、轉 90° 仍關、再轉 90° 開，再轉 180° 回到關；例：Davidtesting 的 `Gate_Pocket` + 美術 `SM_WoodFence` attach 在上面，口袋其餘開口用隱形牆 `GateWall_Pocket` 封住） |
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
- **偽裝 / hover**：所有關卡的方塊、敵人方塊、機關（橋、升降梯、門）在編輯器裡保留原本顏色（紫 / 紅 / 木頭橘 / 黃），遊戲中（灰盒階段起）一律由各藍圖的 `BeginPlay` 換成統一的琥珀色 `MI_Interactable`（不再看 `Disguise` tag）；編輯模式滑鼠移到 tag `Editable` / `Mechanism` 的東西上會畫白框（`ReceiveTick`）。敵人大小 = 方塊 2×2×1（`L_SCALE`）。
- **分段關卡**：tag `StageGoal` 的 actor 是第一段的終點（Level 2 的 checkpoint）。走到後回到灰盒編輯，鏡頭移到 tag `StageCam` 的 TargetPoint，目標換成 Point B（`BP_PathfindingCharacter.FinalTarget`，`BP_PathfindingPlayerController.OnStageCleared`）。注意 `OverviewCamera` 是用 `GetActorOfClass(CameraActor)` 找的，關卡裡只能有一台 CameraActor。
- **開場運鏡**（`BP_PathfindingPlayerController.FlyIntro`，第一次 `EnterPlanning` 時，`bFlyDone`；有開場對話 `IntroSpot` 的關卡（Level 0）不播）：用總覽鏡頭的角度，先拉近 Point A（距離 1700）1.2 s → 2.5 s 滑到終點（角色的 `FinalTarget`，沒有就用 `TargetPoint`）停一下 → 2 s 拉回總覽鏡頭；過程中 Phase 3（不能操作），暫時的 CameraActor 結束後刪除。
- **過場動畫用的是專案副本**：`/Game/Project/Programming/UI/Cinematics/WBP_Scene0_Cutscene`、`WBP_Ending_Cutscene`（複製自組員 `/Game/Dev/Cinematics/...`，Dev 原版不動；控制器 `StartOpeningCutscene` / `PlayEnding` 建立的是副本）。字幕都包在對話框 `CapBoxN`（Border）裡：小狐 / 角色台詞用 Storybook `T_UI_Dialogue_A_Body`（深棕字 34 Bold、自動換行，Padding 110/95/140/80，左右離畫面 220），開場 ERROR 那格（`Caption5`「Cutscene interrupted. / Returning to Edit Mode…」）用系統框 `T_UI_SystemLog_07_Body`（深藍字）。開場的 `Caption3` 被轉場動畫控制顏色（會變白字看不到），所以框裡放的是新的 `FoxLine3`，原 `Caption3` 隱藏。結尾 `PlayCutscene` 改成字幕和切畫面同時設定、拿掉換句前清空 0.3 s（併進前一句停留時間），不會出現空框，總長度不變。
- **開場動畫 / 結束動畫**（`PlayIntro` / `OnOpeningDone`、`PlayEnding` / `OnEndingDone`）：有 `IntroSpot` 的關卡（Level 0）開場小狐先走到佈告欄前（`IntroSpot`）轉向、停 1 秒，再播組員的 `WBP_Scene0_Cutscene`（`StartOpeningCutscene`，取代佈告欄對話），播完（`OnCutsceneFinished`）直接進灰盒；抵達帶 tag `PlayEnding` 的終點（Level 2 的 `PointB_Target`）播 `WBP_Ending_Cutscene`，播完（`OnEndingFinished`）回主選單。
- **（舊）開場對話**（`BP_PathfindingPlayerController.PlayIntro` / `ShowIntroDialogue` / `NextLine`）：關卡裡有 tag `IntroSpot` 的 TargetPoint 時，BeginPlay 不直接進灰盒：Phase 3、隱藏 HUD、最終畫面，Point A 走到該點並轉成它的朝向，畫面下方 `WBP_Dialogue` 依序顯示它的 tag `Say:<文字>`，左鍵下一句，最後一句後回起點並 `EnterPlanning`。
- **填坑換美術**（`SetViewMode`）：tag `FillSlot` 的 TargetPoint（放在坑的格子中心），attach 在它上面的美術只在「最終畫面且有方塊填進這個坑」時顯示，填坑方塊自己 attach 的美術則隱藏。
- **後段晚點出現**（`Editor_Grid` tag `RevealAfterX:<x>`，`storybook_skin.tag_reveal()`，Rebuild / Sync Greybox 後自動補 tag）：中心在 x 之後的 Maze、美術、`GB_`、方塊與其美術加 tag `RevealAfterFill`；遊戲中在第一個方塊填進坑（`FillSlot`）之前全部隱藏、方塊點不到，填進去後 `CheckReveal`（`DropFiller` 之後呼叫）把它們顯示出來。Level 0 用 175：一開始只有第一格坑，另外兩格坑和整座後島都先不出現。
- **斷崖只看得到引導**（`Editor_Grid` tag `GapX:<x0>:<x1>`，`storybook_skin.tag_gap()`，Rebuild 後自動補）：中心在這段 x 範圍內的坑底與坑邊整格的牆加 tag `NoShow`（缺口兩端的牆縮成半格 RIM 保留，島照樣被邊牆圍起來，只留路口）：遊戲與編輯器都不顯示、碰撞保留（方塊照樣落在坑底），兩座島看起來是分開的；每格坑放一個半透明的引導方塊（資料夾 `Guides`，`M_GuideGhost`，tag `VisGrey` + `FillGhost`，後兩格加 `RevealAfterFill`）。Level 0 用 -175:875。
- **下一關**（`OnRunFinished`）：抵達終點時，若有 tag `NextLevel` 的 actor，讀它的 tag `Level:<地圖名>`，2 秒後 `OpenLevel` 切過去。Level 0 的 `PointB_Target` → `Lvl_Level1`，Level 1 的 → `Lvl_Level2`。
- **擋路提示，多個停點**：走不到終點時，在所有 `BlockedStop` 裡挑「走得到（完整路徑）且離終點最近」的那一個（`BP_PathfindingCharacter.StartRun`，`StopBest`）。Level 0 有三個：`CliffStop`（山還在原位：看山）、`GapStop` (-280, 0)（山移走了但第一格坑沒填：走到懸崖邊）、`BridgeStop` (0, 0)（只填了第一格：站在方塊上，對岸的島剛出現）。帶 tag `LookFwd` 的停點讓小狐面向停點自己的正前方（+X，看懸崖 / 對岸），而不是最近的方塊，之後也不畫指向方塊的箭頭（`ShowHint`）。停點不要放在方塊前緣，會被邊緣碰撞擋住、一直走不到（`BridgeStop` 原本在 (60, 0) 就卡住）。山的美術 `ArtRock_Block_Cliff` 水平縮成 0.55 倍（約 470 × 520 cm），移到路邊時不會蓋到隔壁走道。以下是原本的說明：
- **擋路提示**（tag `BlockedStop` 的 TargetPoint，Level 0 的 `CliffStop` 在 (-890, 350)，貼著山；它和格子中心 (-1050, 350) 在同一格的靠山側，角色走完 L 形路線後直走過去、不會掉頭；停在這裡的期間（`bHintPending`）`UpdateOcclusion` 關閉挖空）：走不到終點時，只要還有 `Editable` 方塊在它 1000 cm 內（方塊沒被移走），角色停在這個點（`BP_PathfindingCharacter.StartRun`）並轉身面向擋路的方塊（`ShowHint`），BLOCKED 後回起點，再用 `WBP_Dialogue` 一句一句顯示它的 `Say:` tag（`ShowHint` / `StartHintDialog` / `UpdateHint`，每句 2.8 s，最後一句後關閉），接著在那個方塊上畫上下浮動的黃色箭頭＋框，直到方塊被移走、第一個坑被填或按 PLAY（`HideHint`）。
- **Checkpoint**：tag `Checkpoint` 的 actor；角色經過（2D 260 cm 內）時把它存成新的起點，被抓或 RESET 後從這裡重來（`BP_PathfindingCharacter` Tick）。
- 相鄰兩個節點高度不同 → 中間自動放樓梯（需要足夠的直線格，不夠會出現警告）。方塊/敵人在牆上 → 自動挖凹槽。
- 格子原點存在 `Editor_Grid` actor。生成器也是先放標記再呼叫 `rebuild()`，所以 V3/V4/V5 與新生成的關卡都能直接編輯；`Lvl_BlockTutorial`、`V2` 沒有標記。
- 地形 actor（`Maze` 資料夾）由 Rebuild 管理（依 label 增量更新），不要手動改它們，改標記就好。
- **每階高度**：預設 175 cm；`Editor_Grid` 加 tag `TierH:350` 的關卡每階 350 cm（樓梯 = 2×2×2 格，碰撞用 35 階 10 cm 的隱形方塊，太粗的階梯 NavMesh 爬不上去）。洞的深度固定 175（`PIT`）。
- `puzzle_art.py`（只在選單 **Puzzle → Apply Art**，工具列已移除，避免誤按）：樓梯 → `SM_PinkStone01`、走道地板 → `SM_StonePlatform01`、走道邊緣連續的邊合成一段，用接近原尺寸的模型貼著走道拼：3 格 `SM_StoneWall01`、2 格 `SM_StoneWallDecor`、1 格 `SM_StoneWallWindow`，轉角兩道牆互相穿插；樓梯兩側用斜的 `SM_StoneWallDamaged`（平地格＋樓梯格，scale 1，位置/朝向取自手動調好的 r5_c4，常數 `RAMP_*`；樓梯腳下是轉角時不用）；牆片一律 scale 1；`Editor_Grid` 有 tag `Art` 時樓梯旁不再壓低牆（不留凹槽）；遠離走道的灰牆頂 → 少量 `SM_StoneCliff01/02`；灰色牆方塊維持原樣、外圍 → `SM_StoneWall01` 系列（3 格一段）、B 點 → `SM_Portal` 面向路徑。美術放在 `Art` 資料夾、無碰撞；被蓋住的灰盒方塊只隱藏、保留碰撞。改完標記 / Rebuild 後要再按一次 Apply Art。
- **島嶼邊緣**（`ISLAND`）：外圈只留半格（`RIM` 175 cm）貼著走道的牆，再往外的地形直接切掉；`Maze_Backdrop` 降到 `BACKDROP_Z`（-1800），整個關卡像浮在下面的島。所有用 Rebuild 的關卡都適用。
- **路徑預覽開關**（工具列 **Path On / Off**，`view_mode.toggle_path()`）：切換 `BP_PathfindingPlayerController.bShowPath`（class default，會存檔，PIE 中也即時生效），關掉時遊戲裡不畫最短路徑線（`DrawPathPreview`）。
- **灰盒 / 最終畫面切換**（`view_mode.py`，工具列 **Grey / Final**）：兩套都是 StaticMeshActor，只切顯示。tag `VisFinal`＝最終美術（資料夾名含 `Art`，手動放進去的也算）、`VisGrey`＝只在灰盒顯示（`Greybox` 資料夾的 `GB_` 代理方塊、被美術蓋住的 `Maze` 地板/樓梯方塊）。碰撞與 NavMesh 永遠只來自 `Maze`。切到 Grey 時依目前美術的 transform 與 `/Game/Project/Data/DT_GreyboxProfiles`（Box / Steps / Custom / None）重新產生 `GB_`；不要手改 `GB_`。`Editor_Grid` 有 tag `GreyMaze` 的手擺美術關卡（Camp）樓梯與地板不產生 `GB_`（灰盒＝`Maze` 樓梯，最終畫面隱藏被 `SM_PinkStone01` / `SM_StoneStairs` 蓋住的 `Maze_Stair`），牆、門等其他美術照常產生 `GB_`；拱門與傳送門（mesh 名含 `Arch` / `Portal`）預設產生兩柱＋橫樑的 `GB_`。Live Edit 偵測到美術移動 / 新增 / 刪除後會自動重產 `GB_`。樹（`view_mode.TREE`，目前 `SM_CampTree`）的 `GB_` 是樹幹 2 段＋樹冠 2 段，不是整顆包成大方塊；單一 actor 不要灰盒就加 tag `NoGreybox`（Level 2 的 `SM_CampTree2`）。`GB_` 在兩個方向都伸進可拖曳方塊（tag `Editable`）超過 40 cm 時會被移除（`_clear_blocks`），方塊周圍的佈景不會在灰盒裡把它蓋住。Maze 物件加 tag `KeepMat` 時，Rebuild 不會把它的材質改回預設（Level 2 的 `Maze_Pit_r2_c4` / `Maze_Pit_r2_c10` 坑底用 `MI_StorybookSoil` 泥土）。可拖曳方塊上的美術（例如 `ArtCrate_`）要設 Movable 並 attach 到方塊上才會跟著移動。遊戲中 `BP_PathfindingPlayerController.SetViewMode`：`EnterPlanning` 灰盒、`StartRun` 最終畫面。
- **Storybook 外皮**（`storybook_skin.py`，`Editor_Grid` 有 tag `StorybookSkin` 的關卡，目前是 `Lvl_Level1`）：每個 `Maze_Path/Wall` 複製一份最終材質的分身（走道 `MI_PavingD`、牆 `MI_GrassTopSoilSides`；樓梯不做分身，一律用 `SM_PinkStone01` 樓梯模型，避免重疊，資料夾 `Camp_ArtSkin`，tag `VisFinal`+`NoGreybox`），原本的 Maze 方塊加 `VisGrey`+`Skinned`。每次 Rebuild 後自動重產。從 `/Game/Dev/Lvl_StorybookPreview` 複製來的包邊物件在 `Camp_ArtPreview/Storybook`（tag `NoGreybox`，不產生灰盒）。
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

## Gizmo 提示圖標（Fake Widget）

- **做什麼**：編輯階段（Phase 0）滑鼠懸停時，在可操作的東西上顯示 3D 編輯器手柄風格的圖標，永遠畫在場景最上層、不擋點擊。
  - 方塊（tag `Editable`）→ 移動（平躺在頂面；拖曳時跟著方塊）
  - 旋轉橋 / 單向門（`BP_Mechanism` Kind 1 / 2）→ 旋轉（平躺；門放在鉸鍊）
  - 升降梯（Kind 0）→ 升降（直立在平台上方；`bCurUp` 時翻轉，亮的箭頭指向下一步要去的方向）
  - 終點（角色的 `FinalTarget`，沒有就用 `TargetPoint`）→ 出口（滑鼠在終點 300 cm 內才顯示）
- **程式**：全部在 `/Game/Project/Programming/Blueprints/Pathfinding/BP_GizmoDirector`（複製自組員的 `/Game/Dev/Blueprints/BP_GizmoDirector`，Dev 原版不動；每幀讀 `BP_PathfindingPlayerController` 的 `Phase` / `bDragging` / `Selected` 與游標下的物件，自己生成、擺放圖標）。技術藍圖只改了一處：`BP_PathfindingPlayerController.ReceiveBeginPlay` 最後 spawn 這個 director。拿掉那一行就整個關掉。
- **大小 / 朝向**：`IconScale`（BeginPlay 設 8，出口 ×1.6）。直立圖標（升降、出口）朝 `FaceDir`＝每幀依玩家目前鏡頭（`GetPlayerCameraManager.GetCameraRotation`）的水平反方向重算，旋轉 / 平移視角時會跟著轉向鏡頭；平躺的移動 / 旋轉圖標不受影響。
- **選取高亮（正式版，Shipping 也有）**：控制器原本用 `DrawDebugBox` 畫懸停 / 選中 / 可放（綠）/ 不可放（紅），Shipping 會整個拿掉。`BP_GizmoDirector` 另外用真模型畫：`PlaceShell` 把方塊的 mesh 複製成放大 4 % 的外殼套上高亮材質（`HoverShell` 懸停淡青、`SelShell` 選中琥珀 / 拖曳時綠或紅），拖曳時 `DropBox`（方塊）擺在 `ComputeDrop` 的落點。材質 `/Game/Dev/Materials/Highlight/`（`M_EditHighlight` 半透明 unlit、運動模糊後渲染，`MI_Highlight_Hover/Selected/Valid/Invalid` 只差 `Color`；`Fill` / `Edge` / `Glow` 調濃淡），重建：`Tools/Highlight/build_highlight.py`。Overlay Material 在這些方塊上不會顯示，所以用外殼。控制器的 debug 繪製保留（開發時照樣看得到）。
- **美術**：模型 `/Game/Dev/Meshes/UI/SM_Gizmo*`（材質槽 `IceFace` / `LilacSide` / `LilacDim`）。材質 `/Game/Dev/Materials/Gizmo/`：
  - `M_Gizmo`：Translucent + Unlit + **Disable Depth Test**（畫在最上層）+ Translucency Pass **After Motion Blur**（避開水彩後處理，不會被洗淡）。`MI_Gizmo_Face` / `Edge` / `Dim` 是正面 / 側面 / 升降的暗箭頭。
  - Custom Primitive Data 第 0 位 `Dim`：0 = 亮、1 = 暗。
  - `M_Gizmo_Scene` + `MI_Gizmo_*_Scene`：同樣但會被場景遮擋（給貼地圖標用；目前沒用到，落點 `SM_GizmoDrop`、存檔 `SM_GizmoCheckpoint` 試過後先拿掉）。改顏色要兩套一起改。
- **限制**：畫在後處理之後，所以沒有 bloom 光暈、邊緣沒有抗鋸齒。

## 小狐外觀進度（專案副本 `/Game/Project/Programming/Blueprints/Pathfinding/BP_FoxLook`，複製自組員的 `/Game/Dev/Blueprints/BP_FoxLook`）
- **本專案的改法**：Level 0 開場（有 `IntroSpot`）時是原本的彩色小狐，開場動畫結束、進灰盒時才變成 0（`bWaitIntro`：看到控制器 `bInIntro` 變回 false）；之後是 0（灰模走路時有程序性晃動：上下彈跳＋搖擺，幅度依速度），走到塔（`SM_StoneMonument`，yaw 0，正面朝路）前的 TargetPoint `MonumentStand`（tag `LookStand`）時面向塔、觸發演出 → 1；Level 1 開場 1，走到出口旁的石碑（`SM_MossStone2`，網格名含 Monument）觸發演出 → 2（原貼圖）；Level 2 開場就是 2，checkpoint 不再觸發。離站位點或出口 9 m 內插入繞路，但只限「這一趟真的走到出口」（角色 `RunDestination` 就是出口、且和出口同高）：BLOCKED 時走向 RouteStep 不受影響（Level 1 上層走道就在出口上方 3.5 m，曾因此被拉去終點）。`BP_PathfindingGameMode` spawn 的是這份副本。以下是組員原版的說明：
- 由 `BP_PathfindingGameMode` BeginPlay 生成，不改小狐 / 控制器藍圖。Stage：0 灰模（無動畫）→ 1 白模（有動畫）→ 2 原貼圖。
- Level0 = 0；Level1 = 0，石碑（網格名含 "Monument"）→ 1：運行中小狐離出口（`NextLevel`）9 m 內時，把小狐 `Hops` 剩下的路線換成「NavMesh 走到石碑朝出口側 2.5 m 的站位點 → 直接走到路線終點」，到站位點觸發演出（算不出路時退回：離出口 5 m 內觸發；RESET 回起點會重新啟用）；Level2 = 1（`?Stage2` 為 2），走到 `StageGoal`（Checkpoint_Shrine）→ 2；其他地圖 = 2。
- 灰模：真網格隱藏，`StatueMesh`（PoseableMesh）掛在網格上，開局 0.2 s 複製待機姿勢後定格（角色 Tick 每幀重播動畫，關 Tick 壓不住）。材質 `/Game/Dev/Materials/FoxLook/M_FoxClay`、`M_FoxWhite`。
- 觸發時「資產修復」演出：小狐停下、轉向觸發物，追擊者 CustomTimeDilation 0；`WBP_Dialogue` 逐句顯示（系統行綠字、小狐白字），含 "Reloading" 的系統行帶進度條，期間新舊外觀閃爍，結束時定為新外觀並閃暖光；播完若原本在走且 Phase == 1 則繼續走。
- 台詞：觸發物上的 `Say:<文字>` tag 覆蓋預設，`Say:SYS:<文字>` 為系統行；沒有 tag 時用藍圖內英文預設。

## 漫畫 Glitch（`/Game/Dev/Materials/Glitch/`，重建：`Tools/Glitch/build_glitch.py` 的 `build()`）
- 全屏撕裂 `M_PP_ComicGlitch`：短脈衝用，強度 = max(MI `GlitchAmount`, `MPC_Glitch.Amount`)。
- 物件撕裂（A）`M_PP_ComicGlitchObject`：只作用在 Render CustomDepth + stencil 128–255 的網格（強度 = (stencil−128)/127，只在它是可見表面時）。需要 `r.CustomDepth=3`（DefaultEngine.ini）；Gouache B 的背景遮罩已改成 stencil > 0 不算背景（`Maze_Backdrop` 保持 stencil 0）。
- 整只重新載入閃爍（B）`MF_ComicGlitch`（在 `M_Master_ComicGlitch`）：舊外觀 = `ReloadFromColor` × 底色亮度；`OldLook` = Custom Primitive Data 1（逐物件）；`Reload` = min(MI, `MPC_Glitch.Reload`) 做整場景載入。
- `BPC_AssetReload`（`/Game/Dev/Blueprints`）掛到 actor 上、呼叫 `PlayReload`：A、B 交替（先撕裂再換外觀，越往後撕裂越短越少），首次使用時生成一個帶物件撕裂 blendable 的 unbound PPV。`L_Assets` 的 `SM_GlitchPreview_Animated` 掛著自動循環的預覽。

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
14. **只走格線（`BP_PathfindingCharacter.SquareHops`）**：`StartRun` 算完 `Hops` 後，相鄰兩點若 X、Y 都差 40 cm 以上且同高，就補 L 形轉角（先 X 後 Y，走不通再先 Y；兩段都要 `NavigationRaycast` 不擋；例外：下一段是沿 X 繼續走時改成先 Y，讓最後一段和下一段接成直線、少轉一次彎，Level 0 全通時才會提早對齊橋那一排、不擦過斷崖口旁的山壁），不會斜切過台階、拱門。`BP_FoxLook` 的繞路也會呼叫它，並用 `AddSnapped` 把轉角對齊格子中心；站位點（`LookStand`）若本來就在路線上就不繞路（Level 1 的 `MonumentStand` 在 (350, 525)）。
15. **走進傳送門**（`BP_PathfindingPlayerController.EnterPortal`）：抵達有下一關或結束動畫的終點時，角色沿面向再走 3 m（穿過傳送門）、在前方 1.5 m 播 `NS_PortalMotes`，0.5 s 後鏡頭 1.2 s 淡出成暖白色，再切關或播結束動畫；走進傳送門期間（`bInPortal`）不挖空。
16. **全螢幕 Glitch / 石碑 Glitch**：`StartScreenGlitch(Strength, Dur)` 第一次呼叫時生成 unbound PPV 掛 `M_PP_ComicGlitch`（tag `ComicGlitchScreenPPV`），`UpdateGlitch`（Tick）把 `MPC_Glitch.Amount` 以每秒 5 下的脈衝推到 Strength，前 30% 滿強度、Dur 內淡出（較弱的呼叫不會蓋掉正在播的較強的）。轉場：每次進灰盒（`EnterPlanning`，含開關卡、開場後、RESET / BLOCKED / 被抓後）1.0 / 1.4 s；被抓（`OnCaught`，最終畫面）1.6 / 1.6 s；走進傳送門 0.5 s 後 1.3 / 1.6 s。環境 Glitch（Phase 0/1 隨機出現，`AmbientLevel` 由 `SetAmbientGlitch` 在 BeginPlay 依地圖設定）：Level 0 = 0 沒有；Level 1 = 1 每 14–22 s 一次 0.3 / 0.35 s；Level 2-1 = 2 每 7–12 s 0.5 / 0.5 s；Level 2-2 = 3（`Stage2` 開啟參數或 `OnStageCleared`）每 3.5–7 s 0.7 / 0.7 s。小狐在石碑前變身時（`BP_FoxLook.StartFx`），石碑上的 `BPC_AssetReload` 元件（Level 0 / Level 1 的 `SM_StoneMonument` 已在關卡裡掛上）`PlayReload`；新石碑要自己掛這個元件（藍圖不能從外部 `AddComponentByClass`）。石碑材質用 `/Game/Project/Art/Materials/MI_StoneMonument_Glitch`（母材質 `M_Master_ComicGlitch`，參數照抄 `MI_StoneMonument`），才有「灰模 ↔ 原樣」閃爍；只用 `M_Master` 的物件只會撕裂。**傳送門撕裂**（`BP_PortalGlitch`，controller 的 `PortalGlitch(Pos, Dur)` 生成）：`Setup` 找 Pos 4.5 m 內網格名含 `Portal` / `Archway` 的最終美術，加上離它們 2.3 m 內的 `GreyProxy` 灰盒石柱（`GB_` 沒有來源 tag，用距離分辨，附近的牆不會被抓到），Tick 每秒 7 拍隨機開關 stencil 撕裂，Dur 後關閉並銷毀。觸發：第一次進灰盒、開場運鏡拉近 Point A 時（入口傳送門，3 s；Level 1 有，Level 0 / Level 2 起點沒有傳送門）；`EnterPortal`（出口傳送門，2.5 s）。**小狐被打倒**：`BP_PathfindingCharacter` 掛了 `BPC_AssetReload`（`FoxReload`），`OnCaught` 在 `KnockDown` 後 `PlayReload`（只有撕裂，小狐材質不是 `M_Master_ComicGlitch` 所以不會變灰模；Level 0 的灰模小狐是 FoxLook 的 `StatueMesh`，不在小狐身上，不會撕裂）。**被追擊者擋住 ≠ BLOCKED**：追擊者用身體擋住小狐時，小狐 0.6 s 沒前進會先判定 BLOCKED（Phase 2），之後真正的 `OnCaught`（只在 Phase 1 執行）就被跳過、沒有倒地和 Glitch；所以 `OnRunFinished` 的 BLOCKED 分支先檢查 2 m 內有沒有 `BP_EnemyChaser`，有就把 Phase 設回 1 再走 `OnCaught`（2 m：隔著柵欄 / 木箱牆等著的野獸約 4.4 m，照常 BLOCKED）。`OnCaught` 在 Phase 1 或 2 都會執行，但每輪只一次（`bCaught`，`StartRun` 重設；沒重設時第二輪起被抓完全不觸發、卡在 RUNNING）。追擊者的撞到距離 = 膠囊半徑 + 125 cm（約 170 cm；原本 + 60 太小，野獸模型很大，並排或斜著頂住時中心距離停在 105 cm 以上，撞不到也不算卡住）。**物件撕裂需要 `r.CustomDepth=3`**（`DefaultEngine.ini` 已設，但 Editor 要重開才讀得到）：如果還是 1，stencil 不會寫入，Gouache B 會把開了 CustomDepth 的物件當成背景，整塊塗成背景藍色（看起來像「藍色閃爍」）。
17. **Glitch 觸發點**（`BP_GlitchSpot`，資料夾 `Gimmicks`）：PLAY 中（Phase 1）小狐每次進到它 `Radius` 內（高度差 2.5 m 內），`Target` 美術就撕裂 `GlitchDur` 秒（`ScreenAmt` > 0 時同時播一次全螢幕 Glitch）（`BP_PortalGlitch.SetupActor`：Target 的所有元件＋3 m 內的 `GreyProxy`）。actor 帶 `Say:<文字>` tag 時，該關**第一次**經過會讓小狐停下、轉向 Target、用 `WBP_Dialogue` 每句 2.4 s 顯示（追擊者暫停），講完繼續走；之後經過只撕裂。`bTalked` 只在台詞全部播完（`EndTalk` 時 `LineIdx` ≥ 句數）才設為 true；講到一半被抓、RESET、BLOCKED（Phase 離開 1）會中止且不算，之後的 run 走到這裡仍會再講一次。BeginPlay 會清空 bTalked / bTalking / bInside、Radius ≤ 0 時用 650；Output Log 會印 `GlitchSpot BeginPlay` / `talk START` / `talk END talked=` 方便追查。Level 1：`GlitchSpot_Camp`（放在帳篷那段走道轉上樓梯的轉角 (1400, -875)，半徑 3 m，Target 是帳篷 `SM_TentCamp`，兩句台詞；原本放在帳篷中心半徑 6.5 m，小狐提早轉上樓梯時剛好在範圍外，偶爾不觸發）、`GlitchSpot_Arch`（出口前的拱門 `Art_ExitArch` (-970, 135)，半徑 9 m，觸發點 z 150，撕裂 4 s＋全螢幕 0.45，無台詞、不停）。
18. **對話框逐字打字＋點擊**（`BP_DialogueDriver`，`BP_PathfindingGameMode.BeginPlay` 生成）：每幀處理畫面上所有 `WBP_Dialogue`（呼叫端照舊直接 `SetText` 整句即可）：每秒 45 字逐字打出，打完句尾閃爍 `▶▶`；在對話框範圍（畫面下方 260 px、左右 10–90%）按左鍵：還在打字＝立刻顯示整句，已打完＝設 `WBP_Dialogue.bAdvance`，呼叫端（`BP_GlitchSpot` Tick、`BP_FoxLook` Tick、控制器 `UpdateHint`）看到就切下一句並清掉旗標；不點則照原本計時自動換句（GlitchSpot 3 s、提示 2.8 s、FoxLook 各句 LineDur）。新句判定：前 14 字不同才重新打字（同一句每幀重設或只有句尾進度條變動會繼續打）。WBP_Dialogue 新變數 `Full` / `Shown` / `Chars` / `bAdvance` / `bSystem`。**外觀**（Storybook Dialogue A，貼圖 `/Game/Project/Art/UI/Dialogue/T_UI_Dialogue_A_*`；C 版貼圖也已匯入備用）：`Box` 底圖 = A_Body，`NameBox`（Overlay，固定 334×120＝名牌原圖比例，不拉伸變形）裡疊 `NamePlate`（綠色名牌，Draw As Image）+ `ScaleBox_0`（Scale To Fit、只縮小）包 `NameText`（置中；太長的名字自動縮小字級塞進名牌），左緣對齊對話文字、跨在對話框上緣（anchor 0.12, pos (50, -196)），`ContinueImg`（棕色 V 箭頭）在右下，句子打完才閃爍顯示。名牌由 Driver 決定：`bSystem`（FoxLook 的 `SYS:` 台詞）→ `SYSTEM`，並換成**系統對話框外觀 System Log 07**（`T_UI_SystemLog_07_Body/Nameplate/Continue`：白底藍邊、黃色斜名牌、深色 V 箭頭、文字深藍；04 深藍版也已匯入備用）：Driver 的 `SkinSys` / `SkinFox` 在 `bSystem` 和 `WBP_Dialogue.bSkinSys` 不同時換底圖、Padding、Box 高度（系統 165 / 小狐 250）、名牌大小位置與顏色，貼圖存在 Driver 的 `TexFox*` / `TexSys*` 變數；其他＝小狐，依 `BP_FoxLook.Stage`：0 灰模 `BP_GreyFox`、1 白模 `SK_Fox_WIP`、2 彩色 `Fox`（只是「看起來還在編輯中」的假檔名）。文字色由 Driver 每幀設定（小狐深棕、系統深綠），呼叫端不要再設顏色。
19. **進灰盒時的小狐獨白**（`BP_IntroTalk`，Level 0 的 `IntroTalk_Greybox`，資料夾 `Gimmicks`）：開場動畫結束、第一次進灰盒（Phase 0、控制器 `bInIntro` 變回 false）後等 1.6 s（讓轉場 Glitch 過去），用 `WBP_Dialogue` 依序播它的 `Say:` tag（每句 3.2 s，或點對話框跳句），整關只播一次；按 PLAY 就結束。改台詞＝改這個 actor 的 tag。
13. **走在路中間**：角色不再用 `AIMoveTo` 一段段走（每段結束會停一下），改在 `Tick` 用 `AddMovementInput` 沿 `Hops` 連續前進（轉角 70 cm 內換下一點、最後一點 40 cm），0.6 s 沒前進＝路斷了 → BLOCKED；`can_walk_off_ledges` 關閉，不會走進坑裡。`BP_PathfindingCharacter.StartRun` 把 NavMesh 路徑的每個轉角用 `SnapCell` 移到所在 350 cm 格子的正中央（只在平地：格子中心的 NavMesh 高度和原點不同＝在樓梯上，就只對齊橫越樓梯的那一軸，並在後面補上 NavMesh 原本的轉角＝樓梯腳，免得在樓梯半途轉彎走下樓梯側邊）（格子原點 = tag `EditorGrid` 的 `Editor_Grid`，`get_grid()` 會自動加 tag；沒有就不對齊）。
12. **導航半徑 AgentRadius = 120**（`DefaultEngine.ini` 與各關卡的 `RecastNavMesh-Default`）：讓角色走在路中間、不貼著牆和模型邊緣。舊關卡的 RecastNavMesh 仍是 35，要改那個 actor 的 agent_radius 再 BUILDPATHS。
15b. **PIE 中不要用 `execute_python` 改遊戲物件**（`call_method`、`teleport`、`set_editor_property` 等）：Python 執行會包成 Undo transaction，把 PIE 物件記進 TransBuffer，StopPIE 時 `PlayLevel.cpp:558` 斷言「Object from PIE level still referenced」→ Editor 閃退。PIE 中只做唯讀查詢；要觸發遊戲事件改用主控台 `ke <actor 名> <事件>`（例：`ke BP_PathfindingPlayerController_C_0 StartRun`，不經 Undo）；DSL Write 只編譯不存檔，改完藍圖要馬上 `save_asset`，否則閃退就沒了。
15c. **骨架網格的材質要勾 `Used with Skeletal Mesh`**：沒勾時 Editor 只會在記憶體裡自動補勾（不存檔），所以自己電腦有時正常，隊友拉下來或打包後就變回預設灰格材質（「材質跑掉」）。`M_RockEnemy`（Level 1/2 的石頭野獸）就是這樣，已勾選並存檔。新匯入角色時記得檢查。
11. **角色不走 / 路徑是 0 個點**：通常是關卡裡的 `RecastNavMesh-Default` 壞掉（log 出現 `Unable to find RecastNavMesh instance`）。修法：刪掉該 actor → 稍微移動 `NavMeshBoundsVolume` → 執行 `BUILDPATHS`（有時要做兩次）→ 存檔。改動地形或 NavMesh 範圍後都要重建。

## 音效（`BP_SoundDirector`，`BP_PathfindingGameMode.BeginPlay` 生成，所有關卡）

- 素材在 `/Game/Project/Audio`，目前全是程式合成的 placeholder（`Tools/Audio/gen_sfx.py <輸出資料夾>` 產生 WAV 再匯入）。**換正式音效＝匯入同名資產覆蓋**，藍圖不用改。3D 音效用 `ATT_World`（4500 cm 內全音量、再 7000 cm 衰減完；鏡頭離地圖很遠，所以範圍大）；敵人腳步用 `ATT_Near`（900 / 2600），而且音量再乘上「牠和小狐的距離」（5 m 內全音量、30 m 外無聲），因為聽者是鏡頭、不是小狐。合成器 `gen_sfx.py <dir> v2` 產生第二版（輕巧的小狐腳步、4 種柔和 Glitch、嗡＋咔的旋轉橋 / 門、拿起方塊、傳送聲）。
- Director 每幀看遊戲狀態播放（不改其他藍圖）：
  - `Misc`：控制器 `bInIntro` 變 false 後開始 `BGM_Storybook_Loop`（0.32）＋ `AMB_Wilds_Loop`（0.55）各一次（元件存在 `BgmComp` / `AmbComp`）；灰盒（Phase 0）時兩者「悶住」：低通濾波 650 Hz、音量 ×0.7，最終畫面時恢復（`Muffle` 0↔1，約 0.5 s 平滑過渡，截止頻率 = 650 × 28^(1−Muffle)）；`bDragging` 變 true → `SFX_BoxPick`、變 false → `SFX_BoxDrop`（2D）；控制器 `bInPortal` 變 true（走進傳送門，三個傳送門都是）→ `SFX_Portal`。
  - `Fox`：小狐速度 > 60 時每走 90 cm 一步（音量 0.32、音高 1.05–1.25）`SFX_FoxStep_01–04`（`gen_sfx.py <dir> v3`：濾波噪音的輕拍聲，沒有音高；在腳邊）；`AnimState` 變 3（被打倒）→ `SFX_Hit` ＋ 隨機 Glitch（在小狐身上）；`BP_FoxLook.Stage` 改變 → `SFX_Shimmer`、`bFx` 開始 → 隨機 Glitch。
  - `Enemy`：每隻 `BP_EnemyChaser` 每移動 210 cm → `SFX_EnemyStep_01–03`（在牠身上）。
  - `Mech`：`BP_Mechanism` Kind 0 升降梯 `bCurUp` 改變 → `SFX_Lift`；Kind 1 旋轉橋 `TargetYaw` 改變 → `SFX_BridgeRotate`；Kind 2 單向門 → `SFX_Gate`。
  - `Glitch`：`MPC_Glitch.Amount` 往上越過 0.15（冷卻 0.9 s）→ 2D 隨機一個 `SFX_Glitch_01–04`（Director 的 `Glitches` 陣列；越強越大聲，走進傳送門期間只有 30%）；每個新的 `BP_PortalGlitch`（傳送門、GlitchSpot）→ 隨機 Glitch 在它第一個撕裂的物件上。
- 對話換句音效在 `BP_DialogueDriver.DriveOne`（偵測到新句時）：系統 `SFX_DlgSystem`、小狐 `SFX_DlgFox`。

## HUD（Creator Access 卡片，`WBP_PathfindingHUD`）

- 設計稿 Creator_HUD_A（貼圖在 `/Game/Project/Art/UI/CreatorHUD/`：`T_UI_Creator_Card` 底板、`Header` 標題條、`ButtonMask` 按鈕共用遮罩、`PlayGlyph` / `ResetGlyph`）。所有關卡共用同一個 HUD，所以 Level 0 / 1 / 2 都會換上。
- 結構：`Root` → `CreatorCard`（CanvasPanel，原圖像素座標排版，render scale 0.7，位置 (28, 30)）→ `CardBg`、`HeaderBg`、`CreatorTitle`「CREATOR ACCESS」、`GoalText`（目標文字，預設 "Make a way across."，會換行）、`PlayButton` / `ResetButton`（遮罩染色：可按 #EDFC35、停用 #7D8599，圖示與文字深藍 #1B2550）。
- 舊的資訊面板 `Panel`（Phase / Path / Tool / Selected / 說明文字）保留但 Collapsed，控制器仍會寫它的文字，要除錯時把 `Panel` 設回 Visible 即可。按鈕仍是原本的 `PlayButton` / `ResetButton`（控制器用 `SetIsEnabled` 切換）。

## 選單 / 設定（`/Game/Project/Programming/Blueprints/Menu/`）

- `BP_PuzzleGameInstance`：MasterVolume / MusicVolume / SfxVolume / Language（0 英文、1 繁中、2 簡中，語言按鈕循環切換），`LoadSettings`、`SaveSettings`（slot `PuzzleSettings`）、`ApplyAudio`。
- `BP_MenuPlayerController`：建立 `WBP_MainMenu`、綁定按鈕、`ShowPanel`、`UpdateTexts`（中英文字串都在這裡）。新增關卡要加按鈕 `BtnLvlN` 與事件 `OnLvlN`。
- **外觀（Project Archived 設計稿）**：背景 `Bg` = `/Game/Project/Art/UI/Menu/T_Menu_Background`（2560×1440，在 Level 0 PIE 開場小狐站在佈告欄前時用 SceneCapture 拍的：相機 (-1840, -430, 345)、pitch -13、yaw 11、FOV 74）；左上 `ProjectPill`（綠色圓角「Project」）＋ `TitleCard`（米色圓角卡片、`TitleText`「Archived」，`UpdateTexts` 固定寫 Archived，副標 `SubtitleText` 隱藏）；三個面板各包在米色圓角卡片 `MenuCard` / `LevelCard` / `SettingsCard`（Border，RoundedBox brush），`ShowPanel` 切換的是卡片（裡面的 `MainPanel` / `LevelPanel` / `SettingsPanel` 一律 Visible）；按鈕平常透明、滑過淺棕圓角底，文字深棕 30 Bold；音量 Slider 棕色軌道、綠色把手。**Level Select**＝2×2 卡片格 `SceneGrid`（`SceneRow0`：`BtnLvl0` / `BtnLvl1`，`SceneRow1`：`BtnLvl2` / `BtnLvl3`），每顆按鈕是 `SceneContentN`（`ScenePreviewN` 256×144 最終畫面截圖，RoundedBox brush 圓角 14 + 3 px 棕色描邊；`TxtLvlN` 標題 14 Bold；卡片按鈕的滑過底是淺棕圓角，不用主選單那張帶綠點的選取框圖，拉伸會變形）；截圖 `/Game/Project/UI/MainMenu/T_Scene0–3`（原圖在 `Tools/MainMenu/Assets/Scene0–3.png`；Scene2 = 2-1、Scene3 = 2-2，在 Level 2 PIE 按 PLAY 後用 SceneCapture 拍：2-1 相機 (-900, -1300, 3300) pitch -40 yaw 48，2-2 相機 (-300, 2600, 3900) pitch -42 yaw 50，FOV 58）。`BtnLvl4–6` Collapsed。選單素材（標題、紙張、選取框）在 `/Game/Project/UI/MainMenu/`。
- 主選單：Continue（有進度才顯示）/ New Game（→ Level 0）/ Level Select / Settings / Quit。關卡選擇只有 4 個：`BtnLvl0` Level 0（`Lvl_Level0`）、`BtnLvl1` Level 1（`Lvl_Level1`）、`BtnLvl2` Level 2-1（`Lvl_Level2`）、`BtnLvl3` Level 2-2（`Lvl_Level2` + 開啟參數 `Stage2`）；`BtnLvl4–6` 隱藏。
- 進度：`BP_PuzzleGameInstance.SaveProgress(Map, Options)` 存在設定存檔（`LastLevel` / `LastOptions`，slot `PuzzleSettings`）；`BP_PathfindingPlayerController` 每次進關卡時存一次，過了 Level 2 的 checkpoint（`OnStageCleared`）存成 `Stage2`。Continue = `OpenLevel(LastLevel, LastOptions)`。
- `Stage2` 開啟參數：`BP_PathfindingPlayerController.SkipToStage2` 讓角色從 `StageGoal`（checkpoint）出發、目標換成 Point B、鏡頭用 `StageCam`。
- `BP_PathfindingPlayerController` BeginPlay 會套用音量；`Esc` 回主選單。
- 操作：編輯時左鍵拖方塊、在空白處拖曳＝平移畫面（`StartLeftPan`）；滾輪縮放；右鍵左右拖＝繞畫面中心左右旋轉（`bOrbiting`，用 `GetInputMouseDelta`，俯角固定；右鍵按住時游標被 capture，`GetMousePosition` 不會變）；中鍵/方向鍵平移。PLAY 中沒有視角旋轉。
- 角色 `FollowCameraArm`：第三人稱（長 1000、俯角 30°，看得到後面追來的敵人、有延遲平滑）。
- 坑：**DSL Write 之後不要再呼叫 `compile_blueprint`**（會重複編譯而閃退）；修改 BP 的 class defaults（例如 GameMode 的 PlayerControllerClass）後要 `compile_blueprint` 再存檔，PIE 才會生效。

## 協作規則

- `.uasset` / `.umap` 是二進位檔（Git LFS），**無法合併**。同一個檔案同一時間只能一個人改。
- 專案已改名：GitHub repo `gsn943314/Project_Archived`（舊網址會自動轉址，建議 `git remote set-url origin https://github.com/gsn943314/Project_Archived.git`），專案檔 `Project_Archived.uproject`（pull 之後改開這個檔；舊的 `mcptest.uproject` 已不存在）。本機資料夾名稱不影響，可以不改。
- 開工前先 `git pull`；動到共用藍圖（上表那些）前先在群組說一聲。
- 新關卡請複製一張現有地圖改名（例如 `Lvl_<名字>_xxx`），在自己的地圖上做實驗。
- 開發紀錄：中文原稿寫在 `devlog/`（只留本機，已 gitignore）；GitHub 上公開的是英文版 `devlog/en/`（新增中文 devlog 後要同步翻成英文放進去並更新 `devlog/en/README.md`）。線上圖文版 devlog（case study）在作品集網站 https://davidkuo.tech/projects/project_archived ，原始碼在 `~/Documents/Projects/Active/david-portfolio-website/3d-glass-portfolio`（`app/projects/project_archived/page.tsx`、`data/project-archive.json`）；提到「線上 devlog」指的就是它。
