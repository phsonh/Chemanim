# 原生二维实现边界

当前数据流只有一套化学行为：

```text
PyQt 输入事件
  → chemanim_core.pyd
  → C++ Document / Transaction / ordered nodes
  → 编译后的 typed tracks / 当前帧求值
  → C++ Depiction
  → RDKit atom/bond + 当前 XY conformer
  → ACS1996 SVG（固定键长与固定 viewBox）
  ├─ Qt SVG 普通预览
  └─ NanoSVG RGBA 最终预览与 C++ 引擎
```

Python 不调用 RDKit，也不拥有可变 Atom/Bond 文档或另一套时间轴。工程树、节点列表和检查器看到的 dict 只是 C++ Core 的快照；修改只能通过 Core 命令或一次完整的 pointer transaction 提交。`.cmm` v4 只保存 ordered node sequence，typed tracks 是按节点顺序随时重新编译的求值结果。

运行时缓存使用拓扑、原子属性、键属性和当前 XY 组成的几何键。静止分子只在首帧生成、解析、栅格化并上传；原子运动时才标脏。`--profile` 分别记录 SVG 生成、NanoSVG 解析、栅格化和纹理上传时间。

当前 topology 编辑只作用于基础结构。线性节点已覆盖分子变换、原子 XY/Pose、键形成/删除/键级/立体/可见和曲箭头的主要显示属性。价态诊断 UI、自由基工具、多分子联合选择、完整箭头画布操作柄以及数据驱动基团库仍未完成。
