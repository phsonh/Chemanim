# 原生二维阶段说明

当前分支完成的是一条可检查画面和编辑手感的纵向切片，不是完整动画节点迁移。

数据流是：

```text
SMILES
  → 编辑器中的 RDKit/CoordGen（只生成一次二维起稿）
  → v2 .cmm（内嵌原子、键、稳定 ID、XY）
  → RDKit MolDraw2D ACS1996 SVG（由当前 XY 派生）
  → Lua 数据表
  → C++ SVG 运行时合成
```

C++ 不链接也不调用 RDKit；生成 Lua 时会把当前 XY 的 ACS1996 SVG 一起编译进去。SVG 是派生的运行时绘制结果，不写入 `.cmm`，也不是权威结构数据。编辑器保存后，手工 XY 是权威数据；重新布局只能作为以后显式、可撤销的操作加入。

第一阶段已经覆盖 SMILES 生成、RDKit ACS1996 SVG 基准、原子点选/框选/多选/拖动、精确 XY、拖动撤销重做、v2 工程保存、Lua 生成和 C++ 静态 PNG。高层 molecule 仍是一个对象，atom/bond 只是内部数据。`tools/render_acs_reference.py` 与 `tools/compare_acs_render.py` 用于输出 golden reference 和放大差异图。

尚未覆盖：面向逐原子动画的 RDKit C++/等价矢量命令后端，键选择器、键长/键角/分支旋转控制，Pose，原子坐标与几何控制的 Set/Lerp，成键/断键/键级/电荷事件，分子内部锚点电子箭头，以及新节点时间轴。旧贴图系统要等新画面确认后才从工作树清理。
