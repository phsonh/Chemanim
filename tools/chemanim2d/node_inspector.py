from __future__ import annotations

import json

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout,
                             QLabel, QLineEdit, QPlainTextEdit, QSpinBox, QWidget)


class NodeInspector(QWidget):
    nodeEdited = pyqtSignal(str)

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
        self.title.setText(f'{definition.get("label", node["type"])} · {node["id"]}')
        params = node.get("params", {}); self._updating = True
        for spec in definition.get("fields", []):
            key, kind = spec["key"], spec["kind"]; value = params.get(key, spec.get("default")); editor = None
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
        self._updating = False

    def apply(self):
        if self._updating or not self.node_id: return
        params = {}
        for key, (editor, kind) in self.editors.items():
            if isinstance(editor, QComboBox): params[key] = editor.currentData()
            elif isinstance(editor, QSpinBox): params[key] = editor.value()
            elif isinstance(editor, QDoubleSpinBox): params[key] = round(editor.value(), 2)
            elif isinstance(editor, QCheckBox): params[key] = editor.isChecked()
            elif isinstance(editor, QPlainTextEdit): params[key] = editor.toPlainText()
            else: params[key] = editor.text()
        if self.session.update_node(self.node_id, json.dumps(params)):
            self.nodeEdited.emit(self.node_id)
