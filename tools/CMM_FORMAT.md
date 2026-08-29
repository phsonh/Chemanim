# `.cmm` v6

`.cmm` 是 UTF-8 JSON。共享 C++ Core 读写工程、执行 transaction，并把有序节点求值为 typed tracks；PyQt 只显示 Core 返回的快照。

```json
{
  "format": "chemanim-native-2d",
  "version": 6,
  "mod": "visual_events",
  "next_molecule_id": 3,
  "next_node_id": 12,
  "next_creation_serial": 20,
  "scene": {},
  "style": {},
  "molecules": [],
  "nodes": [
    {"id": "N1", "type": "scene", "enabled": true, "params": {}},
    {"id": "N2", "type": "wait", "enabled": true, "params": {"frames": 30}}
  ]
}
```

## 权威数据

`source_smiles` 只记录导入来源。权威画面由 atom、bond、adornment 及其 XY 决定：

- Atom 没有 `aromatic` 或 `formalCharge`。`creation_serial` 在整个工程内单调递增，删除、撤销和重开都不复用。元素快捷项与文字工具统一写入视觉 `label`；`label_side` 保存左右排版，`number_style` 保存数字的正常/下标/上标模式。
- Bond 只有显式 `single/double/triple` 视觉类型、楔键样式和持久化 `secondary_line_side`。Core 不会因价态、成环或增加取代基改写它。
- AtomAdornment 是形式电荷的内部保存结构，默认显示 `⊕`/`⊖`，并保存锚定 atom、本地偏移、颜色、透明度和存活状态；编辑器不暴露这个内部类型名。
- 当前最早创建且仍存活的 atom 是分子锚点；分子坐标从该 atom 的当前世界 XY 派生，不单独存一份可能失配的位置。

SMILES 导入可以调用 RDKit 解析并 Kekulé 化一次，再立即展平为上述显式数据。保存的 v6 文档不含芳香性语义。

## 动画语义

`nodes` 是唯一创作层。Lerp 从当前时间启动但不推进时间，Wait 推进时间，不同属性可以并行；后发的同属性 Lerp 从接管帧的当前值开始。typed tracks、节点起止帧、逐帧预览和 Lua 都由 C++ Core 从节点序列生成。

拓扑事件以稳定 ID 转移所有权而不是复制：`FormBond`、`BreakBond`、`DetachSubgraph`、`MergeMolecules` 和 `FadeSelection` 都可在任意帧重新求值，拖动时间轴不会破坏基础工程。

## 旧格式迁移

Core 可读取 v2–v5。旧 `display_type` 优先转换为显式单/双键，旧芳香键在没有显示类型时只做一次确定性展平；旧 formal charge 转成带圈形式电荷；旧 `alias` 迁移为 `label`。下次保存只写 v6，并删除 aromatic、displayType、formalCharge 和旧 timeline 字段。

工作区 pan/zoom 不进入 `.cmm`。Scene 输出/逻辑尺寸、背景、FPS 和标题属于工程；基础结构 XY 与动画节点目标坐标严格分开。
