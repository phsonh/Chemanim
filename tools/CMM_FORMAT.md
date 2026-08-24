# `.cmm` v2 工程格式

原生二维编辑器使用 JSON 文本，扩展名仍为 `.cmm`。根对象必须包含：

```json
{
  "format": "chemanim-native-2d",
  "version": 2,
  "mod": "native2d_demo",
  "scene": {},
  "style": {},
  "molecules": [],
  "nodes": []
}
```

编辑器不会把旧版 `chemanim-linear-nodes` v1 当作 v2 猜测读取；打开旧文件时会明确提示使用 Git 历史中的旧编辑器。

## 场景和样式

`scene` 保存输出尺寸、逻辑尺寸、FPS、背景、标题和二维视图缩放 `view_zoom`。坐标原点在画布中心，X 向右、Y 向上。

`style.preset` 当前固定为 `acs_document_1996`。默认值是 Arial 10 pt、14.4 pt 参考键长、0.6 pt 线宽及 18% 双键间距。编辑器预览可以独立缩放；保存的原子坐标不会因此改变。

## 分子

每个 `molecules[]` 项是一个高层场景对象，包含对象变换、源 SMILES、原子、键和预留的 Pose 数据。SMILES 只记录来源；生成后不会覆盖手工坐标。

原子字段：

- `id`：稳定 ID。优先使用 atom map number，否则为 `A1`、`A2`……；
- `element`、`isotope`、`formal_charge`、`radical_electrons`；
- `implicit_hydrogens`、`aromatic`、`chirality`、`alias`、`hidden`；
- `x`、`y`：分子局部二维坐标。

键字段：

- `id`：稳定 ID，如 `B1`；
- `a`、`b`：两端原子的稳定 ID；
- `order`、`aromatic`、`stereo`、`visible`。

当前 `stereo` 支持 `none`、`wedge`、`dash` 和 `either` 数据值；第一阶段 C++ 绘制实楔和虚楔，波浪键会在后续显示编辑中补齐。

`nodes` 在第一阶段保留为空数组。后续的 Set/Lerp、Pose 与拓扑事件会放在这里，不会把每个原子变成场景对象或 Lua table。
