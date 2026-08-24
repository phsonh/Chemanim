# `.cmm` v4

`.cmm` 是 UTF-8 JSON。共享 C++ Core 读写工程、执行编辑 transaction，并把有序节点编译为 typed tracks；PyQt 只显示 Core 返回的文档和求值结果。

```json
{
  "format": "chemanim-native-2d",
  "version": 4,
  "mod": "atom_motion",
  "next_molecule_id": 2,
  "next_node_id": 8,
  "scene": {},
  "style": {},
  "molecules": [],
  "nodes": [
    {"id": "N1", "type": "scene", "enabled": true, "params": {}},
    {"id": "N2", "type": "wait", "enabled": true, "params": {"frames": 30}}
  ]
}
```

Core 可以读取 v2/v3 原生二维工程，并在内存中一次性迁移为 ordered node sequence；下次保存只写 v4，不再持久化旧 `timeline.atom_tweens`。

## 权威层

`source_smiles` 只记录导入来源；`atoms`、`bonds` 和 XY 决定拓扑与初始画面。SMILES 导入只做一次 Kekulé 展平，保存后只剩显式单、双、三键。双键的 `secondary_line_side`（`left/right/center`）是持久化视觉数据，编辑与播放都不会自动重排。每个原子的 `creation_serial` 单调递增且不因删除、撤销或重开复用；最早存活原子就是分子锚点。

`nodes` 是唯一动画创作层。节点顺序决定当前时间：Lerp 在当前帧开始但不推进时间，Wait 推进时间，不同属性可以并行；后发的同属性 Lerp 从接管帧的当前值开始。typed tracks、节点起止帧、预览结果和 Lua 都由 C++ Core 随节点序列编译，不是第二份可编辑数据。

画布 pan/zoom 仅为编辑器工作区状态，不进入 `.cmm`。Scene 输出/逻辑尺寸、背景、FPS 和标题属于工程；基础结构 XY 与动画节点目标坐标也严格分开。
