# 原生二维实现边界

当前数据流只有一套化学行为：

```text
PyQt 输入事件
  → chemanim_core.pyd
  → C++ Document / Transaction / Timeline / Depiction
  → RDKit atom/bond + 当前 XY conformer
  → ACS1996 SVG（固定键长与固定 viewBox）
  ├─ Qt SVG 普通预览
  └─ NanoSVG RGBA 最终预览与 C++ 引擎
```

Python 不调用 RDKit，也不拥有可变 Atom/Bond 文档。工程树和检查器看到的 dict 只是 C++ Core 的只读快照；修改只能通过 Core 命令或一次完整的 pointer transaction 提交。

运行时缓存使用拓扑、原子属性、键属性和当前 XY 组成的几何键。静止分子只在首帧生成、解析、栅格化并上传；原子运动时才标脏。`--profile` 分别记录 SVG 生成、NanoSVG 解析、栅格化和纹理上传时间。

当前 topology 编辑只作用于基础结构。时间轴第一批覆盖原子 XY 与 Pose；拓扑事件、价态诊断 UI、自由基工具以及电子转移箭头和原子锚点的完整整合仍未完成。
