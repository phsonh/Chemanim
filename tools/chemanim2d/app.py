from __future__ import annotations

from pathlib import Path
import subprocess

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QKeySequence, QUndoCommand, QUndoStack
from PyQt6.QtWidgets import (QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QPlainTextEdit, QSplitter, QToolBar, QTreeWidget, QTreeWidgetItem, QVBoxLayout)

from .canvas import StructureCanvas
from .codegen import generate_lua, write_mod
from .inspector import AtomInspector
from .model import Project, load_project, save_project
from .smiles import molecule_from_smiles


class MoveAtomsCommand(QUndoCommand):
    def __init__(self, window: "MainWindow", before, after):
        super().__init__("移动原子"); self.window=window; self.before=before; self.after=after; self.first=True
    def _apply(self, values):
        molecule=self.window.current_molecule()
        if not molecule: return
        for atom in molecule.atoms:
            if atom.id in values: atom.x,atom.y=values[atom.id]
        self.window.canvas.update(); self.window.inspector.refresh_values(); self.window.mark_dirty()
    def undo(self): self._apply(self.before)
    def redo(self):
        if self.first: self.first=False
        else: self._apply(self.after)


class SmilesDialog(QDialog):
    def __init__(self,parent=None,next_id="molecule1"):
        super().__init__(parent); self.setWindowTitle("从 SMILES 新建分子")
        self.name=QLineEdit(next_id); self.smiles=QLineEdit("CC(=O)NC1=CC=C(O)C=C1")
        form=QFormLayout(); form.addRow("对象名",self.name); form.addRow("SMILES",self.smiles)
        note=QLabel("SMILES 只用于生成二维起稿；保存后，画布中的手工坐标是权威数据。"); note.setWordWrap(True)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout=QVBoxLayout(self); layout.addLayout(form); layout.addWidget(note); layout.addWidget(buttons); self.resize(560,150)


class MainWindow(QMainWindow):
    def __init__(self, root: Path):
        super().__init__(); self.root=root; self.project=Project(); self.path:Path|None=None; self.dirty=False; self.undo_stack=QUndoStack(self)
        self.setWindowTitle("Chemanim · 原生二维结构式"); self.resize(1480,900)
        self.tree=QTreeWidget(); self.tree.setHeaderLabel("结构"); self.tree.currentItemChanged.connect(self._tree_selection)
        self.canvas=StructureCanvas(); self.canvas.selectionChanged.connect(self._atom_selection)
        self.canvas.coordinatesChanged.connect(self._coordinates_changed); self.canvas.dragCommitted.connect(self._commit_drag)
        self.inspector=AtomInspector(); self.inspector.atomEdited.connect(self._inspector_edited)
        split=QSplitter(); split.addWidget(self.tree); split.addWidget(self.canvas); split.addWidget(self.inspector)
        split.setSizes([240,950,260]); self.setCentralWidget(split)
        self.code=QPlainTextEdit(); self.code.setReadOnly(True); self.code.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        from PyQt6.QtWidgets import QDockWidget
        self.code_dock=QDockWidget("生成的 Lua",self); self.code_dock.setWidget(self.code)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea,self.code_dock); self.code_dock.hide()
        self._build_toolbar(); self.statusBar().showMessage("点选、框选或 Ctrl 多选原子；拖动修改 XY，滚轮缩放，F 适配。")
        self.refresh_tree()

    def _build_toolbar(self):
        bar=QToolBar("项目",self); bar.setMovable(False); self.addToolBar(bar)
        def action(text,slot,shortcut=None):
            item=QAction(text,self); item.triggered.connect(slot)
            if shortcut: item.setShortcut(shortcut)
            bar.addAction(item); return item
        action("新建工程",self.new_project,QKeySequence.StandardKey.New); action("打开",self.open_project,QKeySequence.StandardKey.Open)
        action("保存",self.save,QKeySequence.StandardKey.Save); bar.addSeparator(); action("从 SMILES 新建",self.add_smiles,"Ctrl+M")
        bar.addSeparator(); undo=self.undo_stack.createUndoAction(self,"撤销"); undo.setShortcut(QKeySequence.StandardKey.Undo); bar.addAction(undo)
        redo=self.undo_stack.createRedoAction(self,"重做"); redo.setShortcut(QKeySequence.StandardKey.Redo); bar.addAction(redo)
        bar.addSeparator(); action("适配",self.canvas.fit,"F"); action("Lua",self.toggle_code,"F4")
        action("生成 Lua",self.generate,"F6"); action("渲染静态图",self.render_still,"F5")

    def mark_dirty(self): self.dirty=True; self._title(); self.code.setPlainText(generate_lua(self.project))
    def _title(self): self.setWindowTitle(("*" if self.dirty else "")+(self.path.name if self.path else "未命名.cmm")+" — Chemanim 原生二维")
    def current_molecule(self): return self.canvas.molecule
    def new_project(self): self.project=Project(); self.path=None; self.dirty=False; self.undo_stack.clear(); self.canvas.set_molecule(None); self.refresh_tree(); self._title()
    def open_project(self):
        name,_=QFileDialog.getOpenFileName(self,"打开 v2 工程",str(self.root/"mod"),"Chemanim v2 (*.cmm)")
        if name: self.load(Path(name))
    def load(self,path:Path):
        try: self.project=load_project(path)
        except Exception as error: QMessageBox.critical(self,"无法打开",str(error)); return
        self.path=path; self.dirty=False; self.undo_stack.clear(); self.canvas.set_molecule(None); self.refresh_tree(); self._title(); self.statusBar().showMessage(f"已打开 {path}")
    def save(self):
        if not self.path:
            name,_=QFileDialog.getSaveFileName(self,"保存 v2 工程",str(self.root/"mod"/self.project.mod/f"{self.project.mod}.cmm"),"Chemanim v2 (*.cmm)")
            if not name: return
            self.path=Path(name)
        try: save_project(self.project,self.path); self.dirty=False; self._title(); self.statusBar().showMessage(f"已原子写入 {self.path}")
        except Exception as error: QMessageBox.critical(self,"保存失败",str(error))
    def add_smiles(self):
        used={m.id for m in self.project.molecules}; index=1
        while f"molecule{index}" in used: index+=1
        dialog=SmilesDialog(self,f"molecule{index}")
        if dialog.exec()!=QDialog.DialogCode.Accepted: return
        object_id=dialog.name.text().strip() or f"molecule{index}"
        try: molecule=molecule_from_smiles(object_id,dialog.smiles.text().strip(),object_id)
        except Exception as error: QMessageBox.warning(self,"无法生成二维结构",str(error)); return
        self.project.molecules.append(molecule); self.mark_dirty(); self.refresh_tree(); self.canvas.set_molecule(molecule); self.canvas.fit()
    def refresh_tree(self):
        self.tree.clear()
        for molecule in self.project.molecules:
            root=QTreeWidgetItem([f"{molecule.name}  ({molecule.id})"]); root.setData(0,Qt.ItemDataRole.UserRole,("molecule",molecule.id)); self.tree.addTopLevelItem(root)
            atoms=QTreeWidgetItem([f"原子  {len(molecule.atoms)}"]); root.addChild(atoms)
            for atom in molecule.atoms:
                item=QTreeWidgetItem([f"{atom.id}  {atom.element}"]); item.setData(0,Qt.ItemDataRole.UserRole,("atom",molecule.id,atom.id)); atoms.addChild(item)
            bonds=QTreeWidgetItem([f"键  {len(molecule.bonds)}"]); root.addChild(bonds)
            for bond in molecule.bonds: bonds.addChild(QTreeWidgetItem([f"{bond.id}  {bond.a}—{bond.b}  {bond.order:g}"]))
            root.setExpanded(True); atoms.setExpanded(True)
        if self.project.molecules and not self.canvas.molecule: self.canvas.set_molecule(self.project.molecules[0])
        self.code.setPlainText(generate_lua(self.project))
    def _tree_selection(self,item,previous):
        if not item: return
        data=item.data(0,Qt.ItemDataRole.UserRole)
        if not data: return
        molecule=next((m for m in self.project.molecules if m.id==data[1]),None)
        if molecule is not self.canvas.molecule: self.canvas.set_molecule(molecule)
        if data[0]=="atom": self.canvas.selected={data[2]}; self._atom_selection(set(self.canvas.selected)); self.canvas.update()
    def _atom_selection(self,selected): self.inspector.set_selection(self.canvas.molecule,selected)
    def _coordinates_changed(self): self.inspector.refresh_values(); self.code.setPlainText(generate_lua(self.project))
    def _commit_drag(self,before,after):
        if before!=after: self.undo_stack.push(MoveAtomsCommand(self,before,after)); self.mark_dirty()
    def _inspector_edited(self): self.canvas.update(); self.mark_dirty()
    def toggle_code(self): self.code_dock.setVisible(not self.code_dock.isVisible())
    def generate(self):
        try: path=write_mod(self.project,self.root); self.statusBar().showMessage(f"已生成 {path}"); self.code.setPlainText(generate_lua(self.project))
        except Exception as error: QMessageBox.critical(self,"生成失败",str(error))
    def render_still(self):
        self.generate(); exe=self.root/"build"/"release"/"chemanim.exe"
        if not exe.exists(): QMessageBox.information(self,"还未构建","请先在项目根目录运行 .\\build.ps1"); return
        try: subprocess.Popen([str(exe),self.project.mod,"--still"],cwd=self.root)
        except Exception as error: QMessageBox.critical(self,"无法启动渲染",str(error))


def save_window_screenshot(window: MainWindow, path: Path):
    path.parent.mkdir(parents=True,exist_ok=True); window.show()
    def prepare():
        window.canvas.fit()
        if window.canvas.molecule:
            atom=next((a for a in window.canvas.molecule.atoms if a.element not in {"C","H"}),window.canvas.molecule.atoms[0])
            window.canvas.selected={atom.id}; window.inspector.set_selection(window.canvas.molecule,{atom.id}); window.canvas.update()
    QTimer.singleShot(200,prepare)
    QTimer.singleShot(900,lambda:(window.grab().save(str(path)), window.close()))
