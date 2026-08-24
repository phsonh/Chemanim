# Chemanim

Chemanim 是我用来做有机反应机理动画的个人工具。它原来依赖 ChemDraw 导出的整张 PNG；现在正在改成原生二维结构式，让原子、键和 XY 直接参与逐帧动画。

当前的核心是一个真正共享的 C++ 模块：分子文档、稳定 ID、编辑手势、15° 吸附、环模板、撤销重做、时间轴求值、RDKit `MolDraw2D` ACS1996 描绘和 NanoSVG 最终栅格化都在这里。C++ 引擎直接链接它，PyQt6 编辑器通过 `chemanim_core.pyd` 调用它；Python 只负责窗口、工具状态和输入事件，没有第二套化学模型或绘制规则。

## 已经能做什么

- 从 SMILES 生成起稿，或从空白分子开始手画；SMILES 不会在保存后重新决定拓扑。
- 框选、套索、移动、删除、橡皮、元素和正负电荷。
- 单键、双键、三键、芳香键、实楔键、虚楔键和波浪键。
- 空白、单原子和稠合键上的 3–8 元环模板及苯环模板。
- 键手势按 15° 吸附，Alt 临时关闭；靠近已有原子时连接吸附优先。
- `.cmm` v3 保存稳定的 molecule/atom/bond/timeline ID，关闭重开不重编号。
- `SetAtomXY`、`LerpAtomXY`、批量 `LerpAtomsXY`；同原子重叠插值由后一个从当前状态接管。
- 基础结构编辑、只读时间轴预览和 Lerp 目标姿态编辑相互分开。
- 编辑器普通预览显示共享 Core 的 SVG；“最终效果预览”显示与引擎相同的 NanoSVG RGBA。
- 引擎按当前帧 atom/bond/XY 动态生成 SVG；静止结构命中缓存，不再把整分子 `acs_svg` 编译进 Lua。

## Windows 上启动

需要 Visual Studio 的“使用 C++ 的桌面开发”和 Python 3.14。首次准备会在仓库的 `.deps` 中安装 RDKit 2026.03.5 C++ 开发包：

```powershell
.\tools\setup_editor.ps1
.\build.ps1
.\tools\run_editor.ps1
```

打开现有工程：

```powershell
.\tools\run_editor.ps1 .\mod\atom_motion\atom_motion.cmm
```

直接渲染 MP4、单帧和性能报告：

```powershell
.\build\release\chemanim.exe atom_motion --no-open
.\build\release\chemanim.exe atom_motion --frame 30 --no-open
.\build\release\chemanim.exe atom_motion --no-open --profile
```

MP4 和检查帧写入 `media/<mod>/`。构建会递归复制 RDKit 的运行时 DLL，所以生成的 EXE 不要求手工设置 `PATH`。

## 目前还不能做什么

这还不是 ChemDraw 的完整替代品。当前没有反应物自动对齐、键角/分支旋转助手、力场、自动价态修复、自由基工具、成键/断键时间轴事件和完整的场景曲箭头整合。价态异常现在只允许存在，还没有做成完善的诊断面板。环模板和基础结构工具已经是真实数据操作，但界面图标与属性面板仍会继续打磨。

格式说明见 [tools/CMM_FORMAT.md](tools/CMM_FORMAT.md)，实现边界见 [docs/native-2d-status.md](docs/native-2d-status.md)。
