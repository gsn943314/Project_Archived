# Epic MegaJam · 网页版（Wasm）构建说明

只在 `feature/web` 分支上。Windows 版仍从 `main` 打包，网页版是额外尝试。用的是 UE 5.9 MegaJam Preview 自带的实验性 Web 平台（WebAssembly + WebGPU，移动端渲染器）。

## 这个分支和 main 的差别

| 改动 | 原因 |
|---|---|
| `Source/`（`mcptest` 模块 + `UWebBuildMarker`）、`.uproject` 的 `Modules` | Web 平台只能构建 C++ 项目。项目从此是"代码项目"，**打开它需要能编译 C++（Visual Studio 2022 + C++ 游戏开发组件）**。游戏逻辑仍全部是蓝图。 |
| `.uproject` 里 `AllToolsets`、`Terminal`、`OnlineSubsystemUtils`、`OnlineSubsystemNull` 加了 `"PlatformDenyList": ["Wasm"]` | 编辑器 AI 工具集会让 Wasm 烘焙崩溃；在线子系统在浏览器里不能运行。 |
| `Config/DefaultEngine.ini` 的 `[/Script/WasmTargetPlatform.WasmTargetSettings]` | 网页标题、点击开始。 |
| `Tools/StorybookPP/PP_Gouache_A.hlsl`、`PP_Gouache_B.hlsl`、`Tools/Glitch/*.hlsl` | 移动渲染路径没有 `SceneTextureLookup(UV, Index, bFiltered)`，改成按渲染路径切换的宏（移动用 `MobileSceneTextureLookup`）。**桌面端走的还是原来的调用，Windows 画面不变。** |
| `Source/mcptest/mcptest.cpp` | Web 的移动前向档没有 GBuffer，Gouache 编译不过、会被默认材质盖满屏幕，所以这一档启动时关掉后处理材质（`r.PostProcessing.DisableMaterials 1`）。延迟档照常有 Gouache。 |

## 两个渲染档

| 档位 | 谁会用到 | 画面 |
|---|---|---|
| 移动延迟（deferred） | 页面判断为桌面级显卡 | 有 Gouache、阴影 |
| 移动前向（forward） | 集成显卡、手机、较弱的显卡 | **没有 Gouache**（原始场景），其他正常 |

两档都没有 Lumen、Nanite、虚拟阴影贴图、光线追踪。测试时可以在网址后加 `?tier=forward` 或 `?tier=deferred` 强制选档。

## 环境（每台要打包的电脑一次）

1. 安装 emscripten **6.0.10**（只认这个版本）到例如 `D:\emsdk`：`git clone https://github.com/emscripten-core/emsdk`，然后 `emsdk install 6.0.10`、`emsdk activate 6.0.10`。
   - 解压时若被杀毒软件挡住（`WinError 5` 拒绝访问），手动解压 `downloads\...-wasm-binaries.zip` 的 `install` 文件夹到 `upstream`，再写 `upstream\.emsdk_version`。
2. **`upstream\emscripten\emscripten-version.txt` 要改成 `6.0.10`**（官方包写的是 `6.0.10-git`，UE 预览版读不了，会报 `Unable to convert ... version '6.0.10-git' to an integer`）。
3. 生成系统头文件：`python upstream\emscripten\embuilder.py build sysroot`（否则报 `'emscripten/emscripten.h' file not found`）。
4. 打包前设环境变量 `WASM_EMSDK_ROOT=D:\emsdk`。

## 打包

先编译一次编辑器目标（分支第一次打开时编辑器也会提示编译）：

```bat
"D:\Program Files\Epic Games\UE_5.9\Engine\Build\BatchFiles\Build.bat" mcptestEditor Win64 Development -Project=<路径>\mcptest.uproject
```

然后（编辑器关掉）：

```bat
set WASM_EMSDK_ROOT=D:\emsdk
"D:\Program Files\Epic Games\UE_5.9\Engine\Build\BatchFiles\RunUAT.bat" BuildCookRun -project=<路径>\mcptest.uproject -noP4 -platform=Wasm -clientconfig=Development -build -cook -stage -pak -iostore -package -archive -archivedirectory=<输出目录> -map=/Game/Project/Maps/Lvl_MainMenu+/Game/Project/Maps/Lvl_Level0_Davidtesting+/Game/Project/Maps/Lvl_Level1+/Game/Project/Maps/Lvl_Level2 -unattended -utf8output -AdditionalCookerOptions="-unattended -nopause -nosplash -nullrhi"
```

第一次约 8 分钟（要把引擎编译成 WebAssembly），之后 2–3 分钟。正式发布用 `-clientconfig=Shipping`。

## 本地运行

```bat
"D:\Program Files\Epic Games\UE_5.9\Engine\Binaries\ThirdParty\Python3\Win64\python.exe" "D:\Program Files\Epic Games\UE_5.9\Engine\Platforms\Wasm\Build\Tools\web\serve.py" --root <输出目录>\Wasm --port 8900
```

用 Chrome 打开 `http://127.0.0.1:8900/index.html`。不能直接双击 `index.html`（需要服务器的跨源隔离头）。Development 版可以加 `?args=/Game/Project/Maps/Lvl_Level1` 直接进某一关。

## 发布

输出目录里的 `Wasm` 文件夹就是整个网站，放到支持自定义响应头的静态托管上（itch.io、Cloudflare Pages 等，需要 COOP/COEP 头）。引擎的部署计划工具：`Engine/Platforms/Wasm/Docs/Deploy.md`。

## 已知问题

- 浏览器内存超过约 2 GB 会崩溃（预览版已知问题）。
- 前向档没有 Gouache。
- 物体撕裂 Glitch 依赖 Custom Stencil，网页版上是否正常还没验证。
