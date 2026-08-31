# `.cmm` v8

`.cmm` 是 UTF-8 JSON。共享 C++ Core 负责读写工程、事务、迁移和有序节点求值；PyQt 只消费 Core 返回的状态和显式编辑能力。

```json
{
  "format": "chemanim-native-2d",
  "version": 8,
  "mod": "visual_events",
  "scene": {},
  "style": {},
  "molecules": [
    {"id": "molecule1", "name": "分子 1", "anchor": {"x": 0, "y": 0}, "anchor_initialized": false,
     "atoms": [], "bonds": [], "adornments": []}
  ],
  "nodes": [
    {"id": "N1", "type": "scene", "enabled": true, "params": {}},
    {"id": "N2", "type": "molecule_create", "enabled": true, "params": {"target": "molecule1"}},
    {"id": "N3", "type": "molecule_set_structure", "enabled": true,
     "params": {"target": "molecule1", "coordinate_space": "molecule_local_v2", "snapshot": {}}}
  ]
}
```

## 四层权威模型

- 对象身份：`molecule_create` 只建立稳定 molecule ID、名称、生命周期和独立 `anchor`；对象本身不保存可编辑结构。
- 新空对象的 `anchor_initialized=false`。第一次提交非空结构时，Core 以存活原子的包围盒中心初始化一次真实锚点，同时反向平移局部坐标以保持画面不跳；此后拓扑变化不再自动重算锚点。缺少该字段的既有 v8 文件按已初始化处理，避免静默改变已有动画。
- 结构状态：`molecule_set_structure` 保存瞬时完整结构；`molecule_gradient_structure` 保存起点/终点结构。快照中的 atom/bond/adornment 使用稳定 ID 和 molecule-local 坐标。
- 对象变换：位置节点修改 `anchor`，X/Y 缩放和旋转围绕该锚点求值；原子增删、首原子删除和拓扑变化都不能改变锚点。
- 编辑视图：Core 将局部结构套用节点处的对象/全局变换后显示，并把世界空间手势经逆变换写回局部快照。洋葱皮属于编辑器覆盖层，不序列化、不导出。

最终坐标顺序为：局部结构 → 局部 X/Y 缩放与旋转 → 对象锚点平移 → 场景级倍率。颜色和透明度同样先求局部值，再与全局 track 相乘。

## 节点与工具元数据

Registry 显式提供 `category`、`scope`、`section`、`order`、`exposure`、`target_kind`、`structure_edit_capability`、`direct_manipulation_capability` 和 `show_section`。UI 不通过 type 名称猜测权限或工具栏层级。

`scope=object` 的入口直接显示动作，不制造“对象 → 对象”重复层级。所有设定/变换参数仍可在非模态检查器中编辑；拥有直接操作能力的坐标和箭头曲线节点还可在画布拖动。

## 结构与稳定 ID

- 元素快捷项与文字工具统一写入视觉 `label`；`label_side` 保存左右排版，`number_style` 保存正常/下标/上标。
- Bond 使用显式 `single/double/triple`、立体类型和 `secondary_line_side`。
- AtomAdornment 保存带圈形式电荷等结构标记，但用户界面不暴露内部 ID。
- SMILES/模板导入是一次 undo 事务，但会生成相邻且语义独立的“新建分子 + 设定分子结构”两个节点。

## 旧格式迁移

Core 可读取 v2–v7。v7 及更早版本中分子对象上的基础结构会迁移成紧随创建节点的 `molecule_set_structure`：最早存活原子的旧世界坐标一次性推导为稳定对象锚点，原子坐标转换成相对锚点的局部坐标，稳定原子/键/标记 ID 保持不变。旧 uniform scale 迁移成相同的 `scale_x/scale_y`。

旧箭头位置节点和细粒度结构节点继续解析、求值、保存和生成 Lua，但 registry 标记为 legacy，不再出现在新建工具栏。保存后统一写 v8。

工作区 pan/zoom、洋葱皮和控制柄不进入 `.cmm`。
