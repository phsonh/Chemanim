from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QAction, QBrush, QColor, QIcon, QImageReader, QKeySequence, QPainter, QPainterPath,
    QPen, QPixmap, QPolygonF, QTextCursor, QTextFormat, QTransform,
)
from PyQt6.QtWidgets import (
    QAbstractItemView, QApplication, QCheckBox, QComboBox,
    QDoubleSpinBox, QFileDialog, QFormLayout, QGraphicsEllipseItem,
    QGraphicsItem, QGraphicsLineItem, QGraphicsPathItem, QGraphicsPixmapItem,
    QGraphicsPolygonItem, QGraphicsScene, QGraphicsView, QGroupBox, QHBoxLayout,
    QHeaderView, QInputDialog, QLabel, QLineEdit, QMainWindow, QMenu,
    QMessageBox, QPlainTextEdit, QPushButton, QSlider, QSpinBox, QSplitter, QStyle,
    QTabBar, QTableWidget, QTableWidgetItem, QTextEdit, QToolBar,
    QToolButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

try:
    from .editor_naming import (
        inherited_node_parameters, live_objects_at, next_numbered_object_name,
    )
    from .editor_ui import (
        ColorValueEditor, compact_nepy_stylesheet,
        MultiTextureFileEditor, TextureFileEditor, TextureResourcePicker,
        node_subcategory, ordered_subcategories,
        parse_color_text,
    )
except ImportError:  # Direct execution via tools/run_editor.ps1
    from editor_naming import (
        inherited_node_parameters, live_objects_at, next_numbered_object_name,
    )
    from editor_ui import (
        ColorValueEditor, compact_nepy_stylesheet,
        MultiTextureFileEditor, TextureFileEditor, TextureResourcePicker,
        node_subcategory, ordered_subcategories,
        parse_color_text,
    )


ROOT = Path(__file__).resolve().parents[1]
MOD_ROOT = ROOT / "mod"
CMM_FORMAT = "chemanim-linear-nodes"
CMM_VERSION = 1


def field(key: str, label: str, kind: str, default: Any) -> dict[str, Any]:
    return {"key": key, "label": label, "kind": kind, "default": default}


NODE_DEFS: dict[str, dict[str, Any]] = {
    "module": {"label": "加载 Chem 模块", "category": "通用", "color": "#546E7A", "palette": False, "fields": []},
    "scene": {"label": "场景搭建", "category": "通用", "color": "#3949AB", "fields": [
        field("width", "视频宽度", "int", 1920), field("height", "视频高度", "int", 1080),
        field("logic_width", "逻辑宽度", "int", 960), field("logic_height", "逻辑高度", "int", 540),
        field("fps", "FPS", "int", 60),
        field("background", "背景颜色", "scene_color", "FFFFFFFF"), field("title", "标题", "text", "animation"),
    ]},
    "load_texture": {"label": "资源加载", "category": "通用", "color": "#00897B", "fields": [
        field("name", "资源名", "text", "texture"), field("file", "PNG 文件", "file", "texture.png"),
        field("anchor_x", "锚点 X", "float01", 0.5), field("anchor_y", "锚点 Y", "float01", 0.5),
    ]},
    "load_textures": {"label": "批量资源加载", "category": "通用", "color": "#00796B", "fields": [
        field("files", "PNG 文件", "files", []),
    ]},
    "new_object": {"label": "新建分子对象", "category": "分子", "color": "#7CB342", "fields": [field("name", "对象名", "text", "molecule1")]},
    "new_arrow": {"label": "新建曲箭头", "category": "箭头", "color": "#D81B60", "fields": [field("name", "对象名", "text", "arrow1")]},
    "set_image": {"label": "选择纹理", "category": "分子", "color": "#43A047", "fields": [field("object", "对象", "sprite", ""), field("texture", "纹理", "texture", "")]},
    "change_image": {"label": "过渡更换纹理", "category": "分子", "color": "#FB8C00", "fields": [
        field("object", "对象", "sprite", ""), field("texture", "目标纹理", "texture", ""),
        field("x", "新贴图 X", "float", 0), field("y", "新贴图 Y", "float", 0),
        field("frames", "帧数", "int", 30), field("mode", "模式", "mode", 0),
    ]},
    "set_pos": {"label": "设定坐标", "category": "分子", "color": "#43A047", "fields": [field("object", "对象", "sprite", ""), field("x", "X", "float", 0), field("y", "Y", "float", 0)]},
    "set_pos_x": {"label": "设定横坐标", "category": "分子", "color": "#43A047", "fields": [field("object", "对象", "sprite", ""), field("value", "X", "float", 0)]},
    "set_pos_y": {"label": "设定纵坐标", "category": "分子", "color": "#43A047", "fields": [field("object", "对象", "sprite", ""), field("value", "Y", "float", 0)]},
    "set_alpha": {"label": "设定透明度", "category": "分子", "color": "#43A047", "fields": [field("object", "对象", "sprite", ""), field("value", "Alpha", "alpha", 255)]},
    "mol_color": {"label": "设定分子颜色", "category": "分子", "color": "#43A047", "fields": [field("object", "对象", "sprite", ""), field("r", "R", "byte", 255), field("g", "G", "byte", 255), field("b", "B", "byte", 255)]},
    "set_scale": {"label": "设定缩放", "category": "分子", "color": "#43A047", "fields": [field("object", "对象", "sprite", ""), field("x", "Scale X", "float", 1), field("y", "Scale Y", "float", 1)]},
    "set_scale_x": {"label": "设定横向缩放", "category": "分子", "color": "#43A047", "fields": [field("object", "对象", "sprite", ""), field("value", "Scale X", "float", 1)]},
    "set_scale_y": {"label": "设定纵向缩放", "category": "分子", "color": "#43A047", "fields": [field("object", "对象", "sprite", ""), field("value", "Scale Y", "float", 1)]},
    "set_rotation": {"label": "设定旋转", "category": "分子", "color": "#43A047", "fields": [field("object", "对象", "sprite", ""), field("value", "角度", "float", 0)]},
    "set_layer": {"label": "设定层级", "category": "分子", "color": "#43A047", "fields": [field("object", "对象", "sprite", ""), field("value", "层级", "float", 0)]},
    "set_visible": {"label": "设定可见", "category": "分子", "color": "#43A047", "fields": [field("object", "对象", "sprite", ""), field("value", "可见", "bool", True)]},
    "set_anchor": {"label": "覆盖对象锚点", "category": "分子", "color": "#43A047", "fields": [field("object", "对象", "sprite", ""), field("x", "锚点 X", "float01", 0.5), field("y", "锚点 Y", "float01", 0.5)]},
    "lerp_pos": {"label": "插值坐标", "category": "分子", "color": "#FB8C00", "fields": [field("object", "对象", "sprite", ""), field("x", "目标 X", "float", 0), field("y", "目标 Y", "float", 0), field("frames", "帧数", "int", 30), field("mode", "模式", "mode", 0)]},
    "lerp_pos_x": {"label": "插值横坐标", "category": "分子", "color": "#FB8C00", "fields": [field("object", "对象", "sprite", ""), field("value", "目标 X", "float", 0), field("frames", "帧数", "int", 30), field("mode", "模式", "mode", 0)]},
    "lerp_pos_y": {"label": "插值纵坐标", "category": "分子", "color": "#FB8C00", "fields": [field("object", "对象", "sprite", ""), field("value", "目标 Y", "float", 0), field("frames", "帧数", "int", 30), field("mode", "模式", "mode", 0)]},
    "lerp_alpha": {"label": "插值透明度", "category": "分子", "color": "#FB8C00", "fields": [field("object", "对象", "sprite", ""), field("value", "目标 Alpha", "alpha", 255), field("frames", "帧数", "int", 30), field("mode", "模式", "mode", 0)]},
    "lerp_mol_color": {"label": "插值分子颜色", "category": "分子", "color": "#FB8C00", "fields": [field("object", "对象", "sprite", ""), field("r", "目标 R", "byte", 255), field("g", "目标 G", "byte", 255), field("b", "目标 B", "byte", 255), field("frames", "帧数", "int", 30), field("mode", "模式", "mode", 0)]},
    "lerp_scale": {"label": "插值缩放", "category": "分子", "color": "#FB8C00", "fields": [field("object", "对象", "sprite", ""), field("x", "目标 Scale X", "float", 1), field("y", "目标 Scale Y", "float", 1), field("frames", "帧数", "int", 30), field("mode", "模式", "mode", 0)]},
    "lerp_scale_x": {"label": "插值横向缩放", "category": "分子", "color": "#FB8C00", "fields": [field("object", "对象", "sprite", ""), field("value", "目标 Scale X", "float", 1), field("frames", "帧数", "int", 30), field("mode", "模式", "mode", 0)]},
    "lerp_scale_y": {"label": "插值纵向缩放", "category": "分子", "color": "#FB8C00", "fields": [field("object", "对象", "sprite", ""), field("value", "目标 Scale Y", "float", 1), field("frames", "帧数", "int", 30), field("mode", "模式", "mode", 0)]},
    "lerp_rotation": {"label": "插值旋转", "category": "分子", "color": "#FB8C00", "fields": [field("object", "对象", "sprite", ""), field("value", "目标角度", "float", 0), field("frames", "帧数", "int", 30), field("mode", "模式", "mode", 0)]},
    "wait": {"label": "等待", "category": "通用", "color": "#8E24AA", "fields": [field("frames", "帧数", "int", 30)]},
    "delete": {"label": "删除分子", "category": "分子", "color": "#E53935", "fields": [field("object", "对象", "sprite", "")]},
    "arrow_curve": {"label": "设定贝塞尔曲线", "category": "箭头", "color": "#D81B60", "fields": [
        field("object", "箭头", "arrow", ""), field("x1", "起点 X", "float", 0), field("y1", "起点 Y", "float", 0),
        field("cx1", "控制点 1 X", "float", 0), field("cy1", "控制点 1 Y", "float", 0),
        field("cx2", "控制点 2 X", "float", 0), field("cy2", "控制点 2 Y", "float", 0),
        field("x2", "终点 X", "float", 0), field("y2", "终点 Y", "float", 0),
    ]},
    "arrow_set_pos": {"label": "设定箭头坐标", "category": "箭头", "color": "#D81B60", "fields": [field("object", "箭头", "arrow", ""), field("x", "X", "float", 0), field("y", "Y", "float", 0)]},
    "arrow_lerp_pos": {"label": "插值箭头坐标", "category": "箭头", "color": "#EC407A", "fields": [field("object", "箭头", "arrow", ""), field("x", "目标 X", "float", 0), field("y", "目标 Y", "float", 0), field("frames", "帧数", "int", 30), field("mode", "模式", "mode", 0)]},
    "arrow_color": {"label": "设定箭头颜色", "category": "箭头", "color": "#D81B60", "fields": [field("object", "箭头", "arrow", ""), field("r", "R", "byte", 25), field("g", "G", "byte", 25), field("b", "B", "byte", 25), field("a", "A", "byte", 255)]},
    "lerp_arrow_color": {"label": "插值箭头颜色", "category": "箭头", "color": "#EC407A", "fields": [field("object", "箭头", "arrow", ""), field("r", "目标 R", "byte", 25), field("g", "目标 G", "byte", 25), field("b", "目标 B", "byte", 25), field("frames", "帧数", "int", 30), field("mode", "模式", "mode", 0)]},
    "arrow_width": {"label": "设定箭头宽度", "category": "箭头", "color": "#D81B60", "fields": [field("object", "箭头", "arrow", ""), field("value", "线宽", "float", 3)]},
    "arrow_progress": {"label": "设定箭头进度", "category": "箭头", "color": "#D81B60", "fields": [field("object", "箭头", "arrow", ""), field("value", "进度", "float01", 0)]},
    "lerp_arrow": {"label": "插值箭头进度", "category": "箭头", "color": "#D81B60", "fields": [field("object", "箭头", "arrow", ""), field("value", "目标进度", "float01", 1), field("frames", "帧数", "int", 30), field("mode", "模式", "mode", 0)]},
    "lerp_arrow_alpha": {"label": "插值箭头透明度", "category": "箭头", "color": "#D81B60", "fields": [field("object", "箭头", "arrow", ""), field("value", "目标 Alpha", "alpha", 0), field("frames", "帧数", "int", 30), field("mode", "模式", "mode", 0)]},
    "delete_arrow": {"label": "删除箭头", "category": "箭头", "color": "#C2185B", "fields": [field("object", "箭头", "arrow", "")]},
    "raw_lua": {"label": "Lua 代码", "category": "通用", "color": "#455A64", "fields": [field("code", "Lua 代码", "multiline", "-- Lua code")]},
}


MODE_NAMES = ["0  Linear", "1  EaseIn²", "2  EaseIn³", "3  EaseOut²", "4  EaseOut³", "5  EaseInOut²", "6  EaseInOut³"]

POSITION_NODE_AXES = {
    "set_pos": "both", "set_pos_x": "x", "set_pos_y": "y",
    "lerp_pos": "both", "lerp_pos_x": "x", "lerp_pos_y": "y",
}


def new_node(node_type: str) -> dict[str, Any]:
    definition = NODE_DEFS[node_type]
    node = {"id": uuid.uuid4().hex, "type": node_type, "enabled": True,
            "params": {item["key"]: deepcopy(item["default"]) for item in definition["fields"]}}
    if node_type == "arrow_curve":
        node["params"]["initialized"] = False
    return node


def default_document(mod: str) -> dict[str, Any]:
    scene = new_node("scene")
    scene["params"]["title"] = mod
    return {"format": CMM_FORMAT, "version": CMM_VERSION, "mod": mod,
            "nodes": [new_node("module"), scene]}


def empty_document() -> dict[str, Any]:
    return {"format": CMM_FORMAT, "version": CMM_VERSION, "mod": "untitled", "nodes": []}


def document_background_color(document: dict[str, Any]) -> QColor:
    value = "FFFFFFFF"
    for node in document.get("nodes", []):
        if node.get("enabled", True) and node.get("type") == "scene":
            value = str(node.get("params", {}).get("background", value))
    parsed = parse_color_text(value)
    return parsed[0] if parsed is not None else QColor("white")


def lua_string(value: Any) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def lua_number(value: Any) -> str:
    number = float(value)
    return str(int(number)) if number.is_integer() else f"{number:.6f}".rstrip("0").rstrip(".")


def identifier(value: str) -> str:
    result = re.sub(r"[^A-Za-z0-9_]+", "_", value) or "object"
    lua_keywords = {
        "and", "break", "do", "else", "elseif", "end", "false", "for",
        "function", "goto", "if", "in", "local", "nil", "not", "or",
        "repeat", "return", "then", "true", "until", "while",
    }
    return "obj_" + result if result[0].isdigit() or result in lua_keywords else result


def texture_entries(node: dict[str, Any]) -> list[dict[str, Any]]:
    """Expand either resource node into the engine's ordinary texture records."""
    params = node.get("params", {})
    if node.get("type") == "load_texture":
        return [{
            "name": str(params.get("name", "")),
            "file": str(params.get("file", "")),
            "anchor_x": params.get("anchor_x", 0.5),
            "anchor_y": params.get("anchor_y", 0.5),
        }]
    if node.get("type") == "load_textures":
        files = params.get("files", [])
        if not isinstance(files, list):
            files = []
        entries: list[dict[str, Any]] = []
        for value in files:
            if isinstance(value, dict):
                file_name = str(value.get("file", "")).strip()
                anchor_x = value.get("anchor_x", 0.5)
                anchor_y = value.get("anchor_y", 0.5)
            else:
                # Accept the early prototype shape so test projects do not
                # become unreadable; saving the property rewrites it as records.
                file_name = str(value).strip()
                anchor_x = anchor_y = 0.5
            if file_name:
                entries.append({
                    "name": Path(file_name).stem,
                    "file": file_name,
                    "anchor_x": anchor_x,
                    "anchor_y": anchor_y,
                })
        return entries
    return []


def node_lua(node: dict[str, Any]) -> str:
    t, p = node["type"], node.get("params", {})
    obj = identifier(str(p.get("object", "object")))
    if t == "module": return 'local chem = require("chem")'
    if t == "scene":
        return "\n".join(["chem.scene {", f"    width = {int(p['width'])},", f"    height = {int(p['height'])},",
            f"    logic_width = {int(p['logic_width'])},", f"    logic_height = {int(p['logic_height'])},",
            f"    fps = {int(p['fps'])},",
            f"    background = {lua_string(p['background'])},", f"    title = {lua_string(p['title'])}", "}"])
    if t in {"load_texture", "load_textures"}:
        entries = texture_entries(node)
        if not entries:
            return "-- 批量资源加载：尚未选择 PNG"
        return "\n".join(
            f"chem.load_texture({lua_string(entry['name'])}, {lua_string(entry['file'])}, "
            f"{lua_number(entry['anchor_x'])}, {lua_number(entry['anchor_y'])})"
            for entry in entries
        )
    if t == "new_object": return f"local {identifier(str(p['name']))} = chem.NewMol()"
    if t == "new_arrow": return f"local {identifier(str(p['name']))} = chem.NewArrow()"
    method = None
    args: list[str] = []
    if t == "set_image": method, args = "SetImage", [lua_string(p.get("texture", ""))]
    elif t == "change_image": method, args = "ChangeImage", [
        lua_string(p.get("texture", "")), lua_number(p.get("x", 0)),
        lua_number(p.get("y", 0)), str(int(p["frames"])), str(int(p["mode"])),
    ]
    elif t == "set_pos": method, args = "SetPos", [lua_number(p["x"]), lua_number(p["y"])]
    elif t == "set_pos_x": method, args = "SetPosX", [lua_number(p["value"])]
    elif t == "set_pos_y": method, args = "SetPosY", [lua_number(p["value"])]
    elif t == "set_alpha": method, args = "SetAlpha", [str(int(p["value"]))]
    elif t == "mol_color": method, args = "SetColor", [str(int(p[k])) for k in ("r", "g", "b")]
    elif t == "set_scale": method, args = "SetScale", [lua_number(p["x"]), lua_number(p["y"])]
    elif t == "set_scale_x": method, args = "SetScaleX", [lua_number(p["value"])]
    elif t == "set_scale_y": method, args = "SetScaleY", [lua_number(p["value"])]
    elif t == "set_rotation": method, args = "SetRotation", [lua_number(p["value"])]
    elif t == "set_layer": method, args = "SetLayer", [lua_number(p["value"])]
    elif t == "set_visible": method, args = "SetVisible", ["true" if p["value"] else "false"]
    elif t == "set_anchor": method, args = "SetAnchor", [lua_number(p["x"]), lua_number(p["y"])]
    elif t == "lerp_pos": method, args = "LerpPos", [lua_number(p["x"]), lua_number(p["y"]), str(int(p["frames"])), str(int(p["mode"]))]
    elif t == "lerp_pos_x": method, args = "LerpPosX", [lua_number(p["value"]), str(int(p["frames"])), str(int(p["mode"]))]
    elif t == "lerp_pos_y": method, args = "LerpPosY", [lua_number(p["value"]), str(int(p["frames"])), str(int(p["mode"]))]
    elif t in {"lerp_alpha", "lerp_arrow_alpha"}: method, args = "LerpAlpha", [str(int(p["value"])), str(int(p["frames"])), str(int(p["mode"]))]
    elif t == "lerp_scale": method, args = "LerpScale", [lua_number(p["x"]), lua_number(p["y"]), str(int(p["frames"])), str(int(p["mode"]))]
    elif t == "lerp_scale_x": method, args = "LerpScaleX", [lua_number(p["value"]), str(int(p["frames"])), str(int(p["mode"]))]
    elif t == "lerp_scale_y": method, args = "LerpScaleY", [lua_number(p["value"]), str(int(p["frames"])), str(int(p["mode"]))]
    elif t == "lerp_rotation": method, args = "LerpRotation", [lua_number(p["value"]), str(int(p["frames"])), str(int(p["mode"]))]
    elif t == "lerp_mol_color": method, args = "LerpColor", [str(int(p[k])) for k in ("r", "g", "b")] + [str(int(p["frames"])), str(int(p["mode"]))]
    elif t in {"delete", "delete_arrow"}: method, args = "Delete", []
    elif t == "arrow_curve":
        if not p.get("initialized", True):
            return "-- 在预览画布中按住并拖动，以绘制箭头曲线"
        method, args = "SetCurve", [lua_number(p[k]) for k in ["x1", "y1", "cx1", "cy1", "cx2", "cy2", "x2", "y2"]]
    elif t == "arrow_set_pos": method, args = "SetPos", [lua_number(p["x"]), lua_number(p["y"])]
    elif t == "arrow_lerp_pos": method, args = "LerpPos", [lua_number(p["x"]), lua_number(p["y"]), str(int(p["frames"])), str(int(p["mode"]))]
    elif t == "arrow_color": method, args = "SetColor", [str(int(p[k])) for k in ["r", "g", "b", "a"]]
    elif t == "lerp_arrow_color": method, args = "LerpColor", [str(int(p[k])) for k in ("r", "g", "b")] + [str(int(p["frames"])), str(int(p["mode"]))]
    elif t == "arrow_width": method, args = "SetWidth", [lua_number(p["value"])]
    elif t == "arrow_progress": method, args = "SetProgress", [lua_number(p["value"])]
    elif t == "lerp_arrow": method, args = "LerpProgress", [lua_number(p["value"]), str(int(p["frames"])), str(int(p["mode"]))]
    if method is not None: return f"{obj}.{method}({', '.join(args)})"
    if t == "wait": return f"chem.Wait({int(p['frames'])})"
    if t == "raw_lua": return str(p["code"])
    raise ValueError(f"未知节点类型：{t}")


def node_summary(node: dict[str, Any]) -> str:
    t, p = node["type"], node.get("params", {})
    if t == "scene": return f"{p['width']}×{p['height']} / logic {p['logic_width']}×{p['logic_height']} / {p['fps']}fps"
    if t == "load_texture": return f"{p['name']} ← {p['file']}  anchor({p['anchor_x']}, {p['anchor_y']})"
    if t == "load_textures":
        names = [entry["name"] for entry in texture_entries(node)]
        return f"{len(names)} 张 PNG" + (f"  ·  {', '.join(names)}" if names else "")
    if t in {"new_object", "new_arrow"}: return str(p["name"])
    if t == "wait": return f"{p['frames']} 帧"
    if "object" in p:
        rest = [f"{k}={v}" for k, v in p.items() if k != "object"]
        return f"{p['object']}  " + "  ".join(rest)
    if t == "raw_lua": return str(next(iter(p.values()), "")).splitlines()[0][:80]
    return "  ".join(f"{k}={v}" for k, v in p.items())


class LegacyEditorWindow(QMainWindow):
    def __init__(self, initial: Path | None = None):
        super().__init__()
        self.document = default_document("untitled")
        self.path: Path | None = None
        self.dirty = False
        self.updating = False
        self.property_widgets: dict[str, QWidget] = {}
        self.resize(1680, 940)
        self._build_ui()
        self._build_actions()
        if initial:
            self.open_path(initial)
        else:
            self.new_document()

    def _build_ui(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.toolbox = QTreeWidget()
        self.toolbox.setHeaderLabel("节点工具箱（双击插入）")
        categories: dict[str, QTreeWidgetItem] = {}
        for node_type, definition in NODE_DEFS.items():
            if not definition.get("palette", True):
                continue
            category = definition["category"]
            parent = categories.setdefault(category, QTreeWidgetItem(self.toolbox, [category]))
            item = QTreeWidgetItem(parent, [definition["label"]])
            item.setData(0, Qt.ItemDataRole.UserRole, node_type)
            item.setForeground(0, QColor(definition["color"]))
        self.toolbox.expandAll()
        self.toolbox.itemDoubleClicked.connect(self.toolbox_double_clicked)
        splitter.addWidget(self.toolbox)

        center_split = QSplitter(Qt.Orientation.Vertical)
        self.node_tree = QTreeWidget()
        self.node_tree.setHeaderLabels(["节点", "帧", "摘要", "Lua 预览"])
        self.node_tree.setColumnWidth(0, 230); self.node_tree.setColumnWidth(1, 70); self.node_tree.setColumnWidth(2, 390)
        self.node_tree.setRootIsDecorated(False)
        self.node_tree.setUniformRowHeights(True)
        self.node_tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.node_tree.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)
        self.node_tree.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.node_tree.itemSelectionChanged.connect(self.selection_changed)
        self.node_tree.itemChanged.connect(self.item_changed)
        self.node_tree.model().rowsMoved.connect(self.tree_reordered)
        center_split.addWidget(self.node_tree)
        self.lua_preview = QPlainTextEdit()
        self.lua_preview.setReadOnly(True)
        self.lua_preview.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        center_split.addWidget(self.lua_preview)
        center_split.setSizes([650, 240])
        splitter.addWidget(center_split)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        self.property_title = QLabel("选择一个节点")
        self.property_title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 6px;")
        right_layout.addWidget(self.property_title)
        self.property_box = QGroupBox("节点属性")
        self.property_form = QFormLayout(self.property_box)
        right_layout.addWidget(self.property_box)
        right_layout.addStretch()
        splitter.addWidget(right)
        splitter.setSizes([250, 1020, 390])
        self.setCentralWidget(splitter)

        toolbar = self.addToolBar("文档")
        for text, callback in [("新建", self.new_document), ("打开", self.open_dialog), ("保存", self.save),
                               ("另存为", self.save_as), ("生成 Lua", self.generate_lua),
                               ("渲染 MP4", self.render_mp4), ("复制节点", self.duplicate_node),
                               ("删除节点", self.delete_node), ("上移", lambda: self.move_node(-1)),
                               ("下移", lambda: self.move_node(1))]:
            action = toolbar.addAction(text); action.triggered.connect(callback)

    def _build_actions(self):
        for shortcut, callback in [(QKeySequence.StandardKey.New, self.new_document),
                                   (QKeySequence.StandardKey.Open, self.open_dialog),
                                   (QKeySequence.StandardKey.Save, self.save),
                                   (QKeySequence("Ctrl+D"), self.duplicate_node),
                                   (QKeySequence("Delete"), self.delete_node),
                                   (QKeySequence("Alt+Up"), lambda: self.move_node(-1)),
                                   (QKeySequence("Alt+Down"), lambda: self.move_node(1))]:
            action = QAction(self); action.setShortcut(shortcut); action.triggered.connect(callback); self.addAction(action)

    def _auto_document(self) -> Path | None:
        files = sorted(MOD_ROOT.glob("*/*.cmm")) if MOD_ROOT.exists() else []
        return files[0] if len(files) == 1 else None

    def update_title(self):
        name = self.path.name if self.path else "未命名.cmm"
        self.setWindowTitle(f"{'*' if self.dirty else ''}{name} — Chemanim 节点编辑器")

    def mark_dirty(self):
        if not self.updating:
            self.dirty = True; self.update_title()

    def maybe_discard(self) -> bool:
        if not self.dirty: return True
        result = QMessageBox.question(self, "未保存", "当前 .cmm 有未保存修改，继续将丢失这些修改。")
        return result == QMessageBox.StandardButton.Yes

    def new_document(self):
        if not self.maybe_discard(): return
        name, ok = QInputDialog.getText(self, "新建 CMM", "模组名", text="aldol")
        if not ok or not name.strip(): return
        name = name.strip()
        self.document = default_document(name); self.path = MOD_ROOT / name / f"{name}.cmm"
        self.dirty = True; self.refresh_all()

    def open_dialog(self):
        if not self.maybe_discard(): return
        name, _ = QFileDialog.getOpenFileName(self, "打开 CMM", str(MOD_ROOT), "Chemanim Model (*.cmm)")
        if name: self.open_path(Path(name))

    def open_path(self, path: Path):
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
            if document.get("format") != CMM_FORMAT or int(document.get("version", 0)) != CMM_VERSION:
                raise ValueError("不是受支持的 Chemanim CMM v1 文件")
            migrated = False
            for node_index, node in enumerate(document.get("nodes", [])):
                if node.get("type") not in NODE_DEFS: raise ValueError(f"未知节点类型：{node.get('type')}")
                node.setdefault("id", uuid.uuid4().hex); node.setdefault("enabled", True); node.setdefault("params", {})
                if node.get("type") == "change_image" and (
                    "x" not in node["params"] or "y" not in node["params"]
                ):
                    x, y = sprite_position_through(
                        document, node_index - 1, str(node["params"].get("object", "")))
                    node["params"].setdefault("x", round(x, 2))
                    node["params"].setdefault("y", round(y, 2))
                    migrated = True
                for spec in NODE_DEFS[node["type"]]["fields"]:
                    node["params"].setdefault(spec["key"], deepcopy(spec["default"]))
            self.document = document; self.path = path; self.dirty = migrated; self.refresh_all()
        except Exception as error:
            QMessageBox.critical(self, "打开失败", str(error))

    def save(self):
        if self.path is None: return self.save_as()
        self.sync_order(); self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.document, ensure_ascii=False, indent=2), encoding="utf-8")
        self.dirty = False; self.update_title(); self.statusBar().showMessage(f"已保存 {self.path}", 4000)
        return True

    def save_as(self):
        name, _ = QFileDialog.getSaveFileName(self, "保存 CMM", str(self.path or MOD_ROOT / "animation.cmm"), "Chemanim Model (*.cmm)")
        if not name: return False
        self.path = Path(name if name.lower().endswith(".cmm") else name + ".cmm")
        return self.save()

    def refresh_all(self, selected_id: str | None = None):
        self.updating = True; self.node_tree.clear()
        node_frames = self.calculate_node_frames()
        for index, node in enumerate(self.document.get("nodes", [])):
            definition = NODE_DEFS[node["type"]]
            lua = node_lua(node).replace("\n", " ")[:180]
            item = QTreeWidgetItem([f"{index + 1:03d}  {definition['label']}", str(node_frames[index]), node_summary(node), lua])
            item.setData(0, Qt.ItemDataRole.UserRole, node["id"])
            item.setFlags((item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsDragEnabled) & ~Qt.ItemFlag.ItemIsDropEnabled)
            item.setCheckState(0, Qt.CheckState.Checked if node.get("enabled", True) else Qt.CheckState.Unchecked)
            item.setForeground(0, QColor(definition["color"]))
            self.node_tree.addTopLevelItem(item)
            if selected_id == node["id"]: self.node_tree.setCurrentItem(item)
        self.updating = False; self.refresh_preview(); self.update_title()
        if self.node_tree.currentItem() is None and self.node_tree.topLevelItemCount(): self.node_tree.setCurrentItem(self.node_tree.topLevelItem(0))

    def current_index(self) -> int:
        item = self.node_tree.currentItem()
        return self.node_tree.indexOfTopLevelItem(item) if item else -1

    def calculate_node_frames(self) -> list[int]:
        current_frame = 0
        frames: list[int] = []
        for node in self.document.get("nodes", []):
            frames.append(current_frame)
            if not node.get("enabled", True):
                continue
            if node["type"] == "wait":
                current_frame += int(node["params"]["frames"])
        return frames

    def current_node(self) -> dict[str, Any] | None:
        index = self.current_index()
        return self.document["nodes"][index] if 0 <= index < len(self.document["nodes"]) else None

    def sync_order(self, *args):
        ids = [self.node_tree.topLevelItem(i).data(0, Qt.ItemDataRole.UserRole) for i in range(self.node_tree.topLevelItemCount())]
        by_id = {node["id"]: node for node in self.document["nodes"]}
        if ids and set(ids) == set(by_id): self.document["nodes"] = [by_id[node_id] for node_id in ids]

    def tree_reordered(self, *args):
        if self.updating: return
        self.sync_order(); self.mark_dirty(); self.refresh_all()

    def toolbox_double_clicked(self, item: QTreeWidgetItem):
        node_type = item.data(0, Qt.ItemDataRole.UserRole)
        if node_type: self.insert_node(node_type)

    def insert_node(self, node_type: str):
        index = self.current_index()
        through_index = index if index >= 0 else len(self.document["nodes"]) - 1
        node = new_node(node_type)
        for key, value in inherited_node_parameters(
            self.document, through_index, node_type).items():
            if key in node["params"]:
                node["params"][key] = value
        if node_type in {"new_object", "new_arrow"}:
            kind = {"new_object": "molecule", "new_arrow": "arrow"}[node_type]
            node["params"]["name"] = next_numbered_object_name(self.document, index, kind)
        live = live_objects_at(self.document, through_index)
        for spec in NODE_DEFS[node_type]["fields"]:
            key, kind = spec["key"], spec["kind"]
            object_kind = {
                "object": "molecule", "sprite": "molecule", "arrow": "arrow",
            }.get(kind)
            if object_kind is not None:
                choices = [name for name, value in live.items() if value == object_kind]
                if choices:
                    node["params"][key] = choices[-1]
            elif kind == "texture" and not node["params"].get(key):
                textures = self.texture_names()
                if textures:
                    node["params"][key] = textures[0]
        if node_type == "change_image":
            x, y = sprite_position_through(
                self.document, through_index, str(node["params"].get("object", "")))
            node["params"]["x"], node["params"]["y"] = round(x, 2), round(y, 2)
        self.document["nodes"].insert(index + 1 if index >= 0 else len(self.document["nodes"]), node)
        self.mark_dirty(); self.refresh_all(node["id"])

    def duplicate_node(self):
        node = self.current_node()
        if not node: return
        clone = deepcopy(node); clone["id"] = uuid.uuid4().hex
        if clone["type"] in {"new_object", "new_arrow"}:
            kind = {"new_object": "molecule", "new_arrow": "arrow"}[clone["type"]]
            clone["params"]["name"] = next_numbered_object_name(
                self.document, self.current_index(), kind)
        self.document["nodes"].insert(self.current_index() + 1, clone)
        self.mark_dirty(); self.refresh_all(clone["id"])

    def delete_node(self):
        index = self.current_index()
        if index < 0: return
        del self.document["nodes"][index]; self.mark_dirty(); self.refresh_all()
        if self.node_tree.topLevelItemCount(): self.node_tree.setCurrentItem(self.node_tree.topLevelItem(min(index, self.node_tree.topLevelItemCount() - 1)))

    def move_node(self, delta: int):
        index = self.current_index(); target = index + delta
        if index < 0 or target < 0 or target >= len(self.document["nodes"]): return
        node = self.document["nodes"].pop(index); self.document["nodes"].insert(target, node)
        self.mark_dirty(); self.refresh_all(node["id"])

    def item_changed(self, item: QTreeWidgetItem):
        if self.updating: return
        node_id = item.data(0, Qt.ItemDataRole.UserRole)
        node = next((n for n in self.document["nodes"] if n["id"] == node_id), None)
        if node:
            node["enabled"] = item.checkState(0) == Qt.CheckState.Checked
            self.mark_dirty(); self.refresh_frame_column(); self.refresh_preview()

    def selection_changed(self):
        node = self.current_node(); self.clear_form()
        if not node: return
        definition = NODE_DEFS[node["type"]]
        self.property_title.setText(definition["label"])
        params = node["params"]
        for spec in definition["fields"]:
            key, kind = spec["key"], spec["kind"]
            value = params.get(key, spec["default"])
            widget = self.make_editor(node, spec, value)
            self.property_widgets[key] = widget
            self.property_form.addRow(spec["label"], widget)

    def clear_form(self):
        self.property_widgets.clear()
        while self.property_form.rowCount(): self.property_form.removeRow(0)

    def make_editor(self, node: dict[str, Any], spec: dict[str, Any], value: Any) -> QWidget:
        key, kind = spec["key"], spec["kind"]
        if kind in {"int", "alpha", "byte"}:
            widget = QSpinBox(); widget.setRange(0 if kind in {"alpha", "byte"} else -1_000_000, 255 if kind in {"alpha", "byte"} else 1_000_000); widget.setValue(int(value))
            widget.valueChanged.connect(lambda v, n=node, k=key: self.change_param(n, k, v)); return widget
        if kind in {"float", "float01"}:
            widget = QDoubleSpinBox(); widget.setDecimals(2); widget.setRange(0 if kind == "float01" else -1_000_000, 1 if kind == "float01" else 1_000_000); widget.setValue(float(value))
            widget.valueChanged.connect(lambda v, n=node, k=key: self.change_param(n, k, v)); return widget
        if kind == "bool":
            widget = QCheckBox(); widget.setChecked(bool(value)); widget.toggled.connect(lambda v, n=node, k=key: self.change_param(n, k, v)); return widget
        if kind == "mode":
            widget = QComboBox(); widget.addItems(MODE_NAMES); widget.setCurrentIndex(int(value)); widget.currentIndexChanged.connect(lambda v, n=node, k=key: self.change_param(n, k, v)); return widget
        if kind in {"object", "sprite", "arrow", "texture"}:
            if kind == "texture":
                widget = TextureResourcePicker(
                    self.texture_resources(), str(value),
                    document_background_color(self.document))
                widget.activated.connect(
                    lambda _index=0, n=node, k=key, w=widget:
                    self.change_param(n, k, w.resource_name()))
                return widget
            widget = QComboBox()
            choices = self.object_names(arrows_only=kind == "arrow", sprites_only=kind != "arrow")
            widget.addItems(choices)
            if str(value) in choices:
                widget.setCurrentText(str(value))
            else:
                widget.setCurrentIndex(-1)
                widget.setPlaceholderText(f"{value}（在此节点前不可用）" if value else "无可用对象")
            widget.currentTextChanged.connect(lambda v, n=node, k=key: self.change_param(n, k, v)); return widget
        if kind == "scene_color":
            widget = ColorValueEditor(str(value))
            widget.colorChanged.connect(lambda result, n=node, k=key: self.change_param(n, k, result))
            return widget
        if kind == "multiline":
            widget = QPlainTextEdit(str(value)); widget.setMinimumHeight(140); widget.textChanged.connect(lambda n=node, k=key, w=widget: self.change_param(n, k, w.toPlainText())); return widget
        if kind == "files":
            widget = MultiTextureFileEditor(
                self.mod_directory(), list(value) if isinstance(value, list) else [],
                document_background_color(self.document))
            widget.filesChanged.connect(
                lambda result, n=node, k=key: self.change_param(n, k, result))
            widget.choose_button.clicked.connect(
                lambda _=False, w=widget, n=node, k=key: self.choose_pngs(w, n, k))
            return widget
        if kind == "file":
            if node.get("type") == "load_texture":
                widget = TextureFileEditor(
                    self.mod_directory(), str(value),
                    document_background_color(self.document))
                widget.edit.editingFinished.connect(
                    lambda e=widget.edit, n=node, k=key: self.change_param(n, k, e.text()))
                widget.button.clicked.connect(
                    lambda _=False, e=widget.edit, n=node, k=key: self.choose_png(e, n, k))
                return widget
            container = QWidget(); layout = QHBoxLayout(container); layout.setContentsMargins(0, 0, 0, 0)
            edit = QLineEdit(str(value)); button = QPushButton("…"); button.setMaximumWidth(34)
            edit.textChanged.connect(lambda v, n=node, k=key: self.change_param(n, k, v)); button.clicked.connect(lambda _, e=edit, n=node, k=key: self.choose_png(e, n, k))
            layout.addWidget(edit); layout.addWidget(button); return container
        widget = QLineEdit(str(value)); widget.textChanged.connect(lambda v, n=node, k=key: self.change_param(n, k, v)); return widget

    def change_param(self, node: dict[str, Any], key: str, value: Any):
        if self.updating: return
        node["params"][key] = value; self.mark_dirty(); self.refresh_node_row(node); self.refresh_frame_column(); self.refresh_preview()

    def refresh_frame_column(self):
        for index, frame in enumerate(self.calculate_node_frames()):
            item = self.node_tree.topLevelItem(index)
            if item is not None:
                item.setText(1, str(frame))

    def refresh_node_row(self, node: dict[str, Any]):
        for i in range(self.node_tree.topLevelItemCount()):
            item = self.node_tree.topLevelItem(i)
            if item.data(0, Qt.ItemDataRole.UserRole) == node["id"]:
                item.setText(2, node_summary(node)); item.setText(3, node_lua(node).replace("\n", " ")[:180]); break

    def choose_png(self, edit: QLineEdit, node: dict[str, Any], key: str):
        mod_dir = self.mod_directory(); name, _ = QFileDialog.getOpenFileName(self, "选择 PNG", str(mod_dir), "PNG (*.png)")
        if not name: return
        source = Path(name); destination = mod_dir / source.name
        if source.resolve() != destination.resolve(): shutil.copy2(source, destination)
        edit.blockSignals(True); edit.setText(destination.name); edit.blockSignals(False)
        node["params"][key] = destination.name
        if node.get("type") == "load_texture" and key == "file":
            node["params"]["name"] = destination.stem
        self.mark_dirty(); self.refresh_all(node["id"])

    def choose_pngs(
        self, widget: MultiTextureFileEditor, node: dict[str, Any], key: str,
    ) -> None:
        mod_dir = self.mod_directory().resolve()
        names, _ = QFileDialog.getOpenFileNames(
            self, "选择模组内的 PNG", str(mod_dir), "PNG (*.png)")
        if not names:
            return
        existing = {
            str(entry["file"]).casefold(): entry for entry in texture_entries(node)
        }
        selected: list[dict[str, Any]] = []
        selected_keys: set[str] = set()
        rejected: list[str] = []
        for name in names:
            source = Path(name).resolve()
            try:
                relative = source.relative_to(mod_dir).as_posix()
            except ValueError:
                rejected.append(str(source))
                continue
            normalized = relative.casefold()
            if normalized not in selected_keys:
                previous = existing.get(normalized, {})
                selected.append({
                    "file": relative,
                    "anchor_x": previous.get("anchor_x", 0.5),
                    "anchor_y": previous.get("anchor_y", 0.5),
                })
                selected_keys.add(normalized)
        if rejected:
            QMessageBox.warning(
                self, "文件不在当前模组中",
                "批量资源加载不会复制文件。以下文件不在当前模组目录，已忽略：\n\n"
                + "\n".join(rejected))
        if not selected:
            return
        node["params"][key] = selected
        widget.set_files(selected)
        self.mark_dirty()
        self.refresh_all(node["id"])

    def scene_size(self) -> tuple[int, int]:
        for node in self.document["nodes"]:
            if node["type"] == "scene" and node.get("enabled", True): return int(node["params"]["logic_width"]), int(node["params"]["logic_height"])
        return 960, 540

    def object_names(self, arrows_only=False, sprites_only=False) -> list[str]:
        kind = "arrow" if arrows_only else "molecule"
        return [
            name for name, live_kind in live_objects_at(
                self.document, self.current_index() - 1).items()
            if live_kind == kind
        ]

    def texture_names(self) -> list[str]:
        return [
            str(entry["name"])
            for node in self.document["nodes"]
            if node.get("enabled", True)
            for entry in texture_entries(node)
        ]

    def texture_resources(self) -> list[dict[str, str]]:
        mod_dir = self.mod_directory()
        return [
            {
                "name": str(entry["name"]),
                "file": str(entry["file"]),
                "path": str((mod_dir / str(entry["file"])).resolve()),
            }
            for node in self.document.get("nodes", [])
            if node.get("enabled", True)
            for entry in texture_entries(node)
        ]

    def build_lua(self, include_disabled=False) -> str:
        blocks = []
        for node in self.document["nodes"]:
            if node.get("enabled", True): blocks.append(node_lua(node))
            elif include_disabled: blocks.append("-- [已禁用] " + node_lua(node).replace("\n", "\n-- "))
        return "\n\n".join(blocks).rstrip() + "\n"

    def refresh_preview(self):
        try: self.lua_preview.setPlainText(self.build_lua(include_disabled=True))
        except Exception as error: self.lua_preview.setPlainText(f"-- 生成错误：{error}")

    def mod_directory(self) -> Path:
        return MOD_ROOT / str(self.document.get("mod", "untitled"))

    def generate_lua(self, quiet=False) -> Path | None:
        try:
            if not self.save(): return None
            path = self.mod_directory() / "main.lua"; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(self.build_lua(), encoding="utf-8")
            self.statusBar().showMessage(f"已生成 {path}", 5000)
            if not quiet: QMessageBox.information(self, "生成成功", str(path))
            return path
        except Exception as error:
            QMessageBox.critical(self, "生成失败", str(error)); return None

    def render_mp4(self):
        if self.generate_lua(quiet=True) is None: return
        executable = ROOT / "build" / "release" / "chemanim.exe"
        if not executable.exists(): QMessageBox.warning(self, "未构建", "请先运行 build.ps1"); return
        subprocess.Popen([str(executable), str(self.document["mod"])], cwd=ROOT)
        self.statusBar().showMessage("已启动 MP4 渲染。", 5000)

    def closeEvent(self, event):
        event.accept() if self.maybe_discard() else event.ignore()


class CommitPlainTextEdit(QPlainTextEdit):
    editingFinished = pyqtSignal()

    def focusOutEvent(self, event) -> None:
        super().focusOutEvent(event)
        self.editingFinished.emit()


class LinearNodeTree(QTreeWidget):
    dropped = pyqtSignal()

    def dropEvent(self, event) -> None:
        super().dropEvent(event)
        if event.isAccepted():
            self.dropped.emit()


def preview_ease(mode: int, value: float) -> float:
    t = max(0.0, min(1.0, value))
    if mode == 1: return t * t
    if mode == 2: return t * t * t
    if mode == 3: return 1.0 - (1.0 - t) ** 2
    if mode == 4: return 1.0 - (1.0 - t) ** 3
    if mode == 5: return 2.0 * t * t if t < 0.5 else 1.0 - (-2.0 * t + 2.0) ** 2 / 2.0
    if mode == 6: return 4.0 * t ** 3 if t < 0.5 else 1.0 - (-2.0 * t + 2.0) ** 3 / 2.0
    return t


class SceneEvaluator:
    """Evaluate typed CMM nodes at a frame without running Lua."""

    SPRITE_DEFAULTS = {
        "x": 0.0, "y": 0.0, "scale_x": 1.0, "scale_y": 1.0,
        "rotation": 0.0, "alpha": 0.0, "anchor_x": -1.0,
        "anchor_y": -1.0, "layer": 0.0, "visible": 1.0,
        "r": 255.0, "g": 255.0, "b": 255.0,
    }
    ARROW_DEFAULTS = {
        **SPRITE_DEFAULTS, "alpha": 255.0, "r": 25.0, "g": 25.0, "b": 25.0,
        "thickness": 3.0, "progress": 0.0,
        "x1": 0.0, "y1": 0.0, "cx1": 0.0, "cy1": 0.0,
        "cx2": 0.0, "cy2": 0.0, "x2": 0.0, "y2": 0.0,
    }

    def __init__(self, document: dict[str, Any]):
        self.document = document
        self.cursor = 0
        self.order = 0
        self.objects: list[dict[str, Any]] = []
        self.current_objects: dict[str, dict[str, Any]] = {}
        self.textures: dict[str, dict[str, Any]] = {}
        self.scene = {
            "logic_width": 960, "logic_height": 540,
            "background": "FFFFFFFF",
        }
        self._compile()

    def _new_object(self, name: str, kind: str) -> None:
        if kind == "arrow":
            defaults = deepcopy(self.ARROW_DEFAULTS)
        else:
            defaults = deepcopy(self.SPRITE_DEFAULTS)
        obj = {
            "name": name, "kind": kind, "born": self.cursor, "dead": 2**31 - 1,
            "defaults": defaults, "tracks": {}, "strings": {}, "image_transitions": [],
        }
        if kind == "sprite":
            obj["string_defaults"] = {"texture": ""}
        else:
            obj["string_defaults"] = {}
        self.objects.append(obj)
        self.current_objects[name] = obj

    def _number_at(self, obj: dict[str, Any], key: str, frame: int) -> float:
        value = float(obj["defaults"].get(key, 0.0))
        segments = sorted(obj["tracks"].get(key, []), key=lambda item: (item["start"], item["order"]))
        for segment in segments:
            if frame < segment["start"]:
                continue
            if frame >= segment.get("cancel", 2**31 - 1):
                value = segment.get("cancel_value", segment["target"])
                continue
            if segment["duration"] <= 0 or frame >= segment["start"] + segment["duration"]:
                value = segment["target"]
            else:
                t = (frame - segment["start"]) / segment["duration"]
                t = preview_ease(segment["mode"], t)
                value = segment["from"] + (segment["target"] - segment["from"]) * t
        return value

    def _string_at(self, obj: dict[str, Any], key: str, frame: int) -> str:
        value = str(obj.get("string_defaults", {}).get(key, ""))
        for event in sorted(obj["strings"].get(key, []), key=lambda item: (item["frame"], item["order"])):
            if frame >= event["frame"]:
                value = event["value"]
        return value

    def _set_number(
        self, obj: dict[str, Any], key: str, target: Any,
        duration=0, mode=0, frame: int | None = None,
    ) -> int:
        start = self.cursor if frame is None else int(frame)
        current = self._number_at(obj, key, start)
        for segment in obj["tracks"].setdefault(key, []):
            effective_end = min(
                segment["start"] + segment["duration"],
                segment.get("cancel", 2**31 - 1),
            )
            if segment["start"] <= start < effective_end:
                segment["cancel"] = start
                segment["cancel_value"] = current
        self.order += 1
        obj["tracks"].setdefault(key, []).append({
            "start": start, "duration": max(0, int(duration)),
            "from": current, "target": float(target),
            "mode": int(mode), "order": self.order,
        })
        return self.order

    def _set_string(self, obj: dict[str, Any], key: str, value: Any, frame: int | None = None) -> int:
        self.order += 1
        obj["strings"].setdefault(key, []).append({
            "frame": self.cursor if frame is None else int(frame),
            "value": str(value), "order": self.order,
        })
        return self.order

    def _image_layers_at(self, obj: dict[str, Any], frame: int) -> list[dict[str, Any]]:
        active = None
        for transition in sorted(
            obj.get("image_transitions", []),
            key=lambda item: (item["start"], item["order"]),
        ):
            effective_end = min(transition["end"], transition.get("cancel", 2**31 - 1))
            if transition["start"] <= frame < effective_end:
                active = transition
        if active is not None:
            duration = max(1, active["end"] - active["start"])
            mix = preview_ease(active["mode"], (frame - active["start"]) / duration)
            layers = [
                {**layer, "alpha": float(layer.get("alpha", 1)) * (1 - mix)}
                for layer in active["from_layers"]
            ]
            layers.append({
                "texture": active["to"], "x": active["to_x"],
                "y": active["to_y"], "alpha": mix,
            })
            return layers
        texture = self._string_at(obj, "texture", frame)
        if not texture:
            return []
        return [{
            "texture": texture,
            "x": self._number_at(obj, "x", frame),
            "y": self._number_at(obj, "y", frame),
            "alpha": 1.0,
        }]

    def _object(self, params: dict[str, Any]) -> dict[str, Any] | None:
        return self.current_objects.get(str(params.get("object", "")))

    def _compile(self) -> None:
        for node in self.document.get("nodes", []):
            if not node.get("enabled", True):
                continue
            node_type, p = node["type"], node.get("params", {})
            if node_type == "scene":
                self.scene.update(p)
            elif node_type in {"load_texture", "load_textures"}:
                for entry in texture_entries(node):
                    self.textures[str(entry["name"])] = dict(entry)
            elif node_type == "wait":
                self.cursor += int(p["frames"])
            elif node_type == "new_object":
                self._new_object(str(p["name"]), "sprite")
            elif node_type == "new_arrow":
                self._new_object(str(p["name"]), "arrow")
            else:
                obj = self._object(p)
                if obj is None:
                    continue
                if node_type in {"delete", "delete_arrow"}:
                    obj["dead"] = min(obj["dead"], self.cursor)
                    name = str(p.get("object", ""))
                    if self.current_objects.get(name) is obj:
                        self.current_objects.pop(name, None)
                elif node_type == "set_image": self._set_string(obj, "texture", p["texture"])
                elif node_type == "change_image":
                    duration = max(0, int(p["frames"]))
                    target = str(p["texture"])
                    target_x = float(p.get("x", self._number_at(obj, "x", self.cursor)))
                    target_y = float(p.get("y", self._number_at(obj, "y", self.cursor)))
                    source_layers = self._image_layers_at(obj, self.cursor)
                    for transition in obj.get("image_transitions", []):
                        effective_end = min(
                            transition["end"], transition.get("cancel", 2**31 - 1))
                        if transition["start"] <= self.cursor < effective_end:
                            transition["cancel"] = self.cursor
                            completion_orders = {
                                transition.get("texture_completion"),
                                transition.get("x_completion"),
                                transition.get("y_completion"),
                            }
                            for events in obj["strings"].values():
                                events[:] = [event for event in events if event["order"] not in completion_orders]
                            for segments in obj["tracks"].values():
                                segments[:] = [segment for segment in segments if segment["order"] not in completion_orders]
                    if duration == 0 or not source_layers:
                        self._set_string(obj, "texture", target)
                        self._set_number(obj, "x", target_x)
                        self._set_number(obj, "y", target_y)
                    else:
                        self.order += 1
                        transition = {
                            "start": self.cursor, "end": self.cursor + duration,
                            "from_layers": source_layers, "to": target,
                            "to_x": target_x, "to_y": target_y, "mode": int(p["mode"]),
                            "order": self.order,
                        }
                        transition["texture_completion"] = self._set_string(
                            obj, "texture", target, self.cursor + duration)
                        transition["x_completion"] = self._set_number(
                            obj, "x", target_x, frame=self.cursor + duration)
                        transition["y_completion"] = self._set_number(
                            obj, "y", target_y, frame=self.cursor + duration)
                        obj["image_transitions"].append(transition)
                elif node_type == "set_pos":
                    self._set_number(obj, "x", p["x"]); self._set_number(obj, "y", p["y"])
                elif node_type == "set_pos_x": self._set_number(obj, "x", p["value"])
                elif node_type == "set_pos_y": self._set_number(obj, "y", p["value"])
                elif node_type == "set_alpha": self._set_number(obj, "alpha", p["value"])
                elif node_type == "mol_color":
                    for key in ("r", "g", "b"): self._set_number(obj, key, p[key])
                elif node_type == "set_scale":
                    self._set_number(obj, "scale_x", p["x"]); self._set_number(obj, "scale_y", p["y"])
                elif node_type == "set_scale_x": self._set_number(obj, "scale_x", p["value"])
                elif node_type == "set_scale_y": self._set_number(obj, "scale_y", p["value"])
                elif node_type == "set_rotation": self._set_number(obj, "rotation", p["value"])
                elif node_type == "set_layer": self._set_number(obj, "layer", p["value"])
                elif node_type == "set_visible": self._set_number(obj, "visible", 1 if p["value"] else 0)
                elif node_type == "set_anchor":
                    self._set_number(obj, "anchor_x", p["x"]); self._set_number(obj, "anchor_y", p["y"])
                elif node_type == "lerp_pos":
                    self._set_number(obj, "x", p["x"], p["frames"], p["mode"])
                    self._set_number(obj, "y", p["y"], p["frames"], p["mode"])
                elif node_type == "lerp_pos_x": self._set_number(obj, "x", p["value"], p["frames"], p["mode"])
                elif node_type == "lerp_pos_y": self._set_number(obj, "y", p["value"], p["frames"], p["mode"])
                elif node_type in {"lerp_alpha", "lerp_arrow_alpha"}: self._set_number(obj, "alpha", p["value"], p["frames"], p["mode"])
                elif node_type == "lerp_scale":
                    self._set_number(obj, "scale_x", p["x"], p["frames"], p["mode"])
                    self._set_number(obj, "scale_y", p["y"], p["frames"], p["mode"])
                elif node_type == "lerp_scale_x": self._set_number(obj, "scale_x", p["value"], p["frames"], p["mode"])
                elif node_type == "lerp_scale_y": self._set_number(obj, "scale_y", p["value"], p["frames"], p["mode"])
                elif node_type == "lerp_rotation": self._set_number(obj, "rotation", p["value"], p["frames"], p["mode"])
                elif node_type == "lerp_mol_color":
                    for key in ("r", "g", "b"): self._set_number(obj, key, p[key], p["frames"], p["mode"])
                elif node_type == "arrow_curve":
                    if not p.get("initialized", True):
                        continue
                    for key in ("x1", "y1", "cx1", "cy1", "cx2", "cy2", "x2", "y2"):
                        self._set_number(obj, key, p[key])
                elif node_type == "arrow_color":
                    for key in ("r", "g", "b"): self._set_number(obj, key, p[key])
                    self._set_number(obj, "alpha", p["a"])
                elif node_type == "arrow_set_pos":
                    self._set_number(obj, "x", p["x"]); self._set_number(obj, "y", p["y"])
                elif node_type == "arrow_lerp_pos":
                    self._set_number(obj, "x", p["x"], p["frames"], p["mode"])
                    self._set_number(obj, "y", p["y"], p["frames"], p["mode"])
                elif node_type == "lerp_arrow_color":
                    for key in ("r", "g", "b"): self._set_number(obj, key, p[key], p["frames"], p["mode"])
                elif node_type == "arrow_width": self._set_number(obj, "thickness", p["value"])
                elif node_type == "arrow_progress": self._set_number(obj, "progress", p["value"])
                elif node_type == "lerp_arrow": self._set_number(obj, "progress", p["value"], p["frames"], p["mode"])

    def evaluate(self, frame: int) -> list[dict[str, Any]]:
        result = []
        for obj in self.objects:
            if frame < obj["born"] or frame >= obj["dead"]:
                continue
            state = {"name": obj["name"], "kind": obj["kind"]}
            for key in obj["defaults"]:
                state[key] = self._number_at(obj, key, frame)
            for key in obj.get("string_defaults", {}):
                state[key] = self._string_at(obj, key, frame)
            active_transition = None
            for transition in sorted(obj.get("image_transitions", []), key=lambda item: (item["start"], item["order"])):
                effective_end = min(
                    transition["end"], transition.get("cancel", 2**31 - 1))
                if transition["start"] <= frame < effective_end:
                    active_transition = transition
            if active_transition is not None:
                state["_image_layers"] = self._image_layers_at(obj, frame)
            result.append(state)
        return sorted(result, key=lambda state: state.get("layer", 0))


def sprite_position_through(
    document: dict[str, Any], through_index: int, object_name: str,
) -> tuple[float, float]:
    """Evaluate a sprite position using only nodes through an insertion point."""
    partial = {**document, "nodes": deepcopy(document.get("nodes", [])[:through_index + 1])}
    evaluator = SceneEvaluator(partial)
    states = evaluator.evaluate(evaluator.cursor)
    for state in reversed(states):
        if state.get("kind") == "sprite" and state.get("name") == object_name:
            return float(state.get("x", 0)), float(state.get("y", 0))
    return 0.0, 0.0


class CanvasView(QGraphicsView):
    def __init__(self, scene: QGraphicsScene, parent=None):
        super().__init__(scene, parent)
        self.zoom = 1.0
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setBackgroundBrush(QColor("#25282e"))
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.priority_drag_item = None
        self.active_drag_item = None
        self.drag_scene_start = QPointF()
        self.drag_item_start = QPointF()
        self.arrow_draw_callback = None
        self.arrow_draw_start: QPointF | None = None
        self.arrow_draw_current: QPointF | None = None
        self.arrow_curve_wheel_callback = None

    def set_arrow_draw_callback(self, callback) -> None:
        self.arrow_draw_callback = callback
        self.arrow_draw_start = None
        self.arrow_draw_current = None
        self.setCursor(
            Qt.CursorShape.CrossCursor if callback is not None
            else Qt.CursorShape.ArrowCursor)

    def set_arrow_curve_wheel_callback(self, callback) -> None:
        self.arrow_curve_wheel_callback = callback

    def set_priority_drag_item(self, item) -> None:
        self.priority_drag_item = item
        self.active_drag_item = None

    def mousePressEvent(self, event) -> None:
        scene_position = self.mapToScene(event.position().toPoint())
        if event.button() == Qt.MouseButton.LeftButton and self.arrow_draw_callback is not None:
            self.arrow_draw_start = scene_position
            self.arrow_draw_current = scene_position
            self.arrow_draw_callback(scene_position, scene_position, False)
            event.accept()
            return
        item = self.priority_drag_item
        if (
            event.button() == Qt.MouseButton.LeftButton
            and item is not None
            and item.sceneBoundingRect().contains(scene_position)
        ):
            self.active_drag_item = item
            self.drag_scene_start = scene_position
            self.drag_item_start = QPointF(item.pos())
            item.begin_external_drag()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self.arrow_draw_start is not None and self.arrow_draw_callback is not None:
            self.arrow_draw_current = self.mapToScene(event.position().toPoint())
            self.arrow_draw_callback(
                self.arrow_draw_start,
                self.arrow_draw_current, False)
            event.accept()
            return
        if self.active_drag_item is not None:
            scene_position = self.mapToScene(event.position().toPoint())
            self.active_drag_item.setPos(
                self.drag_item_start + scene_position - self.drag_scene_start)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self.arrow_draw_start is not None and self.arrow_draw_callback is not None:
            start = self.arrow_draw_start
            end = self.mapToScene(event.position().toPoint())
            self.arrow_draw_start = None
            self.arrow_draw_current = None
            self.arrow_draw_callback(start, end, True)
            event.accept()
            return
        if self.active_drag_item is not None:
            item = self.active_drag_item
            self.active_drag_item = None
            item.finish_external_drag()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def fit_canvas(self) -> None:
        self.zoom = 1.0
        self.fitInView(self.scene().sceneRect().adjusted(-12, -12, 12, 12), Qt.AspectRatioMode.KeepAspectRatio)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if abs(self.zoom - 1.0) < 0.001:
            self.fit_canvas()

    def wheelEvent(self, event) -> None:
        delta = event.angleDelta().y() or event.pixelDelta().y()
        if self.arrow_curve_wheel_callback is not None and delta:
            self.arrow_curve_wheel_callback(1 if delta > 0 else -1)
            # While the initial arrow gesture is held, redraw the draft at the
            # same endpoint immediately with the newly selected bend level.
            if (
                self.arrow_draw_start is not None
                and self.arrow_draw_current is not None
                and self.arrow_draw_callback is not None
            ):
                self.arrow_draw_callback(
                    self.arrow_draw_start, self.arrow_draw_current, False)
            event.accept()
            return
        factor = 1.15 if delta > 0 else 1 / 1.15
        next_zoom = max(0.25, min(8.0, self.zoom * factor))
        factor = next_zoom / self.zoom
        self.zoom = next_zoom
        self.scale(factor, factor)


class DragHandle(QGraphicsEllipseItem):
    def __init__(self, key: str, position: QPointF, color: QColor, callback):
        super().__init__(-6, -6, 12, 12)
        self.key = key
        self.callback = callback
        self.ready = False
        self.setBrush(color)
        self.setPen(QPen(QColor("white"), 1.5))
        self.setZValue(10000)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
            | QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations
        )
        self.setPos(position)
        self.ready = True

    def itemChange(self, change, value):
        result = super().itemChange(change, value)
        if self.ready and change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.callback(self.key, self.pos(), False)
        return result

    def mouseReleaseEvent(self, event) -> None:
        super().mouseReleaseEvent(event)
        self.callback(self.key, self.pos(), True)


class MovableSpriteItem(QGraphicsPixmapItem):
    def __init__(self, name: str, callback, click_callback):
        super().__init__()
        self.name = name
        self.callback = callback
        self.click_callback = click_callback
        self.ready = False
        self.movement_axis = "both"
        self.locked_position = QPointF()
        self.press_position: QPointF | None = None
        self.dragged = False
        # Chemical structure PNGs contain large transparent regions.  Requiring
        # a click on a one-pixel bond makes dragging feel random, so use the
        # visible texture's full bounds as its interaction target.
        self.setShapeMode(QGraphicsPixmapItem.ShapeMode.BoundingRectShape)
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def set_movement_axis(self, axis: str) -> None:
        self.movement_axis = axis
        self.locked_position = QPointF(self.pos())

    def begin_external_drag(self) -> None:
        self.press_position = QPointF(self.pos())
        self.dragged = False
        self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def finish_external_drag(self) -> None:
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        if self.ready and self.dragged:
            self.callback(self.name, self.pos(), True)
        elif self.ready:
            self.click_callback(self.name)
        self.press_position = None

    def mousePressEvent(self, event) -> None:
        self.begin_external_drag()
        super().mousePressEvent(event)

    def itemChange(self, change, value):
        if self.ready and change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            position = QPointF(value)
            if self.movement_axis == "x":
                return QPointF(position.x(), self.locked_position.y())
            if self.movement_axis == "y":
                return QPointF(self.locked_position.x(), position.y())
        result = super().itemChange(change, value)
        if self.ready and change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            if self.press_position is not None:
                delta = self.pos() - self.press_position
                self.dragged = self.dragged or abs(delta.x()) + abs(delta.y()) >= 0.25
            self.callback(self.name, self.pos(), False)
        return result

    def mouseReleaseEvent(self, event) -> None:
        super().mouseReleaseEvent(event)
        self.finish_external_drag()


class SceneCanvas(QWidget):
    objectPositionCommitted = pyqtSignal(str, float, float)
    objectClicked = pyqtSignal(str)
    arrowCurveDrawn = pyqtSignal(str, float, float, float, float, float, float, float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.graphics_scene = QGraphicsScene()
        self.view = CanvasView(self.graphics_scene)
        self.sprite_items: dict[str, MovableSpriteItem] = {}
        self.sprite_companions: dict[str, list[MovableSpriteItem]] = {}
        self.sprite_states: dict[str, dict[str, Any]] = {}
        self.arrow_visuals: list[dict[str, Any]] = []
        self.handles: dict[str, DragHandle] = {}
        self.handle_lines: list[QGraphicsLineItem] = []
        self.selected_node: dict[str, Any] | None = None
        self._adjusting_handles = False
        self._canvas_size: tuple[int, int] | None = None
        self._pixmap_cache: dict[str, QPixmap] = {}
        self._tinted_pixmap_cache: dict[tuple[str, int, int, int], QPixmap] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(self.view, 1)
        self.draw_hint = QLabel("在画布中按住鼠标左键，从箭头起点拖到终点；滚轮粗调凹凸方向")
        self.draw_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.draw_hint.setStyleSheet("padding: 6px; color: #f8fafc; background: #9d174d; font-weight: 600;")
        self.draw_hint.hide()
        layout.addWidget(self.draw_hint)
        controls = QHBoxLayout()
        controls.addWidget(QLabel("预览帧"))
        self.frame_slider = QSlider(Qt.Orientation.Horizontal)
        self.frame_spin = QSpinBox()
        self.frame_spin.setRange(0, 1_000_000)
        self.play_button = QPushButton("▶ 播放")
        self.fit_button = QPushButton("适合画布")
        controls.addWidget(self.frame_slider, 1)
        controls.addWidget(self.frame_spin)
        controls.addWidget(self.play_button)
        controls.addWidget(self.fit_button)
        layout.addLayout(controls)
        self.fit_button.clicked.connect(self.view.fit_canvas)

    @staticmethod
    def _background_color(value: str) -> QColor:
        parsed = parse_color_text(str(value))
        if parsed is not None:
            return parsed[0]
        return QColor("white")

    def render_document(self, document: dict[str, Any], frame: int, selected_node: dict[str, Any] | None, mod_dir: Path) -> None:
        evaluator = SceneEvaluator(document)
        selected_type = selected_node.get("type") if selected_node else ""
        alignment_mode = selected_type == "change_image"
        display_frame = frame
        if alignment_mode and selected_node is not None:
            cursor = 0
            for node in document.get("nodes", []):
                if node.get("id") == selected_node.get("id"):
                    display_frame = cursor
                    break
                if node.get("enabled", True) and node.get("type") == "wait":
                    cursor += int(node.get("params", {}).get("frames", 0))
        states = evaluator.evaluate(display_frame)
        scene_info = evaluator.scene
        width = max(1, int(scene_info.get("logic_width", 960)))
        height = max(1, int(scene_info.get("logic_height", 540)))
        self.selected_node = selected_node
        self.view.set_arrow_draw_callback(None)
        self.view.set_arrow_curve_wheel_callback(None)
        self.view.set_priority_drag_item(None)
        self.graphics_scene.clear()
        self._draft_arrow_path = None
        self._draft_arrow_head = None
        self._draft_bend_level = 1.0
        self.move_companions_with_primary = not alignment_mode
        self.sprite_items.clear(); self.sprite_companions.clear(); self.sprite_states.clear(); self.arrow_visuals.clear()
        self.handles.clear(); self.handle_lines.clear()
        self.graphics_scene.setSceneRect(-width / 2, -height / 2, width, height)
        self.graphics_scene.addRect(
            self.graphics_scene.sceneRect(), QPen(Qt.PenStyle.NoPen),
            QBrush(self._background_color(scene_info.get("background", "FFFFFFFF")))
        ).setZValue(-10000)
        grid_pen = QPen(QColor(150, 150, 150, 70), 0)
        for index in range(1, 10):
            x = -width / 2 + width * index / 10
            y = -height / 2 + height * index / 10
            self.graphics_scene.addLine(x, -height / 2, x, height / 2, grid_pen).setZValue(-9999)
            self.graphics_scene.addLine(-width / 2, y, width / 2, y, grid_pen).setZValue(-9999)
        axis_pen = QPen(QColor(50, 120, 210, 150), 0)
        self.graphics_scene.addLine(-width / 2, 0, width / 2, 0, axis_pen).setZValue(-9998)
        self.graphics_scene.addLine(0, -height / 2, 0, height / 2, axis_pen).setZValue(-9998)

        selected_movable = ""
        selected_axis = "both"
        priority_drag_item = None
        if selected_node and selected_type in POSITION_NODE_AXES:
            selected_movable = str(selected_node["params"].get("object", ""))
            selected_axis = POSITION_NODE_AXES[selected_type]
        elif alignment_mode and selected_node is not None:
            selected_movable = str(selected_node["params"].get("object", ""))
        for state in states:
            if state["kind"] != "sprite" or state.get("visible", 1) <= 0:
                continue
            self.sprite_states[state["name"]] = state
            if alignment_mode and state["name"] == selected_movable and selected_node is not None:
                target_texture = str(selected_node.get("params", {}).get("texture", ""))
                layers = [
                    (str(state.get("texture", "")), 0.38, False,
                     float(state.get("x", 0)), float(state.get("y", 0))),
                    (target_texture, 0.72, True,
                     float(selected_node.get("params", {}).get("x", state.get("x", 0))),
                     float(selected_node.get("params", {}).get("y", state.get("y", 0)))),
                ]
            elif "_image_layers" in state:
                image_layers = list(state.get("_image_layers", []))
                primary_index = max(
                    range(len(image_layers)),
                    key=lambda index: float(image_layers[index].get("alpha", 0)),
                    default=-1,
                )
                layers = [
                    (str(layer.get("texture", "")), float(layer.get("alpha", 0)),
                     index == primary_index, float(layer.get("x", state.get("x", 0))),
                     float(layer.get("y", state.get("y", 0))))
                    for index, layer in enumerate(image_layers)
                ]
            else:
                layers = [(
                    str(state.get("texture", "")), 1.0, True,
                    float(state.get("x", 0)), float(state.get("y", 0)),
                )]
            object_alpha = max(0.0, min(1.0, float(state.get("alpha", 255)) / 255.0))
            for texture_name, blend_alpha, primary, layer_x, layer_y in layers:
                texture = evaluator.textures.get(texture_name)
                if not texture:
                    continue
                texture_path = str((mod_dir / str(texture.get("file", ""))).resolve())
                pixmap = self._pixmap_cache.get(texture_path)
                if pixmap is None:
                    pixmap = QPixmap(texture_path)
                    self._pixmap_cache[texture_path] = pixmap
                if pixmap.isNull():
                    continue
                tint = tuple(int(max(0, min(255, state.get(key, 255)))) for key in ("r", "g", "b"))
                if tint != (255, 255, 255):
                    tint_key = (texture_path, *tint)
                    tinted = self._tinted_pixmap_cache.get(tint_key)
                    if tinted is None:
                        tinted = QPixmap(pixmap.size())
                        tinted.fill(Qt.GlobalColor.transparent)
                        painter = QPainter(tinted)
                        painter.drawPixmap(0, 0, pixmap)
                        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Multiply)
                        painter.fillRect(tinted.rect(), QColor(*tint))
                        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
                        painter.drawPixmap(0, 0, pixmap)
                        painter.end()
                        self._tinted_pixmap_cache[tint_key] = tinted
                    pixmap = tinted
                anchor_x = state.get("anchor_x", -1)
                anchor_y = state.get("anchor_y", -1)
                if anchor_x < 0: anchor_x = float(texture.get("anchor_x", 0.5))
                if anchor_y < 0: anchor_y = float(texture.get("anchor_y", 0.5))
                item = MovableSpriteItem(state["name"], self._sprite_moved, self.objectClicked.emit)
                item.setPixmap(pixmap)
                item.setOffset(-anchor_x * pixmap.width(), -(1.0 - anchor_y) * pixmap.height())
                item.setTransform(QTransform().scale(float(state.get("scale_x", 1)), float(state.get("scale_y", 1))))
                item.setRotation(float(state.get("rotation", 0)))
                opacity = object_alpha * blend_alpha
                if alignment_mode and state["name"] != selected_movable:
                    opacity *= 0.38
                if primary and state["name"] == selected_movable:
                    opacity = max(0.25, opacity)
                item.setOpacity(opacity)
                item.setZValue(float(state.get("layer", 0)))
                item.setPos(layer_x, -layer_y)
                position_editable = primary and state["name"] == selected_movable
                if position_editable:
                    item.setFlags(
                        QGraphicsItem.GraphicsItemFlag.ItemIsMovable
                        | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
                        | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
                    )
                    item.set_movement_axis(selected_axis)
                else:
                    item.setCursor(Qt.CursorShape.ArrowCursor)
                    # Outside the position node bound to this object, sprites
                    # are preview-only. They must not steal drags while arrow
                    # handles or the canvas itself are being edited.
                    item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
                if position_editable:
                    item.setSelected(True)
                    priority_drag_item = item
                item.ready = primary
                self.graphics_scene.addItem(item)
                if primary:
                    self.sprite_items[state["name"]] = item
                else:
                    self.sprite_companions.setdefault(state["name"], []).append(item)

        self.view.set_priority_drag_item(priority_drag_item)

        for state in states:
            if state["kind"] == "arrow" and state.get("visible", 1) > 0:
                self._add_arrow(state, selected_node)
        drawing_node = (
            selected_node is not None
            and selected_node.get("type") == "arrow_curve"
            and not selected_node.get("params", {}).get("initialized", True)
        )
        curve_edit_node = (
            selected_node is not None
            and selected_node.get("type") == "arrow_curve"
        )
        self.draw_hint.setVisible(curve_edit_node)
        self.draw_hint.setVisible(curve_edit_node or alignment_mode)
        if alignment_mode:
            self.draw_hint.setText("洋葱皮对齐：旧帧为半透明参考；拖动新贴图到重合位置，松开鼠标后写入目标坐标")
            self.draw_hint.setStyleSheet(
                "padding: 6px; color: #f8fafc; background: #0f766e; font-weight: 600;")
        else:
            self.draw_hint.setText(
                "在画布中按住鼠标左键，从箭头起点拖到终点；滚轮粗调凹凸方向"
                if drawing_node else
                "拖动四个控制点精调曲线；滚轮粗调凹凸方向"
            )
            self.draw_hint.setStyleSheet(
                "padding: 6px; color: #f8fafc; background: #9d174d; font-weight: 600;")
        if curve_edit_node:
            self.view.set_arrow_curve_wheel_callback(self._wheel_adjust_arrow_curve)
        if drawing_node:
            self.view.set_arrow_draw_callback(self._draw_arrow_gesture)
        canvas_size = (width, height)
        if self._canvas_size != canvas_size:
            self._canvas_size = canvas_size
            self.view.fit_canvas()

    def _sprite_center(self, name: str) -> QPointF:
        item = self.sprite_items.get(name)
        if item is not None:
            return item.mapToScene(item.boundingRect().center())
        state = self.sprite_states.get(name, {})
        return QPointF(float(state.get("x", 0)), -float(state.get("y", 0)))

    @staticmethod
    def _cubic(p0: QPointF, p1: QPointF, p2: QPointF, p3: QPointF, t: float) -> QPointF:
        u = 1.0 - t
        return QPointF(
            u**3*p0.x() + 3*u*u*t*p1.x() + 3*u*t*t*p2.x() + t**3*p3.x(),
            u**3*p0.y() + 3*u*u*t*p1.y() + 3*u*t*t*p2.y() + t**3*p3.y(),
        )

    def _arrow_points(self, state: dict[str, Any]) -> tuple[QPointF, QPointF, QPointF, QPointF]:
        offset = QPointF(float(state.get("x", 0)), -float(state.get("y", 0)))
        scale_x = float(state.get("scale_x", 1))
        scale_y = float(state.get("scale_y", 1))
        return (
            offset + QPointF(state.get("x1", 0) * scale_x, -state.get("y1", 0) * scale_y),
            offset + QPointF(state.get("cx1", 0) * scale_x, -state.get("cy1", 0) * scale_y),
            offset + QPointF(state.get("cx2", 0) * scale_x, -state.get("cy2", 0) * scale_y),
            offset + QPointF(state.get("x2", 0) * scale_x, -state.get("y2", 0) * scale_y),
        )

    def _add_arrow(self, state: dict[str, Any], selected_node: dict[str, Any] | None) -> None:
        p0, p1, p2, p3 = self._arrow_points(state)
        color = QColor(int(state.get("r", 25)), int(state.get("g", 25)), int(state.get("b", 25)))
        color.setAlpha(int(max(0, min(255, state.get("alpha", 255)))))
        path_item = QGraphicsPathItem()
        path_item.setPen(QPen(color, max(0.5, float(state.get("thickness", 3))), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        path_item.setZValue(float(state.get("layer", 0)))
        path_item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.graphics_scene.addItem(path_item)
        head_item = QGraphicsPolygonItem()
        head_item.setBrush(color); head_item.setPen(QPen(Qt.PenStyle.NoPen)); head_item.setZValue(path_item.zValue())
        head_item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.graphics_scene.addItem(head_item)
        visual = {"state": state, "path": path_item, "head": head_item}
        self.arrow_visuals.append(visual)
        self._update_arrow_visual(visual)

        selected = (
            selected_node is not None
            and selected_node.get("type") == "arrow_curve"
            and (
                selected_node.get("type") != "arrow_curve"
                or selected_node.get("params", {}).get("initialized", True)
            )
            and str(selected_node.get("params", {}).get("object", "")) == state["name"]
        )
        if selected:
            guide = QGraphicsPathItem()
            full = QPainterPath(p0); full.cubicTo(p1, p2, p3)
            guide.setPath(full); guide.setPen(QPen(QColor(40, 120, 220, 150), 1.2, Qt.PenStyle.DashLine)); guide.setZValue(9990)
            guide.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
            self.graphics_scene.addItem(guide)
            visual["guide"] = guide
            for start, end in ((p0, p1), (p3, p2)):
                line = self.graphics_scene.addLine(start.x(), start.y(), end.x(), end.y(), QPen(QColor(230, 140, 40, 190), 1, Qt.PenStyle.DashLine))
                line.setZValue(9991); self.handle_lines.append(line)
            colors = {"start": QColor("#1976d2"), "end": QColor("#d32f2f"), "control1": QColor("#f57c00"), "control2": QColor("#f57c00")}
            for key, point in (("start", p0), ("control1", p1), ("control2", p2), ("end", p3)):
                handle = DragHandle(key, point, colors[key], self._handle_moved)
                self.graphics_scene.addItem(handle); self.handles[key] = handle
            self._last_start = p0
            self._last_end = p3

    def _arrow_shape(
        self, p0: QPointF, p1: QPointF, p2: QPointF, p3: QPointF,
        progress: float, head_length: float, head_width: float,
    ) -> tuple[QPainterPath, QPolygonF]:
        progress = max(0.0, min(1.0, progress))
        path = QPainterPath(p0)
        if progress <= 0:
            return path, QPolygonF()
        samples = 192
        points = [self._cubic(p0, p1, p2, p3, index / samples) for index in range(samples + 1)]
        cumulative = [0.0]
        for index in range(1, len(points)):
            dx = points[index].x() - points[index - 1].x()
            dy = points[index].y() - points[index - 1].y()
            cumulative.append(cumulative[-1] + (dx * dx + dy * dy) ** 0.5)

        def through_length(target: float) -> list[QPointF]:
            result = [points[0]]
            for index in range(1, len(points)):
                if cumulative[index] <= target:
                    result.append(points[index])
                    continue
                segment = cumulative[index] - cumulative[index - 1]
                if target > cumulative[index - 1] and segment > 0:
                    local = (target - cumulative[index - 1]) / segment
                    a, b = points[index - 1], points[index]
                    result.append(QPointF(a.x() + (b.x() - a.x()) * local, a.y() + (b.y() - a.y()) * local))
                break
            return result

        target_length = cumulative[-1] * progress
        tip_points = through_length(target_length)
        if len(tip_points) < 2:
            return path, QPolygonF()
        tip = tip_points[-1]
        shaft_points = through_length(max(0.0, target_length - head_length))
        base = shaft_points[-1]
        for point in shaft_points[1:]:
            path.lineTo(point)
        dx, dy = tip.x() - base.x(), tip.y() - base.y()
        axis_length = max(0.001, (dx * dx + dy * dy) ** 0.5)
        ux, uy = dx / axis_length, dy / axis_length
        width_scale = min(1.0, axis_length / max(1.0, head_length))
        normal = QPointF(-uy * head_width * width_scale * 0.5, ux * head_width * width_scale * 0.5)
        return path, QPolygonF([tip, base + normal, base - normal])

    def _update_arrow_visual(self, visual: dict[str, Any]) -> None:
        state = visual["state"]
        p0, p1, p2, p3 = self._arrow_points(state)
        path, head = self._arrow_shape(
            p0, p1, p2, p3,
            float(state.get("progress", 0)),
            max(0.1, float(state.get("thickness", 3))) * (20.0 / 3.0),
            max(0.1, float(state.get("thickness", 3))) * 5.0,
        )
        visual["path"].setPath(path)
        visual["head"].setPolygon(head)

    def _sprite_moved(self, name: str, position: QPointF, final: bool) -> None:
        if getattr(self, "move_companions_with_primary", True):
            for companion in self.sprite_companions.get(name, []):
                companion.setPos(position)
        for visual in self.arrow_visuals:
            self._update_arrow_visual(visual)
        if final:
            self.objectPositionCommitted.emit(name, position.x(), -position.y())

    @staticmethod
    def _gesture_curve_points(
        start: QPointF, end: QPointF, bend_level: float,
    ) -> tuple[QPointF, QPointF, QPointF, QPointF]:
        delta = end - start
        length = max(0.001, (delta.x() ** 2 + delta.y() ** 2) ** 0.5)
        normal = QPointF(delta.y() / length, -delta.x() / length)
        bend = min(70.0, max(18.0, length * 0.18)) * bend_level
        return (
            start,
            start + delta / 3.0 + normal * bend,
            start + delta * (2.0 / 3.0) + normal * bend,
            end,
        )

    @staticmethod
    def _coarse_bend_control_points(
        p0: QPointF, p1: QPointF, p2: QPointF, p3: QPointF, direction: int,
    ) -> tuple[QPointF, QPointF]:
        delta = p3 - p0
        length = max(0.001, (delta.x() ** 2 + delta.y() ** 2) ** 0.5)
        normal = QPointF(delta.y() / length, -delta.x() / length)
        step = min(70.0, max(18.0, length * 0.18)) * (1 if direction > 0 else -1)
        shift = normal * step
        return p1 + shift, p2 + shift

    def _wheel_adjust_arrow_curve(self, direction: int) -> None:
        if not self.handles:
            self._draft_bend_level = max(
                -5.0, min(5.0, self._draft_bend_level + (1 if direction > 0 else -1)))
            return
        required = {"start", "control1", "control2", "end"}
        if not required.issubset(self.handles):
            return
        p0 = self.handles["start"].pos()
        p1 = self.handles["control1"].pos()
        p2 = self.handles["control2"].pos()
        p3 = self.handles["end"].pos()
        p1, p2 = self._coarse_bend_control_points(
            p0, p1, p2, p3, direction)
        self._adjusting_handles = True
        try:
            self.handles["control1"].setPos(p1)
            self.handles["control2"].setPos(p2)
        finally:
            self._adjusting_handles = False
        # Reuse the regular handle path so the guide, rendered arrow, CMM
        # parameters and undo history are updated as one edit.
        self._handle_moved("control1", p1, True)

    def _draw_arrow_gesture(self, start: QPointF, end: QPointF, final: bool) -> None:
        p0, p1, p2, p3 = self._gesture_curve_points(
            start, end, self._draft_bend_level)
        delta = end - start
        length = max(0.001, (delta.x() ** 2 + delta.y() ** 2) ** 0.5)
        if self._draft_arrow_path is None:
            self._draft_arrow_path = QGraphicsPathItem()
            self._draft_arrow_path.setPen(QPen(
                QColor(25, 25, 25), 3.0, Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            self._draft_arrow_path.setZValue(10020)
            self.graphics_scene.addItem(self._draft_arrow_path)
            self._draft_arrow_head = QGraphicsPolygonItem()
            self._draft_arrow_head.setBrush(QColor(25, 25, 25))
            self._draft_arrow_head.setPen(QPen(Qt.PenStyle.NoPen))
            self._draft_arrow_head.setZValue(10021)
            self.graphics_scene.addItem(self._draft_arrow_head)
        path, head = self._arrow_shape(p0, p1, p2, p3, 1.0, 20.0, 15.0)
        self._draft_arrow_path.setPath(path)
        self._draft_arrow_head.setPolygon(head)
        if final and length >= 4 and self.selected_node is not None:
            params = self.selected_node.get("params", {})
            state = next((
                visual["state"] for visual in self.arrow_visuals
                if visual["state"]["name"] == str(params.get("object", ""))
            ), {})
            offset = QPointF(float(state.get("x", 0)), -float(state.get("y", 0)))
            scale_x = float(state.get("scale_x", 1)) or 1.0
            scale_y = float(state.get("scale_y", 1)) or 1.0
            def raw(point: QPointF) -> tuple[float, float]:
                return ((point.x() - offset.x()) / scale_x,
                        -(point.y() - offset.y()) / scale_y)
            a0, a1, a2, a3 = raw(p0), raw(p1), raw(p2), raw(p3)
            self.arrowCurveDrawn.emit(
                str(self.selected_node["id"]),
                a0[0], a0[1], a1[0], a1[1],
                a2[0], a2[1], a3[0], a3[1])

    def _handle_moved(self, key: str, position: QPointF, final: bool) -> None:
        if self._adjusting_handles or not self.handles:
            return
        self._adjusting_handles = True
        try:
            if key == "start" and "control1" in self.handles:
                old = getattr(self, "_last_start", position)
                self.handles["control1"].setPos(self.handles["control1"].pos() + position - old)
                self._last_start = position
            elif key == "end" and "control2" in self.handles:
                old = getattr(self, "_last_end", position)
                self.handles["control2"].setPos(self.handles["control2"].pos() + position - old)
                self._last_end = position
            p0 = self.handles["start"].pos(); p1 = self.handles["control1"].pos()
            p2 = self.handles["control2"].pos(); p3 = self.handles["end"].pos()
            if self.handle_lines:
                self.handle_lines[0].setLine(p0.x(), p0.y(), p1.x(), p1.y())
                self.handle_lines[1].setLine(p3.x(), p3.y(), p2.x(), p2.y())
            for visual in self.arrow_visuals:
                if "guide" in visual:
                    path = QPainterPath(p0); path.cubicTo(p1, p2, p3); visual["guide"].setPath(path)
                    state = visual["state"]
                    arrow_path, head = self._arrow_shape(
                        p0, p1, p2, p3,
                        float(state.get("progress", 0)),
                        max(0.1, float(state.get("thickness", 3))) * (20.0 / 3.0),
                        max(0.1, float(state.get("thickness", 3))) * 5.0,
                    )
                    visual["path"].setPath(arrow_path)
                    visual["head"].setPolygon(head)
        finally:
            self._adjusting_handles = False
        if final and self.selected_node is not None:
            params = self.selected_node["params"]
            if self.selected_node.get("type") == "arrow_curve":
                state = next((
                    visual["state"] for visual in self.arrow_visuals
                    if visual["state"]["name"] == str(params.get("object", ""))
                ), {})
                offset = QPointF(float(state.get("x", 0)), -float(state.get("y", 0)))
                scale_x = float(state.get("scale_x", 1)) or 1.0
                scale_y = float(state.get("scale_y", 1)) or 1.0
                def raw(point: QPointF) -> tuple[float, float]:
                    return ((point.x() - offset.x()) / scale_x,
                            -(point.y() - offset.y()) / scale_y)
                a0 = raw(self.handles["start"].pos())
                a1 = raw(self.handles["control1"].pos())
                a2 = raw(self.handles["control2"].pos())
                a3 = raw(self.handles["end"].pos())
                self.arrowCurveDrawn.emit(
                    str(self.selected_node["id"]),
                    a0[0], a0[1], a1[0], a1[1],
                    a2[0], a2[1], a3[0], a3[1])


class EditorWindow(QMainWindow):
    """Compact Nepy-style editor for Chemanim's mostly-linear scripts."""

    CATEGORY_ORDER = ["通用", "分子", "箭头"]

    def __init__(self, initial: Path | None = None):
        super().__init__()
        self.document = empty_document()
        self.path: Path | None = None
        self.dirty = False
        self.updating = False
        self._syncing_code_selection = False
        self.property_widgets: dict[str, QWidget] = {}
        self.history: list[dict[str, Any]] = []
        self.history_selected_ids: list[str | None] = []
        self.history_index = -1
        self.saved_snapshot = ""
        self.node_line_map: dict[str, tuple[int, int]] = {}
        self._last_object_selection = {
            "object": "", "sprite": "", "arrow": ""}
        self.resize(1480, 900)
        self.setMinimumSize(1050, 650)
        self._build_actions()
        self._build_ui()
        self._build_menus()
        self.preview_timer = QTimer(self)
        self.preview_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.preview_timer.timeout.connect(self._advance_preview_playback)
        self.canvas.play_button.clicked.connect(self._toggle_preview_playback)
        if initial:
            self.open_path(initial)
        else:
            # Cold start is an intentionally empty workspace. Opening the
            # editor must never guess which project the user meant to edit.
            self._reset_history(saved=True)
            self.refresh_all()

    def _icon(self, standard: QStyle.StandardPixmap) -> QIcon:
        return self.style().standardIcon(standard)

    @staticmethod
    def _color_icon(color: str) -> QIcon:
        pixmap = QPixmap(14, 14)
        pixmap.fill(QColor(color))
        return QIcon(pixmap)

    def _make_action(self, text: str, callback, shortcut=None, icon=None) -> QAction:
        action = QAction(icon or QIcon(), text, self)
        if shortcut is not None:
            action.setShortcut(shortcut)
        action.triggered.connect(callback)
        self.addAction(action)
        return action

    def _build_actions(self) -> None:
        self.new_action = self._make_action(
            "新建", self.new_document, QKeySequence.StandardKey.New,
            self._icon(QStyle.StandardPixmap.SP_FileIcon),
        )
        self.open_action = self._make_action(
            "打开", self.open_dialog, QKeySequence.StandardKey.Open,
            self._icon(QStyle.StandardPixmap.SP_DialogOpenButton),
        )
        self.save_action = self._make_action(
            "保存", self.save, QKeySequence.StandardKey.Save,
            self._icon(QStyle.StandardPixmap.SP_DialogSaveButton),
        )
        self.save_as_action = self._make_action("另存为", self.save_as)
        self.undo_action = self._make_action(
            "撤销", self.undo, QKeySequence.StandardKey.Undo,
            self._icon(QStyle.StandardPixmap.SP_ArrowBack),
        )
        self.redo_action = self._make_action(
            "重做", self.redo, QKeySequence.StandardKey.Redo,
            self._icon(QStyle.StandardPixmap.SP_ArrowForward),
        )
        self.duplicate_action = self._make_action(
            "复制节点", self.duplicate_node, QKeySequence("Ctrl+D"),
            self._icon(QStyle.StandardPixmap.SP_FileDialogNewFolder),
        )
        self.delete_action = self._make_action(
            "删除节点", self.delete_node, QKeySequence("Delete"),
            self._icon(QStyle.StandardPixmap.SP_TrashIcon),
        )
        self.move_up_action = self._make_action(
            "上移", lambda: self.move_node(-1), QKeySequence("Alt+Up"),
            self._icon(QStyle.StandardPixmap.SP_ArrowUp),
        )
        self.move_down_action = self._make_action(
            "下移", lambda: self.move_node(1), QKeySequence("Alt+Down"),
            self._icon(QStyle.StandardPixmap.SP_ArrowDown),
        )
        self.toggle_disabled_action = self._make_action(
            "启用/禁用节点", self.toggle_current_disabled, QKeySequence("Ctrl+E")
        )
        self.generate_action = self._make_action(
            "生成 Lua", self.generate_lua, QKeySequence("F6"),
            self._icon(QStyle.StandardPixmap.SP_DialogApplyButton),
        )
        self.render_action = self._make_action(
            "渲染 MP4", self.render_mp4, QKeySequence("F5"),
            self._icon(QStyle.StandardPixmap.SP_MediaPlay),
        )
        self.toggle_code_action = self._make_action(
            "显示代码", self.toggle_code_view, QKeySequence("F4"),
            self._icon(QStyle.StandardPixmap.SP_FileDialogDetailedView),
        )
        self.toggle_code_action.setCheckable(True)

    def _build_ui(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.category_tabs = QTabBar()
        self.category_tabs.setObjectName("nodeCategoryTabs")
        self.category_tabs.setExpanding(False)
        for category in self.CATEGORY_ORDER:
            if any(
                definition["category"] == category and definition.get("palette", True)
                for definition in NODE_DEFS.values()
            ):
                self.category_tabs.addTab(category)
        self.category_tabs.currentChanged.connect(self._rebuild_subcategory_tabs)
        layout.addWidget(self.category_tabs)

        self.subcategory_tabs = QTabBar()
        self.subcategory_tabs.setObjectName("nodeSubcategoryTabs")
        self.subcategory_tabs.setExpanding(False)
        self.subcategory_tabs.setUsesScrollButtons(True)
        self.subcategory_tabs.currentChanged.connect(self._rebuild_node_palette)
        layout.addWidget(self.subcategory_tabs)

        self.node_palette = QToolBar("节点")
        self.node_palette.setMovable(False)
        self.node_palette.setIconSize(QSize(14, 14))
        self.node_palette.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        layout.addWidget(self.node_palette)

        self.node_tree = LinearNodeTree()
        self.node_tree.setHeaderHidden(True)
        self.node_tree.setRootIsDecorated(False)
        self.node_tree.setIndentation(0)
        self.node_tree.setUniformRowHeights(True)
        self.node_tree.setIconSize(QSize(14, 14))
        self.node_tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.node_tree.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.node_tree.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.node_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.node_tree.itemSelectionChanged.connect(self.selection_changed)
        self.node_tree.itemDoubleClicked.connect(lambda *_: self.toggle_current_disabled())
        self.node_tree.customContextMenuRequested.connect(self._open_node_menu)
        self.node_tree.dropped.connect(self.tree_reordered)

        self.lua_preview = QPlainTextEdit()
        self.lua_preview.setObjectName("luaPreview")
        self.lua_preview.setReadOnly(True)
        self.lua_preview.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        fixed_font = self.lua_preview.font()
        fixed_font.setFamilies(["Cascadia Code", "Consolas", "Microsoft YaHei UI"])
        fixed_font.setPointSize(10)
        self.lua_preview.setFont(fixed_font)
        self.lua_preview.cursorPositionChanged.connect(self._code_cursor_changed)

        self.workspace_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.workspace_splitter.addWidget(self._panel("节点序列", self.node_tree))
        self.canvas = SceneCanvas()
        self.canvas.objectPositionCommitted.connect(self._canvas_object_position_committed)
        self.canvas.arrowCurveDrawn.connect(self._canvas_arrow_curve_drawn)
        self.canvas.objectClicked.connect(self._canvas_object_clicked)
        self.canvas.frame_slider.valueChanged.connect(self._preview_slider_changed)
        self.canvas.frame_spin.valueChanged.connect(self._preview_spin_changed)
        self.workspace_splitter.addWidget(self._panel("场景预览", self.canvas))
        self.code_panel = self._panel("生成的 Lua（只读）", self.lua_preview)
        self.workspace_splitter.addWidget(self.code_panel)
        self.workspace_splitter.setStretchFactor(0, 2)
        self.workspace_splitter.setStretchFactor(1, 3)
        self.workspace_splitter.setStretchFactor(2, 2)

        inspector = QWidget()
        inspector_layout = QVBoxLayout(inspector)
        inspector_layout.setContentsMargins(8, 8, 8, 8)
        inspector_layout.setSpacing(7)
        self.property_title = QLabel("未选择节点")
        self.property_title.setObjectName("inspectorTitle")
        inspector_layout.addWidget(self.property_title)
        self.property_table = QTableWidget(0, 2)
        self.property_table.setHorizontalHeaderLabels(["属性", "值"])
        self.property_table.verticalHeader().setVisible(False)
        self.property_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.property_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.property_table.setAlternatingRowColors(True)
        self.property_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.property_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        inspector_layout.addWidget(self.property_table)

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.addWidget(self.workspace_splitter)
        self.main_splitter.addWidget(self._panel("节点参数", inspector))
        self.main_splitter.setStretchFactor(0, 4)
        self.main_splitter.setStretchFactor(1, 1)
        layout.addWidget(self.main_splitter, 1)
        self.setCentralWidget(central)

        self.main_toolbar = QToolBar("主工具栏")
        self.main_toolbar.setMovable(False)
        self.main_toolbar.setIconSize(QSize(18, 18))
        self.main_toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        for actions in (
            [self.new_action, self.open_action, self.save_action],
            [self.undo_action, self.redo_action],
            [self.duplicate_action, self.delete_action, self.move_up_action, self.move_down_action],
            [self.toggle_code_action, self.generate_action, self.render_action],
        ):
            if self.main_toolbar.actions():
                self.main_toolbar.addSeparator()
            self.main_toolbar.addActions(actions)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.main_toolbar)

        self._rebuild_subcategory_tabs(0)
        self.main_splitter.setSizes([1120, 360])
        self.workspace_splitter.setSizes([430, 690, 0])
        self._apply_compact_style()

    @staticmethod
    def _panel(title: str, content: QWidget) -> QWidget:
        panel = QWidget()
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(5, 5, 5, 5)
        panel_layout.setSpacing(4)
        label = QLabel(title)
        label.setObjectName("panelTitle")
        panel_layout.addWidget(label)
        panel_layout.addWidget(content, 1)
        return panel

    def _apply_compact_style(self) -> None:
        self.setStyleSheet(compact_nepy_stylesheet())

    def _build_menus(self) -> None:
        file_menu = self.menuBar().addMenu("文件")
        file_menu.addActions([self.new_action, self.open_action, self.save_action, self.save_as_action])
        edit_menu = self.menuBar().addMenu("编辑")
        edit_menu.addActions([self.undo_action, self.redo_action])
        edit_menu.addSeparator()
        edit_menu.addActions([self.duplicate_action, self.delete_action, self.toggle_disabled_action])
        edit_menu.addSeparator()
        edit_menu.addActions([self.move_up_action, self.move_down_action])
        view_menu = self.menuBar().addMenu("视图")
        view_menu.addAction(self.toggle_code_action)
        build_menu = self.menuBar().addMenu("构建")
        build_menu.addActions([self.generate_action, self.render_action])

    def _rebuild_subcategory_tabs(self, index: int) -> None:
        self.node_palette.clear()
        self.subcategory_tabs.blockSignals(True)
        while self.subcategory_tabs.count():
            self.subcategory_tabs.removeTab(0)
        if index < 0 or index >= self.category_tabs.count():
            self.subcategory_tabs.blockSignals(False)
            return
        category = self.category_tabs.tabText(index)
        node_types = [
            node_type for node_type, definition in NODE_DEFS.items()
            if definition["category"] == category and definition.get("palette", True)
        ]
        for subcategory in ordered_subcategories(category, node_types):
            self.subcategory_tabs.addTab(subcategory)
        self.subcategory_tabs.blockSignals(False)
        if self.subcategory_tabs.count():
            self.subcategory_tabs.setCurrentIndex(0)
            self._rebuild_node_palette(0)

    def _rebuild_node_palette(self, index: int) -> None:
        self.node_palette.clear()
        category_index = self.category_tabs.currentIndex()
        if (
            category_index < 0 or category_index >= self.category_tabs.count()
            or index < 0 or index >= self.subcategory_tabs.count()
        ):
            return
        category = self.category_tabs.tabText(category_index)
        subcategory = self.subcategory_tabs.tabText(index)
        for node_type, definition in NODE_DEFS.items():
            if (
                definition["category"] != category
                or not definition.get("palette", True)
                or node_subcategory(node_type) != subcategory
            ):
                continue
            action = QAction(self._color_icon(definition["color"]), definition["label"], self)
            action.setToolTip(f"在当前节点之后插入“{definition['label']}”")
            action.triggered.connect(lambda _checked=False, value=node_type: self.insert_node(value))
            self.node_palette.addAction(action)

    def _open_node_menu(self, position) -> None:
        if self.current_node() is None:
            return
        menu = QMenu(self)
        menu.addActions([self.duplicate_action, self.delete_action])
        menu.addSeparator()
        menu.addAction(self.toggle_disabled_action)
        menu.addSeparator()
        menu.addActions([self.move_up_action, self.move_down_action])
        menu.exec(self.node_tree.viewport().mapToGlobal(position))

    def _auto_document(self) -> Path | None:
        preferred = MOD_ROOT / "aldol" / "aldol.cmm"
        if preferred.exists():
            return preferred
        files = sorted(MOD_ROOT.glob("*/*.cmm")) if MOD_ROOT.exists() else []
        return files[0] if len(files) == 1 else None

    def _snapshot(self) -> str:
        return json.dumps(self.document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def _reset_history(self, *, saved: bool) -> None:
        self.history = [deepcopy(self.document)]
        self.history_selected_ids = [None]
        self.history_index = 0
        self.saved_snapshot = self._snapshot() if saved else ""
        self._update_dirty_state()

    def _record_history(self, selected_id: str | None = None) -> None:
        current_item = self.node_tree.currentItem()
        current_tree_id = (
            current_item.data(0, Qt.ItemDataRole.UserRole)
            if current_item is not None else None
        )
        if 0 <= self.history_index < len(self.history_selected_ids):
            self.history_selected_ids[self.history_index] = current_tree_id
        snapshot = deepcopy(self.document)
        self.history = self.history[: self.history_index + 1]
        self.history_selected_ids = self.history_selected_ids[: self.history_index + 1]
        self.history.append(snapshot)
        self.history_selected_ids.append(selected_id or current_tree_id)
        self.history_index += 1
        self._update_dirty_state()

    def _update_dirty_state(self) -> None:
        self.dirty = self._snapshot() != self.saved_snapshot
        self.undo_action.setEnabled(self.history_index > 0)
        self.redo_action.setEnabled(self.history_index + 1 < len(self.history))
        self.update_title()

    def undo(self) -> None:
        if self.history_index <= 0:
            return
        self.history_index -= 1
        self.document = deepcopy(self.history[self.history_index])
        self.refresh_all(self.history_selected_ids[self.history_index])
        self._update_dirty_state()

    def redo(self) -> None:
        if self.history_index + 1 >= len(self.history):
            return
        self.history_index += 1
        self.document = deepcopy(self.history[self.history_index])
        self.refresh_all(self.history_selected_ids[self.history_index])
        self._update_dirty_state()

    def update_title(self) -> None:
        name = self.path.name if self.path else "未命名.cmm"
        self.setWindowTitle(f"{'*' if self.dirty else ''}{name} — Chemanim")

    def maybe_discard(self) -> bool:
        if not self.dirty:
            return True
        result = QMessageBox.question(self, "未保存", "当前 .cmm 有未保存修改，继续将丢失这些修改。")
        return result == QMessageBox.StandardButton.Yes

    def new_document(self) -> None:
        if not self.maybe_discard():
            return
        self._stop_preview_playback()
        name, ok = QInputDialog.getText(self, "新建动画", "模组名", text="aldol")
        if not ok or not name.strip():
            return
        name = name.strip()
        self.document = default_document(name)
        self.path = MOD_ROOT / name / f"{name}.cmm"
        self._reset_history(saved=False)
        self.refresh_all()

    def open_dialog(self) -> None:
        if not self.maybe_discard():
            return
        name, _ = QFileDialog.getOpenFileName(self, "打开 CMM", str(MOD_ROOT), "Chemanim 工程 (*.cmm)")
        if name:
            self.open_path(Path(name))

    def open_path(self, path: Path) -> None:
        try:
            self._stop_preview_playback()
            document = json.loads(path.read_text(encoding="utf-8"))
            if document.get("format") != CMM_FORMAT or int(document.get("version", 0)) != CMM_VERSION:
                raise ValueError("不是受支持的 Chemanim CMM v1 文件")
            if not isinstance(document.get("nodes"), list):
                raise ValueError("CMM 缺少 nodes 数组")
            original_node_count = len(document["nodes"])
            document["nodes"] = [
                node for node in document["nodes"]
                if node.get("type") != "arrow_head"
            ]
            migrated_head_nodes = len(document["nodes"]) != original_node_count
            ids: set[str] = set()
            migrated_change_nodes = False
            for node_index, node in enumerate(document["nodes"]):
                node_type = node.get("type")
                if node_type not in NODE_DEFS:
                    raise ValueError(f"未知节点类型：{node_type}")
                node_id = str(node.get("id") or uuid.uuid4().hex)
                if node_id in ids:
                    node_id = uuid.uuid4().hex
                ids.add(node_id)
                node["id"] = node_id
                node.setdefault("enabled", True)
                params = node.setdefault("params", {})
                if node_type == "arrow_curve" and "initialized" not in params:
                    # Existing CMM files already contain intentionally chosen
                    # coordinates. Only newly inserted curve nodes enter draw mode.
                    params["initialized"] = True
                if node_type == "change_image" and ("x" not in params or "y" not in params):
                    x, y = sprite_position_through(
                        document, node_index - 1, str(params.get("object", "")))
                    params.setdefault("x", round(x, 2))
                    params.setdefault("y", round(y, 2))
                    migrated_change_nodes = True
                for spec in NODE_DEFS[node_type]["fields"]:
                    params.setdefault(spec["key"], deepcopy(spec["default"]))
            self.document = document
            self.path = path.resolve()
            migrated = migrated_head_nodes or migrated_change_nodes
            self._reset_history(saved=not migrated)
            self.refresh_all()
            message = f"已打开 {self.path}"
            if migrated_head_nodes:
                message += "；已移除旧箭头头部节点，头部现由线宽自动决定"
            if migrated_change_nodes:
                message += "；已为旧贴图过渡补入当帧目标坐标"
            self.statusBar().showMessage(message, 6000)
        except Exception as error:
            QMessageBox.critical(self, "打开失败", str(error))

    def save(self):
        if self.path is None:
            return self.save_as()
        try:
            self.sync_order()
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.document, ensure_ascii=False, indent=2), encoding="utf-8")
            self.saved_snapshot = self._snapshot()
            self._update_dirty_state()
            self.statusBar().showMessage(f"已保存 {self.path}", 4000)
            return True
        except Exception as error:
            QMessageBox.critical(self, "保存失败", str(error))
            return False

    def save_as(self):
        name, _ = QFileDialog.getSaveFileName(
            self, "保存 CMM", str(self.path or MOD_ROOT / "animation.cmm"), "Chemanim 工程 (*.cmm)"
        )
        if not name:
            return False
        self.path = Path(name if name.lower().endswith(".cmm") else name + ".cmm").resolve()
        return self.save()

    def current_index(self) -> int:
        item = self.node_tree.currentItem()
        return self.node_tree.indexOfTopLevelItem(item) if item else -1

    def current_node(self) -> dict[str, Any] | None:
        index = self.current_index()
        return self.document["nodes"][index] if 0 <= index < len(self.document["nodes"]) else None

    def current_node_id(self) -> str | None:
        node = self.current_node()
        return str(node["id"]) if node else None

    def item_for_node(self, node_id: str) -> QTreeWidgetItem | None:
        for index in range(self.node_tree.topLevelItemCount()):
            item = self.node_tree.topLevelItem(index)
            if item.data(0, Qt.ItemDataRole.UserRole) == node_id:
                return item
        return None

    def calculate_node_frames(self) -> list[int]:
        current_frame = 0
        frames: list[int] = []
        for node in self.document.get("nodes", []):
            frames.append(current_frame)
            if not node.get("enabled", True):
                continue
            if node["type"] == "wait":
                current_frame += int(node["params"]["frames"])
        return frames

    def node_title(self, node: dict[str, Any], frame: int) -> str:
        node_type = node["type"]
        definition = NODE_DEFS[node_type]
        p = node.get("params", {})
        summary = ""
        if node_type == "scene":
            summary = f"{p['width']}×{p['height']}  →  {p['logic_width']}×{p['logic_height']}  ·  {p['fps']} fps"
        elif node_type == "load_texture":
            dimensions = self._png_dimensions(str(p.get("file", "")))
            summary = f"{p['name']}  ←  {p['file']}"
            if dimensions:
                summary += f"  ·  {dimensions} px"
        elif node_type == "load_textures":
            entries = texture_entries(node)
            names = [str(entry["name"]) for entry in entries]
            summary = f"{len(entries)} 张 PNG"
            if names:
                preview_names = ", ".join(names[:5])
                summary += f"  ·  {preview_names}"
                if len(names) > 5:
                    summary += "…"
        elif node_type in {"new_object", "new_arrow"}:
            summary = str(p["name"])
        elif node_type == "set_image":
            summary = f"{p['object']}  ←  {p['texture']}"
            dimensions = self._texture_dimensions(str(p.get("texture", "")))
            if dimensions:
                summary += f"  ·  {dimensions} px"
        elif node_type == "change_image":
            mode_index = max(0, min(len(MODE_NAMES) - 1, int(p["mode"])))
            mode = MODE_NAMES[mode_index].split("  ", 1)[-1]
            dimensions = self._texture_dimensions(str(p.get("texture", "")))
            size_text = f"  ·  {dimensions} px" if dimensions else ""
            summary = (
                f"{p['object']}  ⇄  {p['texture']}{size_text}"
                f"  →  ({lua_number(p.get('x', 0))}, {lua_number(p.get('y', 0))})"
                f"  ·  {p['frames']} 帧  ·  {mode}"
            )
        elif node_type == "set_pos":
            summary = f"{p['object']}  →  ({lua_number(p['x'])}, {lua_number(p['y'])})"
        elif node_type in {"set_pos_x", "set_pos_y"}:
            axis = "X" if node_type.endswith("_x") else "Y"
            summary = f"{p['object']}  →  {axis} {lua_number(p['value'])}"
        elif node_type == "set_alpha":
            summary = f"{p['object']}  →  α {p['value']}"
        elif node_type == "set_scale":
            summary = f"{p['object']}  →  {lua_number(p['x'])} × {lua_number(p['y'])}"
        elif node_type in {"set_scale_x", "set_scale_y"}:
            axis = "X" if node_type.endswith("_x") else "Y"
            summary = f"{p['object']}  →  {axis} {lua_number(p['value'])}"
        elif node_type in {"set_rotation", "set_layer", "set_visible"}:
            summary = f"{p['object']}  →  {p['value']}"
        elif node_type == "set_anchor":
            summary = f"{p['object']}  →  ({lua_number(p['x'])}, {lua_number(p['y'])})"
        elif node_type in {"lerp_mol_color", "lerp_arrow_color"}:
            mode_index = max(0, min(len(MODE_NAMES) - 1, int(p["mode"])))
            mode = MODE_NAMES[mode_index].split("  ", 1)[-1]
            summary = (
                f"{p['object']}  →  RGB({p['r']}, {p['g']}, {p['b']})"
                f"  ·  {p['frames']} 帧  ·  {mode}"
            )
        elif node_type.startswith("lerp_") and node_type != "lerp_arrow":
            target = (
                f"({lua_number(p['x'])}, {lua_number(p['y'])})"
                if "x" in p and "y" in p else str(p.get("value", ""))
            )
            mode_index = max(0, min(len(MODE_NAMES) - 1, int(p["mode"])))
            mode = MODE_NAMES[mode_index].split("  ", 1)[-1]
            summary = f"{p['object']}  →  {target}  ·  {p['frames']} 帧  ·  {mode}"
        elif node_type == "wait":
            summary = f"{p['frames']} 帧"
        elif node_type in {"delete", "delete_arrow"}:
            summary = str(p["object"])
        elif node_type == "arrow_curve":
            summary = (
                f"{p['object']}  ·  拖动画布绘制"
                if not p.get("initialized", True)
                else f"{p['object']}  ·  ({p['x1']}, {p['y1']}) → ({p['x2']}, {p['y2']})"
            )
        elif node_type == "arrow_color":
            summary = f"{p['object']}  ·  RGBA({p['r']}, {p['g']}, {p['b']}, {p['a']})"
        elif node_type in {"arrow_width", "arrow_progress"}:
            summary = f"{p['object']}  →  {p['value']}"
        elif node_type == "lerp_arrow":
            mode_index = max(0, min(len(MODE_NAMES) - 1, int(p["mode"])))
            mode = MODE_NAMES[mode_index].split("  ", 1)[-1]
            summary = f"{p['object']}  →  {p['value']}  ·  {p['frames']} 帧  ·  {mode}"
        elif node_type == "raw_lua":
            summary = str(next(iter(p.values()), "")).splitlines()[0][:72]
        if not summary and "object" in p:
            summary = node_summary(node)
        prefix = f"{frame:04d}   {definition['label']}"
        return f"{prefix}   ·   {summary}" if summary else prefix

    def _png_dimensions(self, file_name: str) -> str:
        if not file_name:
            return ""
        path = Path(file_name)
        if not path.is_absolute():
            path = self.mod_directory() / path
        size = QImageReader(str(path)).size()
        return f"{size.width()}×{size.height()}" if size.isValid() else ""

    def _texture_dimensions(self, texture_name: str) -> str:
        for node in reversed(self.document.get("nodes", [])):
            if not node.get("enabled", True):
                continue
            for entry in reversed(texture_entries(node)):
                if str(entry["name"]) == texture_name:
                    return self._png_dimensions(str(entry["file"]))
        return ""

    def refresh_all(self, selected_id: str | None = None) -> None:
        if selected_id is None:
            selected_id = self.current_node_id()
        self.updating = True
        self.node_tree.blockSignals(True)
        self.node_tree.clear()
        frames = self.calculate_node_frames()
        selected_item = None
        for index, node in enumerate(self.document.get("nodes", [])):
            definition = NODE_DEFS[node["type"]]
            item = QTreeWidgetItem([self.node_title(node, frames[index])])
            item.setData(0, Qt.ItemDataRole.UserRole, node["id"])
            item.setIcon(0, self._color_icon(definition["color"]))
            item.setFlags((item.flags() | Qt.ItemFlag.ItemIsDragEnabled) & ~Qt.ItemFlag.ItemIsDropEnabled)
            if not node.get("enabled", True):
                font = item.font(0)
                font.setStrikeOut(True)
                item.setFont(0, font)
                item.setForeground(0, QColor("#7f8c8d"))
            self.node_tree.addTopLevelItem(item)
            if node["id"] == selected_id:
                selected_item = item
        if selected_item is None and self.node_tree.topLevelItemCount():
            selected_item = self.node_tree.topLevelItem(0)
        if selected_item is not None:
            self.node_tree.setCurrentItem(selected_item)
        self.node_tree.blockSignals(False)
        self.updating = False
        self.refresh_preview()
        self.selection_changed()
        self.update_title()

    def refresh_node_rows(self) -> None:
        frames = self.calculate_node_frames()
        for index, node in enumerate(self.document["nodes"]):
            item = self.node_tree.topLevelItem(index)
            if item is not None:
                item.setText(0, self.node_title(node, frames[index]))

    def sync_order(self, *_args) -> bool:
        ids = [
            self.node_tree.topLevelItem(i).data(0, Qt.ItemDataRole.UserRole)
            for i in range(self.node_tree.topLevelItemCount())
        ]
        by_id = {node["id"]: node for node in self.document["nodes"]}
        if ids and len(ids) == len(by_id) and set(ids) == set(by_id):
            changed = ids != [node["id"] for node in self.document["nodes"]]
            self.document["nodes"] = [by_id[node_id] for node_id in ids]
            return changed
        return False

    def tree_reordered(self, *_args) -> None:
        if self.updating:
            return
        selected_item = self.node_tree.currentItem()
        selected_id = (
            selected_item.data(0, Qt.ItemDataRole.UserRole)
            if selected_item is not None else None
        )
        if self.sync_order():
            self._record_history(selected_id)
        self.refresh_all(selected_id)

    def insert_node(self, node_type: str) -> None:
        index = self.current_index()
        # No selection means append, so defaults must be calculated from the
        # whole document rather than from an artificial index of -1.
        through_index = index if index >= 0 else len(self.document["nodes"]) - 1
        node = new_node(node_type)
        for key, value in inherited_node_parameters(
            self.document, through_index, node_type).items():
            if key in node["params"]:
                node["params"][key] = value
        if node_type in {"new_object", "new_arrow"}:
            kind = {"new_object": "molecule", "new_arrow": "arrow"}[node_type]
            node["params"]["name"] = next_numbered_object_name(self.document, index, kind)
        for spec in NODE_DEFS[node_type]["fields"]:
            key, kind = spec["key"], spec["kind"]
            choices: list[str] = []
            if kind == "arrow": choices = self.object_names(arrows_only=True, through_index=through_index)
            elif kind == "sprite": choices = self.object_names(sprites_only=True, through_index=through_index)
            elif kind == "object": choices = self.object_names(sprites_only=True, through_index=through_index)
            if choices:
                # Binding is contextual: always target the newest live object
                # of the required kind at the insertion point.
                node["params"][key] = choices[-1]
            elif kind == "texture" and not node["params"].get(key):
                textures = self.texture_names()
                if textures:
                    node["params"][key] = textures[0]
        if node_type == "change_image":
            x, y = sprite_position_through(
                self.document, through_index, str(node["params"].get("object", "")))
            node["params"]["x"], node["params"]["y"] = round(x, 2), round(y, 2)
        self.document["nodes"].insert(index + 1 if index >= 0 else len(self.document["nodes"]), node)
        self._record_history(node["id"])
        self.refresh_all(node["id"])

    def duplicate_node(self) -> None:
        node = self.current_node()
        if not node:
            return
        clone = deepcopy(node)
        clone["id"] = uuid.uuid4().hex
        if clone["type"] in {"new_object", "new_arrow"}:
            kind = {"new_object": "molecule", "new_arrow": "arrow"}[clone["type"]]
            clone["params"]["name"] = next_numbered_object_name(
                self.document, self.current_index(), kind)
        self.document["nodes"].insert(self.current_index() + 1, clone)
        self._record_history(clone["id"])
        self.refresh_all(clone["id"])

    def delete_node(self) -> None:
        index = self.current_index()
        if index < 0:
            return
        del self.document["nodes"][index]
        selected_id = None
        if self.document["nodes"]:
            selected_id = self.document["nodes"][min(index, len(self.document["nodes"]) - 1)]["id"]
        self._record_history(selected_id)
        self.refresh_all(selected_id)

    def move_node(self, delta: int) -> None:
        index = self.current_index()
        target = index + delta
        if index < 0 or target < 0 or target >= len(self.document["nodes"]):
            return
        node = self.document["nodes"].pop(index)
        self.document["nodes"].insert(target, node)
        self._record_history(node["id"])
        self.refresh_all(node["id"])

    def toggle_current_disabled(self) -> None:
        node = self.current_node()
        if not node:
            return
        node["enabled"] = not node.get("enabled", True)
        self._record_history(node["id"])
        self.refresh_all(node["id"])

    def selection_changed(self) -> None:
        if self.updating:
            return
        node = self.current_node()
        if node is not None and node.get("params", {}).get("object"):
            name = str(node["params"]["object"])
            field_kind = next(
                (spec["kind"] for spec in NODE_DEFS[node["type"]]["fields"] if spec["key"] == "object"),
                "object",
            )
            self._last_object_selection[field_kind] = name
            self._last_object_selection["object"] = name
        self._populate_inspector(node)
        index = self.current_index()
        if index >= 0:
            frames = self.calculate_node_frames()
            if index < len(frames):
                preview_frame = frames[index]
                if node is not None and node.get("type") in {
                    "lerp_pos", "lerp_pos_x", "lerp_pos_y",
                }:
                    # Position tweens are edited at their destination. After
                    # this initial jump, manual timeline scrubbing always uses
                    # the actual evaluated track and is never overridden.
                    preview_frame += max(0, int(node["params"].get("frames", 0)))
                self._set_preview_frame(preview_frame)
        else:
            self.refresh_canvas()
        if node is not None and not self._syncing_code_selection:
            self._highlight_code_for_node(node["id"])

    def _populate_inspector(self, node: dict[str, Any] | None) -> None:
        self.updating = True
        self.property_widgets.clear()
        self.property_table.clearContents()
        self.property_table.setRowCount(0)
        if node is None:
            self.property_title.setText("未选择节点")
            self.updating = False
            return
        definition = NODE_DEFS[node["type"]]
        self.property_title.setText(definition["label"])
        fields = definition["fields"]
        self.property_table.setRowCount(len(fields))
        for row, spec in enumerate(fields):
            name_item = QTableWidgetItem(spec["label"])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.property_table.setItem(row, 0, name_item)
            value = node["params"].get(spec["key"], spec["default"])
            editor = self.make_editor(node, spec, value)
            self.property_widgets[spec["key"]] = editor
            self.property_table.setCellWidget(row, 1, editor)
            if spec["kind"] == "multiline":
                self.property_table.setRowHeight(row, 120)
            elif spec["kind"] == "texture":
                self.property_table.setRowHeight(row, 82)
            elif spec["kind"] == "scene_color":
                self.property_table.setRowHeight(row, 76)
            elif spec["kind"] == "file" and node.get("type") == "load_texture":
                self.property_table.setRowHeight(row, 132)
            elif spec["kind"] == "files":
                file_count = len(value) if isinstance(value, list) else 0
                self.property_table.setRowHeight(
                    row, max(350, min(720, 86 + file_count * 174)))
        self.updating = False

    def _connect_combo(self, widget: QComboBox, callback) -> None:
        widget.activated.connect(lambda *_: callback())
        if widget.isEditable() and widget.lineEdit() is not None:
            widget.lineEdit().editingFinished.connect(callback)

    def make_editor(self, node: dict[str, Any], spec: dict[str, Any], value: Any) -> QWidget:
        key, kind = spec["key"], spec["kind"]
        commit = lambda result: self.change_param(node, key, result)
        if kind in {"int", "alpha", "byte"}:
            widget = QSpinBox()
            widget.setRange(0 if kind in {"alpha", "byte"} else -1_000_000, 255 if kind in {"alpha", "byte"} else 1_000_000)
            widget.setValue(int(value))
            widget.editingFinished.connect(lambda w=widget: commit(w.value()))
            return widget
        if kind in {"float", "float01"}:
            widget = QDoubleSpinBox()
            widget.setDecimals(2)
            widget.setRange(0 if kind == "float01" else -1_000_000, 1 if kind == "float01" else 1_000_000)
            widget.setValue(float(value))
            if node.get("type") == "arrow_width":
                # Size tuning is visual work: update the canvas on every
                # spin-box step instead of waiting for focus to leave.
                widget.valueChanged.connect(lambda result: commit(result))
            else:
                widget.editingFinished.connect(lambda w=widget: commit(w.value()))
            return widget
        if kind == "bool":
            widget = QComboBox()
            widget.addItems(["否", "是"])
            widget.setCurrentIndex(1 if bool(value) else 0)
            widget.activated.connect(lambda _=0, w=widget: commit(w.currentIndex() == 1))
            return widget
        if kind == "mode":
            widget = QComboBox()
            widget.addItems(MODE_NAMES)
            widget.setCurrentIndex(int(value))
            widget.activated.connect(lambda _=0, w=widget: commit(w.currentIndex()))
            return widget
        if kind in {"object", "sprite", "arrow", "texture"}:
            if kind == "texture":
                widget = TextureResourcePicker(
                    self.texture_resources(), str(value),
                    document_background_color(self.document))
                widget.activated.connect(lambda _index=0, w=widget: commit(w.resource_name()))
                return widget
            widget = QComboBox()
            if kind == "sprite":
                choices = self.object_names(sprites_only=True, through_index=self.current_index() - 1)
            else:
                choices = self.object_names(
                    arrows_only=kind == "arrow", sprites_only=kind != "arrow",
                    through_index=self.current_index() - 1)
            widget.addItems(choices)
            if str(value) in choices:
                widget.setCurrentText(str(value))
            else:
                widget.setCurrentIndex(-1)
                widget.setPlaceholderText(
                    f"{value}（在此节点前已删除或未定义）" if value else "无可用对象")
            self._connect_combo(widget, lambda w=widget: commit(w.currentText()))
            return widget
        if kind == "scene_color":
            widget = ColorValueEditor(str(value))
            widget.colorChanged.connect(commit)
            return widget
        if kind == "multiline":
            widget = CommitPlainTextEdit(str(value))
            widget.editingFinished.connect(lambda w=widget: commit(w.toPlainText()))
            return widget
        if kind == "files":
            widget = MultiTextureFileEditor(
                self.mod_directory(), list(value) if isinstance(value, list) else [],
                document_background_color(self.document))
            widget.filesChanged.connect(commit)
            widget.choose_button.clicked.connect(
                lambda _=False, w=widget, n=node, k=key: self.choose_pngs(w, n, k))
            return widget
        if kind == "file":
            if node.get("type") == "load_texture":
                widget = TextureFileEditor(
                    self.mod_directory(), str(value),
                    document_background_color(self.document))
                widget.edit.editingFinished.connect(
                    lambda e=widget.edit: commit(e.text()))
                widget.button.clicked.connect(
                    lambda _=False, e=widget.edit, n=node, k=key: self.choose_png(e, n, k))
                return widget
            container = QWidget()
            row = QHBoxLayout(container)
            row.setContentsMargins(0, 0, 0, 0)
            edit = QLineEdit(str(value))
            button = QToolButton()
            button.setText("…")
            edit.editingFinished.connect(lambda e=edit: commit(e.text()))
            button.clicked.connect(lambda _=False, e=edit, n=node, k=key: self.choose_png(e, n, k))
            row.addWidget(edit, 1)
            row.addWidget(button)
            return container
        widget = QLineEdit(str(value))
        widget.editingFinished.connect(lambda w=widget: commit(w.text()))
        return widget

    def change_param(self, node: dict[str, Any], key: str, value: Any) -> None:
        if self.updating or node["params"].get(key) == value:
            return
        node["params"][key] = value
        if key == "object":
            field_kind = next(
                (spec["kind"] for spec in NODE_DEFS[node["type"]]["fields"] if spec["key"] == key),
                "object",
            )
            self._last_object_selection[field_kind] = str(value)
            self._last_object_selection["object"] = str(value)
        self._record_history()
        self.refresh_node_rows()
        self.refresh_preview()
        self.refresh_canvas()

    def choose_png(self, edit: QLineEdit, node: dict[str, Any], key: str) -> None:
        mod_dir = self.mod_directory()
        name, _ = QFileDialog.getOpenFileName(self, "选择 PNG", str(mod_dir), "PNG 图片 (*.png)")
        if not name:
            return
        source = Path(name)
        destination = mod_dir / source.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.resolve() != destination.resolve():
            shutil.copy2(source, destination)
        edit.setText(destination.name)
        updates = {key: destination.name}
        if node.get("type") == "load_texture" and key == "file":
            # Choosing a file is the one explicit synchronization point.
            # The resource name remains freely editable afterwards.
            updates["name"] = destination.stem
        if all(node["params"].get(update_key) == update_value
               for update_key, update_value in updates.items()):
            return
        node["params"].update(updates)
        self._record_history(node["id"])
        self.refresh_all(node["id"])

    def choose_pngs(
        self, widget: MultiTextureFileEditor, node: dict[str, Any], key: str,
    ) -> None:
        """Register existing PNGs below the current mod without copying them."""
        mod_dir = self.mod_directory().resolve()
        names, _ = QFileDialog.getOpenFileNames(
            self, "选择模组内的 PNG", str(mod_dir), "PNG 图片 (*.png)")
        if not names:
            return
        existing = {
            str(entry["file"]).casefold(): entry for entry in texture_entries(node)
        }
        selected: list[dict[str, Any]] = []
        selected_keys: set[str] = set()
        rejected: list[str] = []
        for name in names:
            source = Path(name).resolve()
            try:
                relative = source.relative_to(mod_dir).as_posix()
            except ValueError:
                rejected.append(str(source))
                continue
            normalized = relative.casefold()
            if normalized not in selected_keys:
                previous = existing.get(normalized, {})
                selected.append({
                    "file": relative,
                    "anchor_x": previous.get("anchor_x", 0.5),
                    "anchor_y": previous.get("anchor_y", 0.5),
                })
                selected_keys.add(normalized)
        if rejected:
            QMessageBox.warning(
                self, "文件不在当前模组中",
                "批量资源加载不会复制文件。以下文件不在当前模组目录，已忽略：\n\n"
                + "\n".join(rejected))
        if not selected or node["params"].get(key) == selected:
            return
        node["params"][key] = selected
        widget.set_files(selected)
        self._record_history(node["id"])
        self.refresh_all(node["id"])

    def scene_size(self) -> tuple[int, int]:
        for node in self.document["nodes"]:
            if node["type"] == "scene" and node.get("enabled", True):
                return int(node["params"]["logic_width"]), int(node["params"]["logic_height"])
        return 960, 540

    def object_names(
        self, arrows_only=False, sprites_only=False,
        through_index: int | None = None,
    ) -> list[str]:
        """Return objects alive after executing nodes through the given index."""
        if through_index is None:
            through_index = self.current_index() - 1
        live = live_objects_at(self.document, through_index)
        if arrows_only:
            return [name for name, kind in live.items() if kind == "arrow"]
        return [name for name, kind in live.items() if kind == "molecule"]

    def texture_names(self) -> list[str]:
        return [
            str(entry["name"])
            for node in self.document["nodes"]
            if node.get("enabled", True)
            for entry in texture_entries(node)
        ]

    def texture_resources(self) -> list[dict[str, str]]:
        mod_dir = self.mod_directory()
        return [
            {
                "name": str(entry["name"]),
                "file": str(entry["file"]),
                "path": str((mod_dir / str(entry["file"])).resolve()),
            }
            for node in self.document.get("nodes", [])
            if node.get("enabled", True)
            for entry in texture_entries(node)
        ]

    def build_lua_with_map(self, include_disabled=False) -> tuple[str, dict[str, tuple[int, int]]]:
        blocks: list[str] = []
        mapping: dict[str, tuple[int, int]] = {}
        line = 1
        for node in self.document["nodes"]:
            if node.get("enabled", True):
                block = node_lua(node)
            elif include_disabled:
                block = "-- [已禁用] " + node_lua(node).replace("\n", "\n-- ")
            else:
                continue
            count = max(1, len(block.splitlines()))
            mapping[node["id"]] = (line, line + count - 1)
            blocks.append(block)
            line += count + 1
        return "\n\n".join(blocks).rstrip() + "\n", mapping

    def build_lua(self, include_disabled=False) -> str:
        return self.build_lua_with_map(include_disabled)[0]

    def refresh_preview(self) -> None:
        try:
            code, self.node_line_map = self.build_lua_with_map(include_disabled=True)
            vertical = self.lua_preview.verticalScrollBar().value()
            self._syncing_code_selection = True
            self.lua_preview.setPlainText(code)
            self.lua_preview.verticalScrollBar().setValue(vertical)
            self._syncing_code_selection = False
            node_id = self.current_node_id()
            if node_id:
                self._highlight_code_for_node(node_id)
        except Exception as error:
            self.lua_preview.setPlainText(f"-- 生成错误：{error}")

    def _highlight_code_for_node(self, node_id: str) -> None:
        line_range = self.node_line_map.get(node_id)
        if line_range is None:
            self.lua_preview.setExtraSelections([])
            return
        block = self.lua_preview.document().findBlockByNumber(line_range[0] - 1)
        if not block.isValid():
            return
        selection = QTextEdit.ExtraSelection()
        selection.cursor = QTextCursor(block)
        selection.format.setBackground(QColor(70, 120, 190, 55))
        selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        self.lua_preview.setExtraSelections([selection])

    def _code_cursor_changed(self) -> None:
        if self._syncing_code_selection or not self.toggle_code_action.isChecked():
            return
        line = self.lua_preview.textCursor().blockNumber() + 1
        node_id = next((node_id for node_id, bounds in self.node_line_map.items() if bounds[0] <= line <= bounds[1]), None)
        if node_id is None or node_id == self.current_node_id():
            return
        item = self.item_for_node(node_id)
        if item is not None:
            self._syncing_code_selection = True
            self.node_tree.setCurrentItem(item)
            self.node_tree.scrollToItem(item)
            self._syncing_code_selection = False

    def toggle_code_view(self, checked=False) -> None:
        if checked:
            total = max(900, sum(self.workspace_splitter.sizes()))
            self.workspace_splitter.setSizes([int(total * 0.30), int(total * 0.40), int(total * 0.30)])
        else:
            total = max(800, sum(self.workspace_splitter.sizes()))
            self.workspace_splitter.setSizes([int(total * 0.38), int(total * 0.62), 0])

    def _scene_fps(self) -> int:
        for node in self.document.get("nodes", []):
            if node.get("enabled", True) and node.get("type") == "scene":
                return max(1, int(node.get("params", {}).get("fps", 60)))
        return 60

    def _stop_preview_playback(self) -> None:
        if hasattr(self, "preview_timer"):
            self.preview_timer.stop()
        if hasattr(self, "canvas"):
            self.canvas.play_button.setText("▶ 播放")

    def _toggle_preview_playback(self) -> None:
        if self.preview_timer.isActive():
            self._stop_preview_playback()
            return
        maximum = self._preview_max_frame()
        self.canvas.frame_slider.setRange(0, maximum)
        self.canvas.frame_spin.setRange(0, maximum)
        if self.canvas.frame_spin.value() >= maximum:
            self._set_preview_frame(0)
        self.preview_timer.setInterval(max(1, round(1000 / self._scene_fps())))
        self.canvas.play_button.setText("⏸ 暂停")
        self.preview_timer.start()

    def _advance_preview_playback(self) -> None:
        next_frame = self.canvas.frame_spin.value() + 1
        if next_frame > self._preview_max_frame():
            self._stop_preview_playback()
            return
        self.canvas.frame_slider.setValue(next_frame)

    def _preview_max_frame(self) -> int:
        evaluator = SceneEvaluator(self.document)
        maximum = evaluator.cursor
        for obj in evaluator.objects:
            maximum = max(maximum, int(obj.get("born", 0)))
            if obj.get("dead", 2**31 - 1) < 2**31 - 1:
                maximum = max(maximum, int(obj["dead"]))
            for segments in obj.get("tracks", {}).values():
                for segment in segments:
                    maximum = max(maximum, min(
                        int(segment["start"] + segment["duration"]),
                        int(segment.get("cancel", 2**31 - 1)),
                    ))
            for transition in obj.get("image_transitions", []):
                maximum = max(maximum, min(
                    int(transition["end"]),
                    int(transition.get("cancel", 2**31 - 1)),
                ))
        return max(1, maximum)

    def _set_preview_frame(self, frame: int) -> None:
        maximum = self._preview_max_frame()
        value = max(0, min(maximum, int(frame)))
        self.canvas.frame_slider.blockSignals(True)
        self.canvas.frame_spin.blockSignals(True)
        self.canvas.frame_slider.setRange(0, maximum)
        self.canvas.frame_spin.setRange(0, maximum)
        self.canvas.frame_slider.setValue(value)
        self.canvas.frame_spin.setValue(value)
        self.canvas.frame_slider.blockSignals(False)
        self.canvas.frame_spin.blockSignals(False)
        self.refresh_canvas()

    def _preview_slider_changed(self, value: int) -> None:
        self.canvas.frame_spin.blockSignals(True)
        self.canvas.frame_spin.setValue(value)
        self.canvas.frame_spin.blockSignals(False)
        self.refresh_canvas()

    def _preview_spin_changed(self, value: int) -> None:
        self.canvas.frame_slider.blockSignals(True)
        self.canvas.frame_slider.setValue(value)
        self.canvas.frame_slider.blockSignals(False)
        self.refresh_canvas()

    def refresh_canvas(self) -> None:
        if not hasattr(self, "canvas"):
            return
        try:
            self.canvas.render_document(
                self.document, self.canvas.frame_spin.value(), self.current_node(), self.mod_directory()
            )
        except Exception as error:
            self.statusBar().showMessage(f"画布预览失败：{error}", 6000)

    def _node_by_id(self, node_id: str) -> dict[str, Any] | None:
        return next((node for node in self.document["nodes"] if node["id"] == node_id), None)

    def _position_node_for_object(self, object_name: str) -> dict[str, Any] | None:
        current = self.current_node()
        if (
            current is not None
            and current.get("type") in POSITION_NODE_AXES
            and str(current.get("params", {}).get("object", "")) == object_name
        ):
            return current
        preview_frame = self.canvas.frame_spin.value()
        frames = self.calculate_node_frames()
        before: dict[str, Any] | None = None
        after: dict[str, Any] | None = None
        for node, node_frame in zip(self.document.get("nodes", []), frames):
            if (
                not node.get("enabled", True)
                or node.get("type") not in POSITION_NODE_AXES
                or str(node.get("params", {}).get("object", "")) != object_name
            ):
                continue
            if node_frame <= preview_frame:
                before = node
            elif after is None:
                after = node
        return before or after

    def _select_node(self, node_id: str) -> None:
        for index in range(self.node_tree.topLevelItemCount()):
            item = self.node_tree.topLevelItem(index)
            if item.data(0, Qt.ItemDataRole.UserRole) == node_id:
                self.node_tree.setCurrentItem(item)
                self.node_tree.scrollToItem(item, QAbstractItemView.ScrollHint.PositionAtCenter)
                return

    def _canvas_object_clicked(self, object_name: str) -> None:
        target = self._position_node_for_object(object_name)
        if target is not None:
            if target is not self.current_node():
                self._select_node(target["id"])
            return
        fallback_id: str | None = None
        for node in self.document.get("nodes", []):
            if not node.get("enabled", True):
                continue
            params = node.get("params", {})
            if node.get("type") == "new_object" and str(params.get("name", "")) == object_name:
                fallback_id = node["id"]
        if fallback_id is not None:
            self._select_node(fallback_id)

    def _canvas_object_position_committed(self, object_name: str, x: float, y: float) -> None:
        current = self.current_node()
        if (
            current is not None
            and current.get("type") == "change_image"
            and str(current.get("params", {}).get("object", "")) == object_name
        ):
            current["params"]["x"] = round(x, 2)
            current["params"]["y"] = round(y, 2)
            self._record_history(current["id"])
            self.refresh_all(current["id"])
            return
        node = self._position_node_for_object(object_name)
        if node is None:
            self.statusBar().showMessage(
                f"{object_name} 还没有位置节点；请先添加“设定位置”或位置插值节点。", 5000)
            self.refresh_canvas()
            return
        node_type = node["type"]
        if node_type in {"set_pos", "lerp_pos"}:
            node["params"]["x"] = round(x, 2)
            node["params"]["y"] = round(y, 2)
        elif node_type in {"set_pos_x", "lerp_pos_x"}:
            node["params"]["value"] = round(x, 2)
        else:
            node["params"]["value"] = round(y, 2)
        self._record_history(node["id"])
        self.refresh_all(node["id"])

    def _canvas_arrow_curve_drawn(
        self, node_id: str, x1: float, y1: float, cx1: float, cy1: float,
        cx2: float, cy2: float, x2: float, y2: float,
    ) -> None:
        node = self._node_by_id(node_id)
        if node is None or node.get("type") != "arrow_curve":
            return
        node["params"].update({
            "x1": round(x1, 2), "y1": round(y1, 2),
            "cx1": round(cx1, 2), "cy1": round(cy1, 2),
            "cx2": round(cx2, 2), "cy2": round(cy2, 2),
            "x2": round(x2, 2), "y2": round(y2, 2),
            "initialized": True,
        })
        self._record_history(node_id)
        self.refresh_all(node_id)

    def mod_directory(self) -> Path:
        return MOD_ROOT / str(self.document.get("mod", "untitled"))

    def generate_lua(self, quiet=False) -> Path | None:
        try:
            if not self.save():
                return None
            path = self.mod_directory() / "main.lua"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(self.build_lua(), encoding="utf-8")
            self.statusBar().showMessage(f"已生成 {path}", 5000)
            if not quiet:
                QMessageBox.information(self, "生成成功", str(path))
            return path
        except Exception as error:
            QMessageBox.critical(self, "生成失败", str(error))
            return None

    def render_mp4(self) -> None:
        if self.generate_lua(quiet=True) is None:
            return
        executable = ROOT / "build" / "release" / "chemanim.exe"
        if not executable.exists():
            QMessageBox.warning(self, "未构建", "请先运行 build.ps1")
            return
        subprocess.Popen([str(executable), str(self.document["mod"])], cwd=ROOT)
        self.statusBar().showMessage("已启动 MP4 渲染，完成后会自动播放。", 5000)

    def closeEvent(self, event) -> None:
        self._stop_preview_playback()
        event.accept() if self.maybe_discard() else event.ignore()


def main() -> int:
    app = QApplication(sys.argv); app.setStyle("Fusion")
    ui_font = app.font()
    ui_font.setFamilies(["Microsoft YaHei UI", "Segoe UI", "sans-serif"])
    app.setFont(ui_font)
    initial = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else None
    window = EditorWindow(initial); window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
