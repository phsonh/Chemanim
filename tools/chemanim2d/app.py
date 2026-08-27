from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QFont, QFontDatabase, QKeySequence
from PyQt6.QtWidgets import (QApplication, QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMenu, QMessageBox,
    QPushButton, QSlider, QSpinBox, QSplitter, QToolBar, QVBoxLayout, QWidget)

from .canvas import StructureCanvas
from .core import BUILD_COMMIT, DOCUMENT_VERSION, CoreSession
from .mode_toolbar import ModeToolPanel
from .node_inspector import NodeInspector
from .node_list import NodeList
from .periodic_table import PeriodicTableDialog
from .scene_inspector import SceneInspector


class SmilesDialog(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent);self.setWindowTitle("从 SMILES 生成视觉起稿")
        self.name=QLineEdit("新分子");self.smiles=QLineEdit("CC(=O)NC1=CC=C(O)C=C1")
        form=QFormLayout();form.addRow("名称",self.name);form.addRow("SMILES",self.smiles)
        note=QLabel("SMILES 只在导入时由 RDKit 展平成显式单、双、三键；之后只服从 Core 保存的视觉数据。");note.setWordWrap(True)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject)
        layout=QVBoxLayout(self);layout.addLayout(form);layout.addWidget(note);layout.addWidget(buttons);self.resize(600,170)


class MainWindow(QMainWindow):
    def __init__(self,root:Path):
        super().__init__();self.root=root;self.path=None;self.dirty=False;self.session=CoreSession();self.session.add_blank_molecule("molecule1");self._context_hit={"kind":"none","id":""};self._playing=False
        QFontDatabase.addApplicationFont("C:/Windows/Fonts/msyh.ttc");font=QFont("Microsoft YaHei UI");font.setPointSizeF(10.5);self.setFont(font)
        self.setWindowTitle("Chemanim");self.resize(1600,980)
        self.setStyleSheet("""
          QMainWindow,QDialog{background:#1d1f22;color:#e5e8ec} QMenuBar,QMenu,QToolBar,QStatusBar{background:#202327;color:#e5e8ec;border-color:#343940}
          QWidget#modeToolPanel{background:#181a1d;border-bottom:1px solid #3a3f46} QScrollArea,QScrollArea>QWidget>QWidget{background:#181a1d;border:0}
          QTabBar#primaryTabs::tab{min-width:88px;padding:8px 20px;background:#25292e;color:#b9c1ca;border:1px solid #41474f;border-bottom:0;margin-right:3px;border-top-left-radius:4px;border-top-right-radius:4px}
          QTabBar#primaryTabs::tab:selected{background:#31577f;color:#ffffff;border-color:#568ac0}
          QWidget#secondaryRow{background:#202328;border-top:1px solid #3b424a;border-bottom:1px solid #3b424a}
          QTabBar#secondaryTabs::tab{min-width:76px;padding:6px 16px;background:#202328;color:#aeb7c2;border:0;border-bottom:3px solid transparent;margin-right:2px}
          QTabBar#secondaryTabs::tab:selected{color:#ffffff;background:#29323c;border-bottom-color:#55a1e8}
          QWidget#tertiaryTools{background:#15181b;border-top:0}
          QPushButton{background:#2a2e33;color:#e5e8ec;border:1px solid #41474f;padding:5px 12px} QPushButton:hover{background:#343a41}
          QToolButton{background:transparent;color:#e5e8ec;border:1px solid transparent;padding:4px 7px} QToolButton:hover{background:#2b3036;border-color:#414852} QToolButton:checked{background:#285b91;border-color:#54a4ee}
          QTreeWidget,QLineEdit,QPlainTextEdit,QComboBox,QSpinBox,QDoubleSpinBox{background:#24272b;color:#e7e9ec;border:1px solid #3b4148;selection-background-color:#2467a5}
          QLabel{color:#e4e7eb} QLabel#inspectorTitle{font-size:16px;font-weight:600;padding:6px 0} QLabel[toolGroup="true"]{color:#aeb7c2;font-weight:600;padding:0 4px}
          QSplitter::handle{background:#31363c}
        """)
        self._build_actions();self._build_menu()
        self.mode_panel=ModeToolPanel(self.session);self.mode_panel.nodeRequested.connect(self._add_node);self.mode_panel.drawToolRequested.connect(self._set_tool);self.mode_panel.elementRequested.connect(self._set_element);self.mode_panel.periodicTableRequested.connect(self.choose_element)
        self.node_list=NodeList(self.session);self.node_list.setMinimumWidth(420);self.node_list.setMaximumWidth(600);self.node_list.nodeSelected.connect(self._node_selected);self.node_list.editRequested.connect(self._edit_node_dialog);self.node_list.frameRequested.connect(self._set_frame);self.node_list.sequenceEdited.connect(self._sequence_edited);self.node_list.undoRequested.connect(self.undo);self.node_list.redoRequested.connect(self.redo)
        self.canvas=StructureCanvas(self.session);self.canvas.selectionChanged.connect(self._selection);self.canvas.transactionCommitted.connect(self._transaction);self.canvas.hoverChanged.connect(self._hover);self.canvas.zoomChanged.connect(self._zoom_status);self.canvas.contextRequested.connect(self._canvas_context);self.canvas.undoRequested.connect(self.undo);self.canvas.redoRequested.connect(self.redo)
        split=QSplitter();split.addWidget(self.node_list);split.addWidget(self.canvas);split.setSizes([440,1160])
        self._build_transport()
        center=QWidget();layout=QVBoxLayout(center);layout.setContentsMargins(0,0,0,0);layout.setSpacing(0);layout.addWidget(self.mode_panel);layout.addWidget(split,1);layout.addWidget(self.transport);self.setCentralWidget(center)
        self.play_timer=QTimer(self);self.play_timer.timeout.connect(self._play_tick)
        self.refresh_all();self.canvas.request_refresh();self.canvas.setFocus();self.statusBar().showMessage(f"Core {BUILD_COMMIT[:12]} · 文档 v{DOCUMENT_VERSION} · 100%")

    def _action(self,text,slot,shortcut=None,checkable=False):
        action=QAction(text,self);action.triggered.connect(slot);action.setCheckable(checkable)
        if shortcut:action.setShortcut(shortcut)
        return action

    def _build_actions(self):
        self.actions={"new":self._action("新建",self.new_project,QKeySequence.StandardKey.New),"open":self._action("打开",self.open_project,QKeySequence.StandardKey.Open),"save":self._action("保存",self.save,QKeySequence.StandardKey.Save),"undo":self._action("撤销",self.undo,QKeySequence.StandardKey.Undo),"redo":self._action("重做",self.redo,QKeySequence.StandardKey.Redo),"delete":self._action("删除",self._delete_focused,QKeySequence.StandardKey.Delete),"duplicate":self._action("复制节点",self._duplicate_focused,"Ctrl+D"),"lua":self._action("生成 Lua",self.generate_lua,"F6"),"render":self._action("渲染 MP4",self.render_mp4,"F5"),"fit":self._action("适配画板",self.canvas_fit,"F"),"fit_all":self._action("适配全部内容",self.canvas_fit_all,"Shift+F"),"final":self._action("最终效果预览",lambda checked:self.canvas.set_final_effect(checked),checkable=True),"blank":self._action("空白分子",self.add_blank,"Ctrl+Shift+M"),"smiles":self._action("SMILES 起稿",self.add_smiles,"Ctrl+M")}

    def _build_menu(self):
        file=self.menuBar().addMenu("文件");[file.addAction(self.actions[k]) for k in ("new","open","save")];file.addSeparator();[file.addAction(self.actions[k]) for k in ("lua","render")]
        edit=self.menuBar().addMenu("编辑");edit.addAction(self.actions["undo"]);edit.addAction(self.actions["redo"]);edit.addSeparator();edit.addAction(self.actions["duplicate"]);edit.addAction(self.actions["delete"])
        view=self.menuBar().addMenu("视图");[view.addAction(self.actions[k]) for k in ("fit","fit_all","final")]
        build=self.menuBar().addMenu("构建");build.addAction(self.actions["blank"]);build.addAction(self.actions["smiles"])
        bar=QToolBar("快捷",self);bar.setMovable(False);bar.setFloatable(False)
        for key in ("new","open","save","undo","redo","lua","render"):bar.addAction(self.actions[key])
        self.addToolBar(bar)

    def _build_transport(self):
        self.transport=QWidget();layout=QHBoxLayout(self.transport);layout.setContentsMargins(8,4,8,4)
        self.play_button=QPushButton("▶ 播放");self.play_button.clicked.connect(self._toggle_play);self.edit_mode=QLabel("编辑：基础结构")
        self.frame_slider=QSlider(Qt.Orientation.Horizontal);self.frame_spin=QSpinBox();self.frame_spin.setRange(0,100000);self.frame_slider.setRange(0,0);self.frame_slider.valueChanged.connect(self.frame_spin.setValue);self.frame_spin.valueChanged.connect(self.frame_slider.setValue);self.frame_spin.valueChanged.connect(self._preview_frame)
        layout.addWidget(self.play_button);layout.addWidget(self.edit_mode);layout.addWidget(QLabel("当前帧"));layout.addWidget(self.frame_slider,1);layout.addWidget(self.frame_spin)

    def _toggle_play(self):
        self._playing=not self._playing;self.play_button.setText("■ 停止" if self._playing else "▶ 播放")
        if self._playing:self.play_timer.start(max(1,round(1000/max(1,self.session.project().get("scene",{}).get("fps",60)))))
        else:self.play_timer.stop()
    def _play_tick(self):
        end=max(0,self.session.end_frame);self.frame_spin.setValue(0 if self.frame_spin.value()>=end else self.frame_spin.value()+1)

    def mark_dirty(self):self.dirty=True;self._title()
    def _title(self):self.setWindowTitle(("*" if self.dirty else "")+(self.path.name if self.path else "未命名.cmm")+" — Chemanim")
    def _zoom_status(self,scale):self.statusBar().showMessage(f"Core {BUILD_COMMIT[:12]} · 缩放 {scale*100:.0f}%")
    def canvas_fit(self):self.canvas.fit_artboard()
    def canvas_fit_all(self):self.canvas.fit_all()
    def refresh_all(self,selected_node=""):
        self.node_list.refresh(selected_node);end=max(0,self.session.end_frame);self.frame_slider.setRange(0,end);self.frame_spin.setRange(0,max(100,end));self.canvas.request_refresh();self._title()
    def _transaction(self):self.mark_dirty();self.refresh_all(self.node_list.current_id())
    def _sequence_edited(self):self.mark_dirty();self.refresh_all(self.node_list.current_id());self.canvas.set_preview_frame(self.frame_spin.value())
    def _selection(self,atoms,bonds):pass
    def _delete_focused(self):
        focus=QApplication.focusWidget()
        if focus is self.node_list.tree or self.node_list.isAncestorOf(focus):self.node_list.delete()
        elif self.session.delete_selection():self._transaction()
    def _duplicate_focused(self):
        focus=QApplication.focusWidget()
        if focus is self.node_list.tree or self.node_list.isAncestorOf(focus):self.node_list.duplicate()
    def _hover(self,value):
        if value["kind"]!="none":self.statusBar().showMessage(f'{value["kind"]} · Core {BUILD_COMMIT[:12]}')
    def _set_tool(self,value):self.mode_panel.mode="绘制";self.session.edit_base(self.frame_spin.value());self.canvas.set_base_edit(True);self.session.set_tool(value);self.edit_mode.setText("编辑：基础结构");self.node_list.tree.clearSelection();self.statusBar().showMessage(f"绘制工具：{value}")
    def _set_element(self,value):self.session.set_element(value);self._set_tool("atom_label")
    def choose_element(self):
        dialog=PeriodicTableDialog(self)
        if dialog.exec()==QDialog.DialogCode.Accepted and dialog.selected_element:self._set_element(dialog.selected_element)

    def _latest_arrow(self,before):
        alive=[]
        for node in self.session.project().get("nodes",[])[:before]:
            target=node.get("params",{}).get("target","")
            if node["type"]=="arrow_new" and target:alive.append(target)
            elif node["type"]=="arrow_delete" and target in alive:alive.remove(target)
        return alive[-1] if alive else ""

    def _add_node(self,node_type,seed=None,open_editor=True):
        project=self.session.project();nodes=project.get("nodes",[]);current=self.node_list.current_id();index=next((i+1 for i,n in enumerate(nodes) if n["id"]==current),len(nodes))
        if node_type=="scene":self._scene_dialog();return ""
        node_id=self.session.add_node(node_type,"{}",index);project=self.session.project();node=next(item for item in project["nodes"] if item["id"]==node_id);params=dict(node.get("params",{}));params.update(seed or {})
        definition=next((item for item in self.session.node_registry() if item["type"]==node_type),{})
        if any(field.get("key")=="target" and field.get("kind")=="molecule" for field in definition.get("fields",[])) and not params.get("target"):params["target"]=self.session.active_molecule
        if node_type.startswith("atom_") and self.canvas.selected_atoms and not params.get("atom"):params["atom"]=self.canvas.selected_atoms[-1]
        if node_type.startswith("bond_") and self.canvas.selected_bonds and not params.get("bond"):params["bond"]=self.canvas.selected_bonds[-1]
        if node_type=="arrow_new":
            used=[int(m.group(1)) for item in project["nodes"] if item["type"]=="arrow_new" for m in [re.fullmatch(r"arrow(\d+)",item.get("params",{}).get("target",""))] if m];params["target"]=f"arrow{max(used,default=0)+1}"
        elif node_type.startswith("arrow_") and not params.get("target"):params["target"]=self._latest_arrow(index)
        self.session.update_node(node_id,json.dumps(params,ensure_ascii=False));self.mark_dirty();self.refresh_all(node_id);self._node_selected(node_id)
        if open_editor:self._edit_node_dialog(node_id)
        return node_id

    def _node_selected(self,node_id):
        node=next((item for item in self.session.project().get("nodes",[]) if item["id"]==node_id),None)
        if not node:return
        timing=next((item for item in self.session.node_timings() if item["id"]==node_id),{"end":0});self._set_frame(timing["end"])
        self.canvas.set_base_edit(False)
        if node["type"]=="scene":self.edit_mode.setText("编辑：场景")
        else:self.session.edit_node(node_id);self.edit_mode.setText(f"编辑节点：{node.get('type','')}")

    def _edit_node_dialog(self,node_id):
        node=next((item for item in self.session.project().get("nodes",[]) if item["id"]==node_id),None)
        if not node:return
        if node["type"]=="scene":self._scene_dialog();return
        dialog=QDialog(self);dialog.setWindowTitle("节点参数");inspector=NodeInspector(self.session,dialog);inspector.set_node(node_id);inspector.nodeEdited.connect(lambda _id:(self.mark_dirty(),self.refresh_all(node_id),self.canvas.set_preview_frame(self.frame_spin.value())))
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Close);buttons.rejected.connect(dialog.reject)
        layout=QVBoxLayout(dialog);layout.addWidget(inspector);layout.addWidget(buttons);dialog.resize(430,max(240,min(720,inspector.sizeHint().height()+100)));dialog.exec()

    def _context_seed(self,kind,stable_id,node_type):
        project=self.session.evaluated_project(self.frame_spin.value());molecule=next((m for m in project.get("molecules",[]) if m["id"]==self.session.active_molecule),{})
        seed={"target":self.session.active_molecule}
        if node_type.startswith("molecule_"):
            alive=[a for a in molecule.get("atoms",[]) if a.get("alive",True)]
            if alive:
                anchor=min(alive,key=lambda a:a.get("creation_serial",0));seed.update(x=anchor.get("x",0.0),y=anchor.get("y",0.0))
            if "alpha" in node_type:seed["value"]=molecule.get("alpha",255)
            elif "scale" in node_type:seed["value"]=molecule.get("scale",1.0)
            elif "rotation" in node_type:seed["value"]=molecule.get("rotation",0.0)
            elif "color" in node_type:seed.update(molecule.get("color",{"r":255,"g":255,"b":255}))
        elif kind=="atom":
            seed["atom"]=stable_id;value=next((a for a in molecule.get("atoms",[]) if a["id"]==stable_id),{})
            if "_xy" in node_type:seed.update(x=value.get("x",0.0),y=value.get("y",0.0))
            elif "alpha" in node_type:seed["value"]=value.get("alpha",255)
            elif "color" in node_type:seed.update(value.get("color",{"r":0,"g":0,"b":0}))
            elif "element" in node_type:seed["value"]=value.get("element","C")
        elif kind=="bond":
            seed["bond"]=stable_id;value=next((b for b in molecule.get("bonds",[]) if b["id"]==stable_id),{})
            if "alpha" in node_type:seed["value"]=value.get("alpha",255)
            elif "color" in node_type:seed.update(value.get("color",{"r":0,"g":0,"b":0}))
            elif "order" in node_type:seed["value"]=value.get("type","single")
            elif "secondary" in node_type:seed["value"]=value.get("secondary_line_side","center")
        elif kind=="adornment":
            seed["adornment"]=stable_id;value=next((a for a in molecule.get("adornments",[]) if a["id"]==stable_id),{})
            if "offset" in node_type:seed.update(x=value.get("x",0.0),y=value.get("y",0.0))
            elif "alpha" in node_type:seed["value"]=value.get("alpha",255)
            elif "color" in node_type:seed.update(value.get("color",{"r":0,"g":0,"b":0}))
            elif "text" in node_type:seed["value"]=value.get("text","⊕")
        return seed

    def _scene_dialog(self):
        dialog=QDialog(self);dialog.setWindowTitle("场景设置");inspector=SceneInspector(self.session,dialog);inspector.refresh();inspector.sceneEdited.connect(lambda:(self.mark_dirty(),self.canvas.fit_artboard()))
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Close);buttons.rejected.connect(dialog.reject);layout=QVBoxLayout(dialog);layout.addWidget(inspector);layout.addWidget(buttons);dialog.resize(480,420);dialog.exec();self.refresh_all(self.node_list.current_id())

    def _canvas_context(self,hit,global_pos):
        self._context_hit=hit;kind=hit.get("kind","none");target=self.session.active_molecule
        menu=QMenu(self);objects=[("分子",{"position":("坐标","molecule_set_position","molecule_lerp_position"),"alpha":("透明度","molecule_set_alpha","molecule_lerp_alpha"),"color":("颜色","molecule_set_color","molecule_lerp_color"),"scale":("缩放","molecule_set_scale","molecule_lerp_scale"),"rotation":("旋转","molecule_set_rotation","molecule_lerp_rotation")})]
        if kind=="atom":objects.append(("原子",{"xy":("坐标","atom_set_xy","atom_lerp_xy"),"alpha":("透明度","atom_set_alpha","atom_lerp_alpha"),"color":("颜色","atom_set_color","atom_lerp_color"),"element":("元素/文字","atom_set_element",None)}))
        elif kind=="bond":objects.append(("键",{"alpha":("透明度","bond_set_alpha","bond_lerp_alpha"),"color":("颜色","bond_set_color","bond_lerp_color"),"type":("视觉键型","bond_set_order",None),"secondary":("双键副线方向","bond_set_secondary_side",None)}))
        elif kind=="adornment":objects.append(("形式电荷",{"offset":("坐标","adornment_set_offset","adornment_lerp_offset"),"alpha":("透明度","adornment_set_alpha","adornment_lerp_alpha"),"color":("颜色","adornment_set_color","adornment_lerp_color")}))
        for object_label,properties in objects:
            root=menu.addMenu(object_label);set_menu=root.addMenu("设定");lerp_menu=root.addMenu("插值")
            for _key,(label,set_type,lerp_type) in properties.items():
                object_kind=kind if object_label!="分子" else "molecule"
                object_id=hit.get("id","") if object_label!="分子" else target
                seed=self._context_seed(object_kind,object_id,set_type)
                action=QAction(label,set_menu);action.triggered.connect(lambda checked=False,t=set_type,s=dict(seed):self._add_node(t,s));set_menu.addAction(action)
                if lerp_type:
                    lerp_seed=self._context_seed(object_kind,object_id,lerp_type)
                    action=QAction(label,lerp_menu);action.triggered.connect(lambda checked=False,t=lerp_type,s=dict(lerp_seed):self._add_node(t,s));lerp_menu.addAction(action)
            if not lerp_menu.actions():lerp_menu.setEnabled(False)
        menu.exec(global_pos)

    def _set_frame(self,frame):self.frame_spin.setValue(frame)
    def _preview_frame(self,frame):self.canvas.set_preview_frame(frame)
    def new_project(self):self.session.new_project();self.session.add_blank_molecule("molecule1");self.canvas.set_base_edit(True);self.path=None;self.dirty=False;self.refresh_all();self.canvas.fit_artboard()
    def add_blank(self):stable_id=self.session.add_blank_molecule("");self.mark_dirty();self.refresh_all();self.statusBar().showMessage(f"已新建 {stable_id}")
    def add_smiles(self):
        dialog=SmilesDialog(self)
        if dialog.exec()!=QDialog.DialogCode.Accepted:return
        try:stable_id=self.session.import_smiles(dialog.name.text().strip(),dialog.smiles.text().strip())
        except Exception as error:QMessageBox.warning(self,"无法导入",str(error));return
        self.mark_dirty();self.refresh_all();self.canvas.fit_all();self.statusBar().showMessage(f"已导入 {stable_id}")
    def open_project(self):
        name,_=QFileDialog.getOpenFileName(self,"打开工程",str(self.root/"mod"),"Chemanim (*.cmm)")
        if name:self.load(Path(name))
    def load(self,path:Path):
        try:self.session.load(str(path))
        except Exception as error:QMessageBox.critical(self,"无法打开",str(error));return
        self.canvas.set_base_edit(True);self.path=path;self.dirty=False;self.refresh_all();self.canvas.fit_artboard()
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
