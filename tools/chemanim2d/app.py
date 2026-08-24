from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QFont, QFontDatabase, QKeySequence
from PyQt6.QtWidgets import (QDialog, QDialogButtonBox, QDockWidget, QFileDialog,
    QFormLayout, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QMainWindow,
    QMenu, QMessageBox, QPushButton, QSlider, QSpinBox, QSplitter,
    QStackedWidget, QToolBar, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from .canvas import StructureCanvas
from .core import BUILD_COMMIT, DOCUMENT_VERSION, CoreSession
from .inspector import AtomInspector
from .mode_toolbar import ModeToolPanel
from .node_inspector import NodeInspector
from .node_list import NodeList
from .scene_inspector import SceneInspector


class SmilesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowTitle("从 SMILES 生成起稿")
        self.name=QLineEdit("新分子");self.smiles=QLineEdit("CC(=O)NC1=CC=C(O)C=C1")
        form=QFormLayout();form.addRow("名称",self.name);form.addRow("SMILES",self.smiles)
        note=QLabel("SMILES 仅用于导入起稿；此后 C++ Core 的 atom/bond/XY 与稳定 ID 是权威数据。");note.setWordWrap(True)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject)
        layout=QVBoxLayout(self);layout.addLayout(form);layout.addWidget(note);layout.addWidget(buttons);self.resize(560,150)


class MainWindow(QMainWindow):
    def __init__(self, root: Path):
        super().__init__();self.root=root;self.path=None;self.dirty=False;self.session=CoreSession();self.session.add_blank_molecule("molecule1")
        QFontDatabase.addApplicationFont("C:/Windows/Fonts/msyh.ttc");self.setFont(QFont("Microsoft YaHei UI",9))
        self.setWindowTitle("Chemanim");self.resize(1580,960)
        self.setStyleSheet("""
            QMainWindow, QDialog { background:#1d1f22; color:#e5e8ec; }
            QMenuBar, QMenu, QToolBar, QStatusBar { background:#202327; color:#e5e8ec; border-color:#343940; }
            QWidget#modeToolPanel { background:#181a1d; border-bottom:1px solid #3a3f46; }
            QScrollArea, QScrollArea > QWidget > QWidget { background:#181a1d; border:0; }
            QPushButton { background:#2a2e33; color:#e5e8ec; border:1px solid #41474f; padding:4px 10px; }
            QPushButton:hover { background:#343a41; }
            QPushButton[level="primary"], QPushButton[level="secondary"] { background:#25292e; color:#dfe4ea; border:1px solid #3a4048; padding:3px 18px; }
            QPushButton[level="primary"]:checked, QPushButton[level="secondary"]:checked { background:#35577e; border-color:#4f86c3; }
            QToolButton { background:transparent; color:#e5e8ec; border:1px solid transparent; padding:3px; }
            QToolButton:hover { background:#2b3036; border-color:#414852; }
            QToolButton:checked { background:#285b91; border-color:#54a4ee; }
            QTreeWidget, QLineEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox { background:#24272b; color:#e7e9ec; border:1px solid #3b4148; selection-background-color:#2467a5; }
            QDockWidget, QLabel { color:#e4e7eb; }
            QLabel#inspectorTitle { font-size:16px; font-weight:600; padding:6px 0; }
            QLabel[toolGroup="true"] { color:#9fa8b3; font-size:11px; padding:0 4px; }
            QSplitter::handle { background:#31363c; }
        """)
        self._build_actions();self._build_menu_and_shortcuts()

        self.tree=QTreeWidget();self.tree.setHeaderLabels(["结构","稳定 ID"]);self.tree.currentItemChanged.connect(self._tree_selection)
        self.canvas=StructureCanvas(self.session);self.canvas.selectionChanged.connect(self._selection);self.canvas.transactionCommitted.connect(self._transaction);self.canvas.hoverChanged.connect(self._hover);self.canvas.zoomChanged.connect(self._zoom_status)
        self.atom_inspector=AtomInspector(self.session);self.atom_inspector.atomEdited.connect(self._transaction)
        self.node_inspector=NodeInspector(self.session);self.node_inspector.nodeEdited.connect(self._node_edited)
        self.scene_inspector=SceneInspector(self.session);self.scene_inspector.sceneEdited.connect(self._scene_edited)
        self.blank_inspector=QLabel("选择节点或一个原子以编辑参数");self.blank_inspector.setAlignment(Qt.AlignmentFlag.AlignTop|Qt.AlignmentFlag.AlignLeft);self.blank_inspector.setMargin(14)
        self.inspector_stack=QStackedWidget();self.inspector_stack.addWidget(self.blank_inspector);self.inspector_stack.addWidget(self.atom_inspector);self.inspector_stack.addWidget(self.node_inspector);self.inspector_stack.addWidget(self.scene_inspector)
        split=QSplitter();split.addWidget(self.tree);split.addWidget(self.canvas);split.addWidget(self.inspector_stack);split.setSizes([255,1040,285])
        self.mode_panel=ModeToolPanel(self.session);self.mode_panel.nodeRequested.connect(self._add_node);self.mode_panel.drawToolRequested.connect(self._set_tool);self.mode_panel.elementRequested.connect(self._set_element);self.mode_panel.periodicTableRequested.connect(self.choose_element);self.mode_panel.groupPanelRequested.connect(self.show_group_panel)
        center=QWidget();layout=QVBoxLayout(center);layout.setContentsMargins(0,0,0,0);layout.setSpacing(0);layout.addWidget(self.mode_panel);layout.addWidget(split,1);self.setCentralWidget(center)
        self._build_node_dock()
        self.refresh_all();self.canvas.request_refresh();self.canvas.setFocus()
        self.statusBar().showMessage(f"Core {BUILD_COMMIT[:12]} · 文档 v{DOCUMENT_VERSION} · 100%")

    def _action(self,text,slot,shortcut=None,checkable=False):
        action=QAction(text,self);action.triggered.connect(slot);action.setCheckable(checkable)
        if shortcut:action.setShortcut(shortcut)
        return action

    def _build_actions(self):
        self.actions={
            "new":self._action("新建",self.new_project,QKeySequence.StandardKey.New),"open":self._action("打开",self.open_project,QKeySequence.StandardKey.Open),"save":self._action("保存",self.save,QKeySequence.StandardKey.Save),
            "undo":self._action("撤销",self.undo,QKeySequence.StandardKey.Undo),"redo":self._action("重做",self.redo,QKeySequence.StandardKey.Redo),"lua":self._action("生成 Lua",self.generate_lua,"F6"),"render":self._action("渲染 MP4",self.render_mp4,"F5"),
            "fit":self._action("适配画板",self.canvas_fit,"F"),"fit_all":self._action("适配全部内容",self.canvas_fit_all,"Shift+F"),"final":self._action("最终效果预览",lambda checked:self.canvas.set_final_effect(checked),checkable=True),
            "blank":self._action("空白分子",self.add_blank,"Ctrl+Shift+M"),"smiles":self._action("SMILES 起稿",self.add_smiles,"Ctrl+M")}

    def _build_menu_and_shortcuts(self):
        file_menu=self.menuBar().addMenu("文件");[file_menu.addAction(self.actions[key]) for key in ("new","open","save")];file_menu.addSeparator();[file_menu.addAction(self.actions[key]) for key in ("lua","render")]
        edit=self.menuBar().addMenu("编辑");edit.addAction(self.actions["undo"]);edit.addAction(self.actions["redo"])
        view=self.menuBar().addMenu("视图");[view.addAction(self.actions[key]) for key in ("fit","fit_all","final")]
        build=self.menuBar().addMenu("构建");build.addAction(self.actions["blank"]);build.addAction(self.actions["smiles"])
        bar=QToolBar("快捷",self);bar.setMovable(False);bar.setFloatable(False);bar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        for key in ("new","open","save","undo","redo","lua","render"):bar.addAction(self.actions[key])
        self.addToolBar(bar)

    def _build_node_dock(self):
        dock=QDockWidget("线性节点 · 创作层",self);dock.setObjectName("linearNodesDock")
        panel=QWidget();layout=QVBoxLayout(panel);layout.setContentsMargins(4,4,4,4)
        self.node_list=NodeList(self.session);self.node_list.nodeSelected.connect(self._node_selected);self.node_list.frameRequested.connect(self._set_frame);self.node_list.sequenceEdited.connect(self._sequence_edited);layout.addWidget(self.node_list,1)
        row=QHBoxLayout();self.edit_mode=QLabel("编辑：基础结构");self.edit_mode.setMinimumWidth(190);self.frame_slider=QSlider(Qt.Orientation.Horizontal);self.frame_spin=QSpinBox();self.frame_spin.setRange(0,100000);self.frame_slider.setRange(0,0);self.frame_slider.valueChanged.connect(self.frame_spin.setValue);self.frame_spin.valueChanged.connect(self.frame_slider.setValue);self.frame_spin.valueChanged.connect(self._preview_frame)
        row.addWidget(self.edit_mode);row.addWidget(QLabel("预览帧"));row.addWidget(self.frame_slider,1);row.addWidget(self.frame_spin);layout.addLayout(row)
        dock.setWidget(panel);self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea,dock)

    def mark_dirty(self):self.dirty=True;self._title()
    def _title(self):self.setWindowTitle(("*" if self.dirty else "")+(self.path.name if self.path else "未命名.cmm")+" — Chemanim")
    def _zoom_status(self,scale):self.statusBar().showMessage(f"Core {BUILD_COMMIT[:12]} · 缩放 {scale*100:.0f}%")
    def canvas_fit(self):self.canvas.fit_artboard()
    def canvas_fit_all(self):self.canvas.fit_all()

    def refresh_tree(self):
        current=self.session.active_molecule;self.tree.clear()
        for molecule in self.session.project().get("molecules",[]):
            root=QTreeWidgetItem([molecule["name"],molecule["id"]]);root.setData(0,Qt.ItemDataRole.UserRole,("molecule",molecule["id"]));self.tree.addTopLevelItem(root)
            atoms=QTreeWidgetItem([f'原子 ({len(molecule["atoms"])})',""]);root.addChild(atoms)
            for atom in molecule["atoms"]:
                item=QTreeWidgetItem([f'{atom["element"]}  ({atom["x"]:.2f}, {atom["y"]:.2f})',atom["id"]]);item.setData(0,Qt.ItemDataRole.UserRole,("atom",molecule["id"],atom["id"]));atoms.addChild(item)
            bonds=QTreeWidgetItem([f'键 ({len(molecule["bonds"])})',""]);root.addChild(bonds)
            for bond in molecule["bonds"]:
                display=f' · 显示 {bond["display_type"]}' if bond.get("display_type") else "";item=QTreeWidgetItem([f'{bond["a"]}—{bond["b"]}  {bond["type"]}{display}',bond["id"]]);item.setData(0,Qt.ItemDataRole.UserRole,("bond",molecule["id"],bond["id"]));bonds.addChild(item)
            root.setExpanded(molecule["id"]==current);atoms.setExpanded(molecule["id"]==current)

    def refresh_all(self,selected_node=""):
        self.refresh_tree();self.node_list.refresh(selected_node);end=max(0,self.session.end_frame);self.frame_slider.setRange(0,end);self.frame_spin.setRange(0,max(100,end));self.scene_inspector.refresh();self.atom_inspector.refresh_values();self.canvas.request_refresh();self._title()

    def _transaction(self):self.mark_dirty();self.refresh_all(self.node_list.current_id())
    def _node_edited(self,node_id):self.mark_dirty();self.refresh_all(node_id);self.canvas.set_preview_frame(self.frame_spin.value())
    def _scene_edited(self):self.mark_dirty();self.refresh_all(self.node_list.current_id());self.canvas.fit_artboard()
    def _sequence_edited(self):self.mark_dirty();self.refresh_all(self.node_list.current_id());self.canvas.set_preview_frame(self.frame_spin.value())
    def _hover(self,value):
        if value["kind"]!="none":self.statusBar().showMessage(f'{value["kind"]} {value["id"]} · Core {BUILD_COMMIT[:12]}')

    def _tree_selection(self,item,previous):
        if not item:return
        data=item.data(0,Qt.ItemDataRole.UserRole)
        if not data:return
        if data[1]!=self.session.active_molecule:self.session.set_active_molecule(data[1]);self.canvas.request_refresh()
        if data[0]=="atom":self.atom_inspector.set_selection([data[2]],[]);self.inspector_stack.setCurrentWidget(self.atom_inspector)

    def _selection(self,atoms,bonds):
        self.atom_inspector.set_selection(atoms,bonds)
        if len(atoms)==1 and not self.node_list.current_id():self.inspector_stack.setCurrentWidget(self.atom_inspector)

    def _set_tool(self,value):
        self.session.edit_base(self.frame_spin.value());self.session.set_tool(value);self.edit_mode.setText("编辑：基础结构");self.node_list.tree.clearSelection();self.inspector_stack.setCurrentWidget(self.atom_inspector);self.statusBar().showMessage(f"绘制工具：{value}")

    def _set_element(self,value):self.session.set_element(value);self._set_tool("atom_label")
    def choose_element(self):
        elements=("H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og").split()
        value,ok=QInputDialog.getItem(self,"周期表","元素",elements,elements.index("C"),False)
        if ok:self._set_element(value)

    def show_group_panel(self):
        QMessageBox.information(self,"基团 Registry","基团面板使用数据驱动 registry；当前 registry 为空，因此不显示不可用的假按钮。")

    def _latest_arrow(self,before_index):
        alive=[]
        for node in self.session.project().get("nodes",[])[:before_index]:
            target=node.get("params",{}).get("target","")
            if node["type"]=="arrow_new" and target:alive.append(target)
            elif node["type"]=="arrow_delete" and target in alive:alive.remove(target)
        return alive[-1] if alive else ""

    def _add_node(self,node_type):
        project=self.session.project();nodes=project.get("nodes",[]);current=self.node_list.current_id();index=next((i+1 for i,n in enumerate(nodes) if n["id"]==current),len(nodes))
        if node_type=="scene":
            existing=next((node["id"] for node in nodes if node["type"]=="scene"),"")
            if existing:self.node_list.refresh(existing);self._node_selected(existing);return
        node_id=self.session.add_node(node_type,"{}",index);project=self.session.project();node=next(item for item in project["nodes"] if item["id"]==node_id);params=dict(node.get("params",{}))
        if any(field.get("key")=="target" and field.get("kind")=="molecule" for definition in self.session.node_registry() if definition["type"]==node_type for field in definition.get("fields",[])):params["target"]=self.session.active_molecule
        if node_type.startswith("atom_") and self.canvas.selected_atoms:params["atom"]=self.canvas.selected_atoms[-1]
        if node_type.startswith("bond_") and self.canvas.selected_bonds:params["bond"]=self.canvas.selected_bonds[-1]
        if node_type=="arrow_new":
            used=[int(match.group(1)) for item in project["nodes"] if item["type"]=="arrow_new" for match in [re.fullmatch(r"arrow(\d+)",item.get("params",{}).get("target",""))] if match];params["target"]=f"arrow{max(used,default=0)+1}"
        elif node_type.startswith("arrow_"):params["target"]=self._latest_arrow(index)
        self.session.update_node(node_id,json.dumps(params));self.mark_dirty();self.refresh_all(node_id);self._node_selected(node_id)

    def _node_selected(self,node_id):
        node=next((item for item in self.session.project().get("nodes",[]) if item["id"]==node_id),None)
        if not node:return
        timing=next((item for item in self.session.node_timings() if item["id"]==node_id),{"end":0});self._set_frame(timing["end"])
        if node["type"]=="scene":self.inspector_stack.setCurrentWidget(self.scene_inspector);self.scene_inspector.refresh();self.edit_mode.setText("编辑：Scene")
        else:self.node_inspector.set_node(node_id);self.inspector_stack.setCurrentWidget(self.node_inspector);self.session.edit_node(node_id);self.edit_mode.setText(f"编辑节点：{node_id}")

    def _set_frame(self,frame):self.frame_spin.setValue(frame)
    def _preview_frame(self,frame):self.canvas.set_preview_frame(frame)

    def new_project(self):self.session.new_project();self.session.add_blank_molecule("molecule1");self.path=None;self.dirty=False;self.refresh_all();self.canvas.fit_artboard()
    def add_blank(self):stable_id=self.session.add_blank_molecule("");self.mark_dirty();self.refresh_all();self.statusBar().showMessage(f"已新建 {stable_id}")
    def add_smiles(self):
        dialog=SmilesDialog(self)
        if dialog.exec()!=QDialog.DialogCode.Accepted:return
        try:stable_id=self.session.import_smiles(dialog.name.text().strip(),dialog.smiles.text().strip())
        except Exception as error:QMessageBox.warning(self,"无法导入",str(error));return
        self.mark_dirty();self.refresh_all();self.statusBar().showMessage(f"已导入 {stable_id}")
    def open_project(self):
        name,_=QFileDialog.getOpenFileName(self,"打开工程",str(self.root/"mod"),"Chemanim (*.cmm)")
        if name:self.load(Path(name))
    def load(self,path:Path):
        try:self.session.load(str(path))
        except Exception as error:QMessageBox.critical(self,"无法打开",str(error));return
        self.path=path;self.dirty=False;self.refresh_all();self.canvas.fit_artboard()
    def save(self):
        if not self.path:
            name,_=QFileDialog.getSaveFileName(self,"保存工程",str(self.root/"mod"/"native2d.cmm"),"Chemanim (*.cmm)")
            if not name:return
            self.path=Path(name)
        try:self.session.save(str(self.path))
        except Exception as error:QMessageBox.critical(self,"保存失败",str(error));return
        self.dirty=False;self._title();self.statusBar().showMessage(f"已保存 {self.path}")
    def undo(self):
        if self.session.undo():self.mark_dirty();self.refresh_all()
    def redo(self):
        if self.session.redo():self.mark_dirty();self.refresh_all()
    def generate_lua(self):
        try:path=self.session.write_mod(str(self.root))
        except Exception as error:QMessageBox.critical(self,"生成失败",str(error));return
        self.statusBar().showMessage(f"已由线性节点生成 {path}")
    def render_mp4(self):
        self.generate_lua();executable=self.root/"build"/"release"/"chemanim.exe"
        if not executable.exists():QMessageBox.information(self,"尚未构建","请先运行 .\\build.ps1");return
        try:subprocess.Popen([str(executable),self.session.project().get("mod","native2d_demo")],cwd=self.root)
        except Exception as error:QMessageBox.critical(self,"无法启动渲染",str(error))


def save_window_screenshot(window:MainWindow,path:Path):
    path.parent.mkdir(parents=True,exist_ok=True);window.show();QTimer.singleShot(250,window.canvas.fit_artboard);QTimer.singleShot(1100,lambda:(window.grab().save(str(path)),window.close()))
