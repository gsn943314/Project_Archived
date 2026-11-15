# Epic MegaJam · 漫画 Glitch 特效使用说明

漫画风格的"系统出错 / 资产重新加载"效果，分三种用法。资产都在 `/Game/Dev/Materials/Glitch/` 和 `/Game/Dev/Blueprints/`。

| 想要的效果 | 用什么 |
|---|---|
| 某个物体"重新加载"：撕裂和灰模闪烁交替，最后定格 | `BPC_AssetReload` 组件 |
| 整个场景一起从灰模加载回来 | `MPC_Glitch` 的 `Reload` |
| 全屏撕裂一下 | `M_PP_ComicGlitch` 加上 `MPC_Glitch` 的 `Amount` |

## 预览

打开 `/Game/Dev/L_Assets`，在 Outliner 里双击 `SM_GlitchPreview_Animated`，镜头会飞到这块石头。点一下视口空白处取消选中，按 `Alt+S` 进入 Simulate。石头会自动循环播放重新加载效果，按 `Esc` 停止。编辑器窗口要在前台，否则视口不刷新。

| 旧外观（未加载的灰模） | 撕裂时 | 开场满强度撕裂 |
|---|---|---|
| ![](glitch/reload_old.jpg) | ![](glitch/reload_tear.jpg) | ![](glitch/reload_start.jpg) |

## 1. 单个物体重新加载：`BPC_AssetReload`

### 准备

- 物体的材质要用 **`M_Master_ComicGlitch` 的材质实例**，才会变成灰模并闪烁。可以复制 `MI_ComicGlitch_StoneCliff03_Preview`，换上自己的贴图，参数和石头母材质一样（`BaseColorMap`、`StoneColorMask` 等）。
- 用其他材质的物体也能挂这个组件，但只会撕裂，不会变灰模。

### 挂组件

- 关卡里摆好的物体：选中，在 Details 面板点 **Add**，搜 `BPC_AssetReload`。
- 蓝图 actor：在 Components 面板里加 `BPC_AssetReload`。

### 触发

- 在任何蓝图里拿到这个组件，调用 **`PlayReload`**。例如剧情事件、触发盒的 Overlap、关卡蓝图。
- 想进关卡就播放：勾选 **`bAutoPlay`**。
- 每个关卡第一次播放时，组件会自动生成需要的后处理体积，不用手动放。

### 参数（在组件的 Details 面板里调）

| 参数 | 默认 | 作用 |
|---|---|---|
| `Duration` | 2 | 整段长度（秒） |
| `Rate` | 7 | 每秒几拍，越大闪得越快 |
| `bAutoPlay` | 关 | 开始游戏就播放 |
| `LoopInterval` | 0 | 大于 0 时播完等这么多秒再重播，只建议预览时用 |

### 节奏

1. 0–0.3 秒：灰模加撕裂，表示"出错了"。
2. 中段：每一拍先短暂撕裂一下，再干净地切换外观。越往后原样出现得越多，撕裂越短、越少、越弱。
3. 结尾：定格成原样，最后撕裂一下，约 0.2 秒内淡出。

## 2. 整个场景重新加载：`MPC_Glitch.Reload`

场景里所有用 `M_Master_ComicGlitch` 的物体都读 `MPC_Glitch` 的 `Reload`：

- `0`：全部是灰模；
- `1`：全部是原样（默认）；
- 中间值：每个物体按各自的节拍闪烁，原样出现的比例随数值增加。

蓝图里用 **Set Scalar Parameter Value**（Collection 选 `MPC_Glitch`，Parameter Name 填 `Reload`），搭配 Timeline 从 0 推到 1。

## 3. 全屏撕裂：`M_PP_ComicGlitch`

![](glitch/screen_pulse.jpg)

### 准备

在关卡的后处理体积里加上它：选中后处理体积，在 Details 面板找到 **Rendering Features → Post Process Materials**，加一个元素，选 `M_PP_ComicGlitch`。也可以选它的材质实例，但要确认实例里 `GlitchAmount = 0`、`PreviewLoop = 0`。

### 触发

用 **Set Scalar Parameter Value** 设 `MPC_Glitch` 的 **`Amount`**，用 Timeline 让它瞬间冲到 1，约 0.3–0.6 秒内降回 0。平时保持 0，画面就是干净的。

### 材质参数

| 参数 | 作用 |
|---|---|
| `TearWidth` | 条带宽度 |
| `ColorSplit` | RGB 分色距离 |
| `ScreenShift` | 错位距离 |
| `GlitchStepsPerSecond` | 每秒跳几次 |
| `InkCyan` / `InkMagenta` / `InkYellow` | 油墨颜色 |

## 注意事项

- **`MPC_Glitch` 的默认值请保持 `Amount = 0`、`Reload = 1`**，否则所有关卡一进去就是故障或灰模状态。只在运行时用蓝图改。
- **Custom Stencil 128–255 留给物体撕裂用。** 其他效果要用 Stencil 的话，请用 1–127。
- **开了 Render CustomDepth、Stencil 为 0 的物体会被 Gouache 后处理当成背景涂掉**，例如 `Maze_Backdrop`。物体撕裂会自动使用 128 以上的值，不受影响。
- 项目设置需要 `r.CustomDepth=3`（Custom Depth-Stencil 开启），已经写在 `Config/DefaultEngine.ini`。
- **不要在材质编辑器里手动改这几个材质的节点**：`MF_ComicGlitch`、`M_Master_ComicGlitch` 里的 glitch 部分、`M_PP_ComicGlitch`、`M_PP_ComicGlitchObject`。它们由 `Tools/Glitch/build_glitch.py` 生成，重建会覆盖手动修改。要改效果，请改 `Tools/Glitch/` 里的 HLSL 再重建。材质实例的参数可以随便调。
- 目前只有 `M_Master_ComicGlitch` 支持灰模闪烁，正式的石头母材质 `M_Master` 还没接入。

## 相关资产

| 资产 | 用途 |
|---|---|
| `/Game/Dev/Blueprints/BPC_AssetReload` | 重新加载组件，交替驱动撕裂和闪烁 |
| `/Game/Dev/Materials/Glitch/MPC_Glitch` | 全局控制：`Amount`（全屏撕裂）、`Reload`（整场景加载） |
| `/Game/Dev/Materials/Glitch/M_Master_ComicGlitch` | 支持灰模闪烁的物体母材质 |
| `/Game/Dev/Materials/Glitch/MF_ComicGlitch` | 灰模闪烁的材质函数 |
| `/Game/Dev/Materials/Glitch/M_PP_ComicGlitch` | 全屏撕裂后处理 |
| `/Game/Dev/Materials/Glitch/M_PP_ComicGlitchObject` | 只作用在标记物体上的撕裂后处理（组件自动使用） |
| `Tools/Glitch/` | 构建脚本和 HLSL 源码 |
