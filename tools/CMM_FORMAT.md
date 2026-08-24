# `.cmm` v3

`.cmm` 是 UTF-8 JSON。权威数据由共享 C++ Core 读写，PyQt 不维护平行的 dataclass 模型。

```json
{
  "format": "chemanim-native-2d",
  "version": 3,
  "mod": "atom_motion",
  "next_molecule_id": 2,
  "next_timeline_id": 4,
  "scene": {},
  "style": {},
  "molecules": [],
  "timeline": { "atom_tweens": [], "pose_tweens": [] }
}
```

Core 仍可读取现有 v2 原生二维工程；下次保存会写成 v3。旧的 `chemanim-linear-nodes` v1 不是同一种格式。

## 分子

每个 molecule 是一个场景对象。`source_smiles` 只记录导入来源；`atoms`、`bonds` 和 XY 才决定当前拓扑和画面。`next_atom_id` 与 `next_bond_id` 单调递增，因此删除后不会复用稳定 ID。

原子主要字段为 `id`、`element`、`x`、`y`、`isotope`、`formal_charge`、`radical_electrons`、`implicit_hydrogens`、`aromatic`、`alias` 和 `hidden`。

键主要字段为 `id`、`a`、`b`、`type`、`stereo` 和 `visible`。`type` 为 `single`、`double`、`triple` 或 `aromatic`；`stereo` 为 `none`、`wedge`、`dash` 或 `wavy`。

Pose 存储 `atom ID → {x,y}`，不会复制拓扑。原子和键不是独立场景对象。

## 时间轴

`atom_tweens` 保存稳定节点 ID、molecule/atom ID、起始帧、帧数、目标 XY 和 easing。`pose_tweens` 指向 molecule 内部的一组 Pose 坐标。后发的同原子插值会终止仍在运行的前一个插值，并以该帧求值结果为新起点。

画布观察缩放不写回模型。编辑基础结构时修改初始 XY；编辑 tween 或 Pose 时只修改节点目标。
