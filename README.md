# Chemanim

Chemanim 是我用来制作有机反应机理动画的一个个人工具。最初的做法是从 ChemDraw 导出每个状态的 PNG，再用 Lua 控制贴图淡入、移动和曲箭头。这个工作流能用，但结构一改就要重新导图，不同状态也很难自然对齐。

项目现在正在改成原生二维结构式：在编辑器里输入 SMILES 得到二维起稿，原子、键和坐标直接保存在 `.cmm` 中；手工拖动后的排版是权威数据。结构式的第一阶段绘制直接采用 RDKit `MolDraw2D` 的 ACS1996 SVG，不再由 Chemanim 猜标签和双键布局。

## 当前状态

第一条原生二维链路已经可以使用：

- 由 RDKit/CoordGen 从 SMILES 生成二维坐标；
- 原子和键使用稳定 ID，普通碳与其隐式氢默认不显示；
- 编辑器可以点选、框选、多选和拖动原子，也可以输入精确的 X/Y；
- 拖动支持撤销、重做，工程以 v2 `.cmm` 原子写入；
- 编辑器把当前 XY 写回二维 conformer，并实时显示 RDKit ACS1996 SVG；
- 创建时的参考键长会保存，不会因后续拖动而逐帧重新缩放；
- C++ 当前使用同一份 ACS1996 SVG 做运行时合成，因此标签、双键、楔键和避让语义来自 RDKit；
- 可以先输出 1920×1080 PNG 检查最终渲染。

旧的 PNG 模组和 MP4 管线暂时仍留在分支中作对照。现在的 C++ SVG 合成是第一阶段过渡后端，还不是可逐原子更新的 RDKit C++ `MolDraw2D` 后端；原子动画、键长、键角、分支旋转、Pose 和拓扑变化都还没有迁移。

## 在 Windows 上运行

准备编辑器环境并启动：

```powershell
.\tools\setup_editor.ps1
.\tools\run_editor.ps1
```

在工具栏选择“从 SMILES 新建”，拖动原子后保存即可。仓库里有一个带芳环、羧基和虚楔键的布洛芬 v2 示例：

```powershell
.\tools\run_editor.ps1 .\mod\native2d_demo\native2d_demo.cmm
```

构建 C++ 引擎并输出静态检查图：

```powershell
.\build.ps1
.\build\release\chemanim.exe native2d_demo --still --no-open
```

图片会生成在 `media/native2d_demo/native2d_demo_preview.png`。不带 `--still` 时仍使用现有 Media Foundation 管线输出 MP4。

## Lua 数据入口

编辑器会生成这种短脚本；实际的 `atoms` 和 `bonds` 由 `.cmm` 编译进去：

```lua
local chem = require("chem")

chem.scene {
    width = 1920, height = 1080,
    logic_width = 960, logic_height = 540,
    fps = 60, view_zoom = 2.2,
    background = "FFFFFFFF"
}

local molecule1 = chem.NewMol(compiled_molecule_data)
molecule1.SetPos(0, 0)
molecule1.SetAlpha(255)
```

v2 工程字段见 [tools/CMM_FORMAT.md](tools/CMM_FORMAT.md)，现阶段的技术边界见 [docs/native-2d-status.md](docs/native-2d-status.md)。仓库地址是 <https://github.com/phsonh/Chemanim>。
