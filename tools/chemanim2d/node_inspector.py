from __future__ import annotations

import json

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout,
                             QLabel, QLineEdit, QPlainTextEdit, QPushButton,
                             QSpinBox, QWidget)


LEGACY_STRUCTURE_TYPES = {"molecule_lerp_structure", "bond_form", "bond_break",
                          "selection_show", "selection_hide", "selection_fade"}


def molecule_name(project, stable_id):
    molecule = next((item for item in project.get("molecules", []) if item["id"] == stable_id), None)
    name = (molecule or {}).get("name", "")
    if name and name != stable_id: return name
    suffix = stable_id.removeprefix("molecule")
    return f"分子 {suffix}" if suffix.isdigit() else (name or "分子")


class NodeInspector(QWidget):
    nodeEdited = pyqtSignal(str)
    editStructureRequested = pyqtSignal(str)
    rebuildRequested = pyqtSignal(str)

    def __init__(self, session, parent=None):
        super().__init__(parent); self.session = session; self.node_id = ""; self._updating = False; self.editors = {}
        self.layout = QFormLayout(self); self.title = QLabel("未选择节点"); self.title.setObjectName("inspectorTitle"); self.layout.addRow(self.title)

    def set_node(self, node_id):
        self.node_id = node_id; self.refresh()

    def _clear(self):
        while self.layout.rowCount() > 1: self.layout.removeRow(1)
        self.editors.clear()

    def _choices(self, kind, params):
        project = self.session.project(); target = params.get("target", "")
        current = next((item for item in project.get("nodes", []) if item["id"] == self.node_id), None)
        if kind == "molecule":
            if current and current["type"] == "molecule_create":
                return [(item["name"], item["id"]) for item in project.get("molecules", [])]
            alive = []
            for node in project.get("nodes", []):
                if node["id"] == self.node_id: break
                value = node.get("params", {}).get("target", "")
                if node["type"] == "molecule_create" and value not in alive: alive.append(value)
                elif node["type"] == "molecule_delete" and value in alive: alive.remove(value)
            by_id = {item["id"]: item for item in project.get("molecules", [])}
            return [(by_id[value]["name"], value) for value in alive if value in by_id]
        molecule = next((item for item in project.get("molecules", []) if item["id"] == target), None)
        if kind == "atom": return [(f'{item.get("label") or "C"} · {item["id"]}', item["id"]) for item in (molecule or {}).get("atoms", []) if item.get("alive",True)]
        if kind == "bond": return [(f'{item["a"]}—{item["b"]} · {item["id"]}', item["id"]) for item in (molecule or {}).get("bonds", []) if item.get("alive",True)]
        if kind == "pose": return [(key, key) for key in (molecule or {}).get("poses", {})]
        if kind == "arrow":
            names = []
            for node in project.get("nodes", []):
                if node["id"] == self.node_id: break
                if node["type"] == "arrow_new": names.append(node["params"].get("target", ""))
                elif node["type"] == "arrow_delete" and node["params"].get("target") in names: names.remove(node["params"].get("target"))
            return [(name, name) for name in names if name]
        if kind == "easing": return [(name, value) for name, value in (("Linear","linear"),("In Quad","in_quad"),("Out Quad","out_quad"),("In/Out Quad","in_out_quad"),("Smoothstep","smoothstep"),("Step","step"))]
        if kind == "bond_order": return [(name, value) for name, value in (("单键","single"),("双键","double"),("三键","triple"))]
        if kind == "secondary_line_side": return [(name,value) for name,value in (("左侧","left"),("右侧","right"),("居中","center"))]
        if kind == "bond_stereo": return [(name, value) for name, value in (("无","none"),("实楔","wedge"),("虚楔","dash"),("波浪","wavy"))]
        return []

    def refresh(self):
        self._clear(); project = self.session.project(); node = next((item for item in project.get("nodes", []) if item["id"] == self.node_id), None)
        if not node: self.title.setText("未选择节点"); return
        definition = next((item for item in self.session.node_registry() if item["type"] == node["type"]), None)
        params = node.get("params", {}); self._updating = True
        if node["type"] in LEGACY_STRUCTURE_TYPES:
            self.title.setText("旧版结构节点")
            note=QLabel("旧版结构节点，仅用于兼容。目标对象会在画布中高亮；内部引用不可手工编辑。")
            note.setWordWrap(True);self.layout.addRow(note);self._updating=False;return
        if node["type"]=="molecule_gradient_structure":
            self.title.setText(f'渐变结构 · {molecule_name(project,params.get("target",""))}')
        else:self.title.setText(definition.get("label", "节点"))
        for spec in definition.get("fields", []):
            key, kind = spec["key"], spec["kind"]; value = params.get(key, spec.get("default")); editor = None
            if node["type"]=="molecule_gradient_structure" and key=="target":
                editor=QLineEdit(molecule_name(project,value));editor.setReadOnly(True)
                self.editors[key]=(editor,"readonly_target");self.layout.addRow("目标分子",editor);continue
            choices = self._choices(kind, params)
            if choices:
                editor = QComboBox()
                for label, data in choices: editor.addItem(label, data)
                found = editor.findData(value)
                if found >= 0: editor.setCurrentIndex(found)
                elif value: editor.addItem(str(value), value); editor.setCurrentIndex(editor.count() - 1)
                editor.currentIndexChanged.connect(self.apply)
            elif kind in ("int", "byte", "alpha"):
                editor = QSpinBox(); editor.setRange(0 if kind in ("byte", "alpha") else -100000, 255 if kind in ("byte", "alpha") else 100000); editor.setValue(int(value)); editor.editingFinished.connect(self.apply)
            elif kind in ("float", "float01"):
                editor = QDoubleSpinBox(); editor.setRange(0 if kind == "float01" else -100000, 1 if kind == "float01" else 100000); editor.setDecimals(2); editor.setSingleStep(.05 if kind == "float01" else .1); editor.setValue(float(value)); editor.editingFinished.connect(self.apply)
            elif kind == "bool":
                editor = QCheckBox(); editor.setChecked(bool(value)); editor.toggled.connect(self.apply)
            elif kind == "multiline":
                editor = QPlainTextEdit(str(value)); editor.setMinimumHeight(120); editor.textChanged.connect(self.apply)
            else:
                editor = QLineEdit(str(value)); editor.editingFinished.connect(self.apply)
            self.editors[key] = (editor, kind); self.layout.addRow(spec["label"], editor)
            if key == "target" and definition.get("target_immutable"):
                editor.setEnabled(False);editor.setToolTip("新建分子的目标由 Core 分配，不可重新指向")
        if node["type"]=="molecule_gradient_structure":
            summary=self.session.gradient_summary(self.node_id)
            if summary.get("needs_review"):
                warning=QLabel("起点结构已变化，需要检查");warning.setStyleSheet("color:#f0ad4e;font-weight:600");self.layout.addRow(warning)
                rebuild=QPushButton("以新起点重建终态");rebuild.clicked.connect(lambda:self.rebuildRequested.emit(self.node_id));self.layout.addRow(rebuild)
            values=[]
            for key,label in (("added_atoms","新增原子"),("added_bonds","新增键"),("moved_atoms","移动原子"),("deleted_objects","删除对象"),("changed_objects","改变样式")):
                values.append(f'{label} {summary.get(key,0)} 个')
            text=QLabel("\n".join(values));self.layout.addRow("变化摘要",text)
            edit=QPushButton("编辑终态结构");edit.clicked.connect(lambda:self.editStructureRequested.emit(self.node_id));self.layout.addRow(edit)
        self._updating = False

    def apply(self):
        if self._updating or not self.node_id: return
        current=next((item for item in self.session.project().get("nodes",[]) if item["id"]==self.node_id),{})
        params = dict(current.get("params",{}))
        for key, (editor, kind) in self.editors.items():
            if kind=="readonly_target":continue
            if isinstance(editor, QComboBox): params[key] = editor.currentData()
            elif isinstance(editor, QSpinBox): params[key] = editor.value()
            elif isinstance(editor, QDoubleSpinBox): params[key] = round(editor.value(), 2)
            elif isinstance(editor, QCheckBox): params[key] = editor.isChecked()
            elif isinstance(editor, QPlainTextEdit): params[key] = editor.toPlainText()
            else: params[key] = editor.text()
        if self.session.update_node(self.node_id, json.dumps(params)):
            self.nodeEdited.emit(self.node_id)
