# Chemanim

Chemanim 是我用来制作有机反应机理动画的个人工具。它现在直接保存原子、显式键型和二维坐标，不再依赖整张 ChemDraw PNG，也不会在编辑或播放时替我“纠正”结构。

工程只有一套共享 C++ Core：文档、稳定 ID、画布手势、撤销重做、线性节点、逐帧求值和描绘都在 Core 中。C++ 引擎直接链接它，PyQt6 编辑器通过 `chemanim_core.pyd` 调用它；Python 只负责界面与输入事件。

## 现在能做什么

- 从空白画布手画，或用 SMILES 生成一次性起稿。导入时 RDKit 会把芳香表示展平成明确的单、双键，保存后不再做芳香性、价态或 Kekulé 推断。
- 绘制单、双、三、实楔、虚楔和波浪键；双键副线方向是持久化的 `left/right/center` 视觉数据，不会因取代、拖动或播放而跳动。
- 使用 3–8 元环及“六元环加三根显式双键”的苯环模板；点击键生成稠环，点击原子生成螺环，拖动时可自由旋转整个模板。
- 框选、套索、直接拖动选区和连续橡皮擦；一整段手势只产生一次撤销记录。
- 用结构工具放置带圈的形式电荷 `⊕`、`⊖`。它们跟随锚定原子，也可单独移动、变色和做透明度动画。
- `.cmm` v5 保存稳定 atom/bond/adornment/node ID、单调不复用的 `creationSerial`、显式视觉键型和 ordered node sequence。
- 分子坐标由当前最早创建且仍存活的原子派生。分子移动、旋转和缩放围绕该锚点；锚点删除或转移不会让其余内容跳动。
- 线性节点是唯一创作层。Lerp 在当前帧启动，Wait 推进时间；同属性后发插值从接管帧的当前状态继续。typed tracks、预览和 Lua 都由 Core 从同一节点序列求值。
- 基础视觉事件包括选择淡入淡出、显式成键/断键、基团转移、分子合并和分子内成键；预览可以任意向前或向后拖动，不会破坏基础工程。
- 画布右键分子、原子、键或形式电荷即可建立对应 Set/Lerp 节点；绘制模式修改基础结构，脚本模式只修改节点目标。
- 明确区分 Artboard 与外部工作区；中键或 Space+左键平移，滚轮围绕鼠标缩放，最小倍率自动居中。最终预览和 MP4 只输出 Artboard 内部。
- 普通预览使用共享 Core SVG，“最终效果预览”和引擎都使用 NanoSVG 栅格化结果。

## Windows 启动

需要 Visual Studio 的“使用 C++ 的桌面开发”和 Python 3.14。首次准备会在仓库 `.deps` 中安装 RDKit C++ 开发包：

```powershell
.\tools\setup_editor.ps1
.\build.ps1 -Configuration Release
.\tools\run_editor.ps1
```

打开工程：

```powershell
.\tools\run_editor.ps1 .\mod\visual_events\visual_events.cmm
```

渲染 MP4 或检查单帧：

```powershell
.\build\release\chemanim.exe visual_events --no-open
.\build\release\chemanim.exe visual_events --frame 75 --no-open
```

结果写入 `media/<mod>/`。编辑器会核对 `chemanim_core.pyd` 内置提交号与当前源码；不一致时会要求先重建，避免旧二进制造成假通过。

## 目前还不能做什么

这不是化学验证器，也还不是 ChemDraw 的完整替代品。当前没有自动价态修复、芳香性运行时语义、反应知识库、力场、键角助手或可用的基团库。多分子联合选择、曲箭头完整画布操作柄，以及复杂拓扑转移与同时进行的多重分子变换仍需要更多实用项目检验。

格式见 [tools/CMM_FORMAT.md](tools/CMM_FORMAT.md)，实现边界见 [docs/native-2d-status.md](docs/native-2d-status.md)，第三方来源见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
