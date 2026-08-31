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

对象身份、局部结构状态、对象变换和编辑视图已经分层。曲箭头支持画布自由拖拽起稿、滚轮粗调以及 P0/C1/C2/P3 四点精调；所有设定/变换节点仍可通过非模态参数检查器精确输入。旧细粒度结构节点仅保留兼容执行，不再作为新建入口。
