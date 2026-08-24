from __future__ import annotations

from pathlib import Path
import subprocess

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QActionGroup, QColor, QIcon, QKeySequence, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QSplitter, QToolBar, QTreeWidget, QTreeWidgetItem, QVBoxLayout,
    QDockWidget, QWidget, QHBoxLayout, QPushButton, QSlider, QSpinBox)

from .canvas import StructureCanvas
from .core import CoreSession
from .inspector import AtomInspector


def tool_icon(kind: str) -> QIcon:
    pixmap = QPixmap(28, 28); pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor(225, 230, 236), 2))
    if kind.startswith("ring") or kind == "benzene":
        count = 6 if kind == "benzene" else int(kind[-1]); from math import cos, sin, pi
        points = [__import__('PyQt6.QtCore').QtCore.QPointF(14 + 10*cos(-pi/2+i*2*pi/count), 14 + 10*sin(-pi/2+i*2*pi/count)) for i in range(count)]
        from PyQt6.QtGui import QPolygonF
        painter.drawPolygon(QPolygonF(points))
        if kind == "benzene": painter.drawEllipse(8, 8, 12, 12)
    elif "bond" in kind or "wedge" in kind:
        if kind == "double_bond": painter.drawLine(5, 11, 23, 11); painter.drawLine(5, 17, 23, 17)
        elif kind == "triple_bond":
            for y in (9, 14, 19): painter.drawLine(5, y, 23, y)
        elif kind == "solid_wedge":
            painter.setBrush(QColor(225,230,236)); painter.drawPolygon(__import__('PyQt6.QtGui').QtGui.QPolygonF([__import__('PyQt6.QtCore').QtCore.QPointF(4,14),__import__('PyQt6.QtCore').QtCore.QPointF(24,7),__import__('PyQt6.QtCore').QtCore.QPointF(24,21)]))
        else: painter.drawLine(4, 20, 24, 8)
    elif kind == "atom_label": painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "C")
    elif "charge" in kind: painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "+" if "positive" in kind else "−")
    elif kind == "eraser": painter.drawRect(7, 8, 15, 12)
    elif kind == "select_lasso": painter.drawEllipse(5, 6, 18, 16)
    else: painter.drawRect(5, 6, 18, 16)
    painter.end(); return QIcon(pixmap)


class SmilesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowTitle("从 SMILES 生成起稿")
        self.name = QLineEdit("新分子"); self.smiles = QLineEdit("CC(=O)NC1=CC=C(O)C=C1")
        form = QFormLayout(); form.addRow("名称", self.name); form.addRow("SMILES", self.smiles)
        note = QLabel("SMILES 仅用于起稿。导入后由 C++ Core 中的 atom/bond/XY 和稳定 ID 作为权威数据。"); note.setWordWrap(True)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self); layout.addLayout(form); layout.addWidget(note); layout.addWidget(buttons); self.resize(560, 150)


class MainWindow(QMainWindow):
    def __init__(self, root: Path):
        super().__init__(); self.root = root; self.path = None; self.dirty = False; self.session = CoreSession()
        self.session.add_blank_molecule("molecule1")
        self.setWindowTitle("Chemanim · 结构编辑"); self.resize(1540, 920)
        self.tree = QTreeWidget(); self.tree.setHeaderLabels(["结构", "稳定 ID"]); self.tree.currentItemChanged.connect(self._tree_selection)
        self.canvas = StructureCanvas(self.session); self.canvas.selectionChanged.connect(self._selection)
        self.canvas.transactionCommitted.connect(self._transaction); self.canvas.hoverChanged.connect(self._hover)
        self.inspector = AtomInspector(self.session); self.inspector.atomEdited.connect(self._transaction)
        split = QSplitter(); split.addWidget(self.tree); split.addWidget(self.canvas); split.addWidget(self.inspector); split.setSizes([260, 1020, 260]); self.setCentralWidget(split)
        self._build_project_toolbar(); self._build_structure_toolbar(); self._build_timeline(); self.refresh_tree(); self.canvas.request_refresh()
        self.statusBar().showMessage("在空白处拖动键可创建两个原子；从已有原子拖出可延伸；靠近原子优先连接；Alt 临时关闭 15° 吸附。")

    def _build_project_toolbar(self):
        bar = QToolBar("工程", self); bar.setMovable(False); self.addToolBar(bar)
        def add(text, slot, shortcut=None, checkable=False):
            action = QAction(text, self); action.triggered.connect(slot); action.setCheckable(checkable)
            if shortcut: action.setShortcut(shortcut)
            bar.addAction(action); return action
        add("新建", self.new_project, QKeySequence.StandardKey.New); add("打开", self.open_project, QKeySequence.StandardKey.Open)
        add("保存", self.save, QKeySequence.StandardKey.Save); bar.addSeparator(); add("空白分子", self.add_blank, "Ctrl+Shift+M")
        add("SMILES 起稿", self.add_smiles, "Ctrl+M"); bar.addSeparator(); add("撤销", self.undo, QKeySequence.StandardKey.Undo)
        add("重做", self.redo, QKeySequence.StandardKey.Redo); bar.addSeparator(); add("适配视图", self.canvas.fit, "F")
        final = add("最终效果预览", lambda checked: self.canvas.set_final_effect(checked), checkable=True); final.setToolTip("使用与引擎相同的 NanoSVG 后端")
        bar.addSeparator(); add("生成 Lua", self.generate_lua, "F6"); add("渲染 MP4", self.render_mp4, "F5")

    def _build_structure_toolbar(self):
        bar = QToolBar("结构工具", self); bar.setMovable(False); bar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon); self.addToolBar(bar)
        group = QActionGroup(self); group.setExclusive(True)
        tools = [
            ("框选", "select_rectangle", "V"), ("套索", "select_lasso", "L"), ("移动", "move", "M"), ("橡皮", "eraser", "E"),
            ("单键", "single_bond", "1"), ("双键", "double_bond", "2"), ("三键", "triple_bond", "3"), ("芳香键", "aromatic_bond", "4"),
            ("实楔", "solid_wedge", None), ("虚楔", "dashed_wedge", None), ("波浪键", "wavy_bond", None),
            ("元素", "atom_label", "A"), ("正电荷", "charge_positive", "+"), ("负电荷", "charge_negative", "-"),
            ("三元环", "ring3", None), ("四元环", "ring4", None), ("五元环", "ring5", None), ("六元环", "ring6", None),
            ("七元环", "ring7", None), ("八元环", "ring8", None), ("苯环", "benzene", "B")]
        for label, key, shortcut in tools:
            action = QAction(tool_icon(key), label, self); action.setCheckable(True); action.setData(key); group.addAction(action); bar.addAction(action)
            if shortcut: action.setShortcut(shortcut)
            action.triggered.connect(lambda checked, value=key: self._set_tool(value) if checked else None)
            if key == "select_rectangle": action.setChecked(True)
        bar.addSeparator(); self.element_action = QAction("元素: C", self); self.element_action.triggered.connect(self.choose_element); bar.addAction(self.element_action)

    def _build_timeline(self):
        dock = QDockWidget("原子姿态时间轴", self); panel = QWidget(); layout = QVBoxLayout(panel)
        self.timeline_tree = QTreeWidget(); self.timeline_tree.setHeaderLabels(["节点", "帧", "对象"]); self.timeline_tree.currentItemChanged.connect(self._timeline_selection); layout.addWidget(self.timeline_tree)
        row = QHBoxLayout(); self.frame_slider = QSlider(Qt.Orientation.Horizontal); self.frame_slider.setRange(0, 1800)
        self.frame_spin = QSpinBox(); self.frame_spin.setRange(0, 1800); self.frame_slider.valueChanged.connect(self.frame_spin.setValue); self.frame_spin.valueChanged.connect(self.frame_slider.setValue); self.frame_slider.valueChanged.connect(self._preview_frame)
        add = QPushButton("为选中原子添加 30 帧 Lerp"); add.clicked.connect(self._add_atom_tween); base = QPushButton("编辑基础结构"); base.clicked.connect(self._edit_base)
        row.addWidget(QLabel("帧")); row.addWidget(self.frame_slider); row.addWidget(self.frame_spin); row.addWidget(add); row.addWidget(base); layout.addLayout(row)
        dock.setWidget(panel); self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)

    def _set_tool(self, value): self.session.set_tool(value); self.statusBar().showMessage(f"当前工具：{value}")
    def choose_element(self):
        from PyQt6.QtWidgets import QInputDialog
        value, ok = QInputDialog.getItem(self, "元素标签", "元素", ["C","H","N","O","F","P","S","Cl","Br","I","B","Si"], 0, True)
        if ok and value.strip(): self.session.set_element(value.strip()); self.element_action.setText(f"元素: {value.strip()}"); self.session.set_tool("atom_label")

    def mark_dirty(self): self.dirty = True; self._title()
    def _title(self): self.setWindowTitle(("*" if self.dirty else "") + (self.path.name if self.path else "未命名.cmm") + " — Chemanim")
    def _transaction(self): self.mark_dirty(); self.refresh_tree(); self.inspector.refresh_values(); self.canvas.request_refresh()
    def _hover(self, value):
        if value["kind"] != "none": self.statusBar().showMessage(f'{value["kind"]} {value["id"]}')

    def new_project(self):
        self.session.new_project(); self.session.add_blank_molecule("molecule1"); self.path = None; self.dirty = False; self.refresh_tree(); self.canvas.fit(); self._title()
    def add_blank(self):
        stable_id = self.session.add_blank_molecule(""); self.mark_dirty(); self.refresh_tree(); self.canvas.fit(); self.statusBar().showMessage(f"已新建 {stable_id}")
    def add_smiles(self):
        dialog = SmilesDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted: return
        try: stable_id = self.session.import_smiles(dialog.name.text().strip(), dialog.smiles.text().strip())
        except Exception as error: QMessageBox.warning(self, "无法导入", str(error)); return
        self.mark_dirty(); self.refresh_tree(); self.canvas.fit(); self.statusBar().showMessage(f"已导入 {stable_id}")
    def open_project(self):
        name, _ = QFileDialog.getOpenFileName(self, "打开工程", str(self.root / "mod"), "Chemanim (*.cmm)")
        if name: self.load(Path(name))
    def load(self, path: Path):
        try: self.session.load(str(path))
        except Exception as error: QMessageBox.critical(self, "无法打开", str(error)); return
        self.path = path; self.dirty = False; self.refresh_tree(); self.canvas.fit(); self._title()
    def save(self):
        if not self.path:
            name, _ = QFileDialog.getSaveFileName(self, "保存工程", str(self.root / "mod" / "native2d.cmm"), "Chemanim (*.cmm)")
            if not name: return
            self.path = Path(name)
        try: self.session.save(str(self.path))
        except Exception as error: QMessageBox.critical(self, "保存失败", str(error)); return
        self.dirty = False; self._title(); self.statusBar().showMessage(f"已保存 {self.path}")
    def undo(self):
        if self.session.undo(): self.mark_dirty(); self.refresh_tree(); self.canvas.request_refresh()
    def redo(self):
        if self.session.redo(): self.mark_dirty(); self.refresh_tree(); self.canvas.request_refresh()
    def generate_lua(self):
        try: path = self.session.write_mod(str(self.root))
        except Exception as error: QMessageBox.critical(self, "生成失败", str(error)); return
        self.statusBar().showMessage(f"已生成 {path}")
    def render_mp4(self):
        self.generate_lua(); executable = self.root / "build" / "release" / "chemanim.exe"
        if not executable.exists(): QMessageBox.information(self, "尚未构建", "请先运行 .\\build.ps1"); return
        mod = self.session.project().get("mod", "native2d_demo")
        try: subprocess.Popen([str(executable), mod], cwd=self.root)
        except Exception as error: QMessageBox.critical(self, "无法启动渲染", str(error))

    def refresh_tree(self):
        self.tree.clear(); project = self.session.project(); active = self.session.active_molecule
        for molecule in project.get("molecules", []):
            root = QTreeWidgetItem([molecule["name"], molecule["id"]]); root.setData(0, Qt.ItemDataRole.UserRole, ("molecule", molecule["id"])); self.tree.addTopLevelItem(root)
            atoms = QTreeWidgetItem([f'原子 ({len(molecule["atoms"])})', ""]); root.addChild(atoms)
            for atom in molecule["atoms"]:
                item = QTreeWidgetItem([f'{atom["element"]}  ({atom["x"]:.2f}, {atom["y"]:.2f})', atom["id"]]); item.setData(0, Qt.ItemDataRole.UserRole, ("atom", molecule["id"], atom["id"])); atoms.addChild(item)
            bonds = QTreeWidgetItem([f'键 ({len(molecule["bonds"])})', ""]); root.addChild(bonds)
            for bond in molecule["bonds"]:
                item = QTreeWidgetItem([f'{bond["a"]}—{bond["b"]}  {bond["type"]}', bond["id"]]); item.setData(0, Qt.ItemDataRole.UserRole, ("bond", molecule["id"], bond["id"])); bonds.addChild(item)
            root.setExpanded(molecule["id"] == active); atoms.setExpanded(molecule["id"] == active)
        self.timeline_tree.clear()
        for tween in project.get("timeline", {}).get("atom_tweens", []):
            item = QTreeWidgetItem([f'LerpAtomXY {tween["atom"]}', f'{tween["start"]} → {tween["start"]+tween["frames"]}', tween["molecule"]]); item.setData(0, Qt.ItemDataRole.UserRole, tween["id"]); self.timeline_tree.addTopLevelItem(item)

    def _tree_selection(self, item, previous):
        if not item: return
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data: return
        if data[1] != self.session.active_molecule: self.session.set_active_molecule(data[1]); self.canvas.fit()
    def _selection(self, atom_ids, bond_ids): self.inspector.set_selection(atom_ids, bond_ids)
    def _preview_frame(self, frame):
        self.session.preview_timeline(frame); self.canvas.request_refresh(); self.statusBar().showMessage(f"时间轴预览：第 {frame} 帧（只读）")
    def _edit_base(self):
        self.session.edit_base(self.frame_spin.value()); self.session.set_tool("move"); self.canvas.request_refresh(); self.statusBar().showMessage("正在编辑基础结构：拖动会修改初始 atom/XY")
    def _add_atom_tween(self):
        if len(self.canvas.selected_atoms) != 1: QMessageBox.information(self, "请选择原子", "先选择一个原子。"); return
        atom_id = self.canvas.selected_atoms[0]; project = self.session.project(); molecule = next(item for item in project["molecules"] if item["id"] == self.session.active_molecule); atom = next(item for item in molecule["atoms"] if item["id"] == atom_id)
        tween = self.session.add_atom_tween(atom_id, self.frame_spin.value(), 30, atom["x"], atom["y"]); self.session.edit_atom_tween(tween); self.mark_dirty(); self.refresh_tree(); self.canvas.request_refresh(); self.statusBar().showMessage(f"正在编辑 {tween} 的目标坐标；基础结构不会改变")
    def _timeline_selection(self, item, previous):
        if not item: return
        tween = item.data(0, Qt.ItemDataRole.UserRole)
        if tween: self.session.edit_atom_tween(tween); self.canvas.request_refresh(); self.statusBar().showMessage(f"正在编辑 {tween} 的目标坐标")


def save_window_screenshot(window: MainWindow, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True); window.show(); QTimer.singleShot(250, window.canvas.fit)
    QTimer.singleShot(1100, lambda: (window.grab().save(str(path)), window.close()))
