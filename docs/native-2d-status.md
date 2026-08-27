# 原生二维实现边界

当前数据流只有一套视觉行为：

```text
PyQt 输入事件
  → chemanim_core.pyd
  → C++ Document / Transaction / ordered nodes
  → 编译后的 typed tracks / 当前帧求值
  → C++ Depiction
  → 当前帧显式 atom/bond/adornment + XY
  → ACS1996 标签几何 + Core 固定视觉键 SVG
  ├─ Qt SVG 普通预览
  └─ NanoSVG RGBA 最终预览与 C++ 引擎
```

Python 不调用 RDKit，也不拥有可变 Atom/Bond 文档或另一套时间轴。界面看到的 dict 只是 C++ Core 的快照；修改只能通过 Core 命令或一次完整的 pointer transaction 提交。`.cmm` v5 只保存 ordered node sequence，typed tracks 是按节点顺序随时重新求值的结果。

RDKit 只在 SMILES 导入时解析并展平芳香表示，并在描绘时提供 ACS 字体和标签几何。运行时文档没有 aromatic perception、Kekulé 或价态纠正；单、双、三键及双键副线方向完全服从 Core 保存的显式视觉数据。

运行时缓存使用拓扑、原子属性、键属性和当前 XY 组成的几何键。静止分子只在首帧生成、解析、栅格化并上传；原子运动时才标脏。`--profile` 分别记录 SVG 生成、NanoSVG 解析、栅格化和纹理上传时间。

基础结构编辑与脚本目标编辑分离。线性节点已覆盖分子变换、原子 XY、带圈形式电荷、选择淡入淡出、成键/断键、基团转移、分子合并和曲箭头的主要显示属性。多分子联合选择、完整箭头画布操作柄以及数据驱动基团库仍未完成。
