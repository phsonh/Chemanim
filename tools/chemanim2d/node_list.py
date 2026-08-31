from __future__ import annotations

from PyQt6.QtCore import QEvent, Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence
from PyQt6.QtWidgets import (QHBoxLayout, QPushButton, QTreeWidget,
                             QTreeWidgetItem, QVBoxLayout, QWidget)

from .node_inspector import LEGACY_STRUCTURE_TYPES, molecule_name

EASING_NAMES={"linear":"线性","in_quad":"二次缓入","out_quad":"二次缓出","in_out_quad":"二次缓入缓出",
              "in_cubic":"三次缓入","out_cubic":"三次缓出","in_out_cubic":"三次缓入缓出"}


def _number(value):
    if isinstance(value,bool):return "是" if value else "否"
    if isinstance(value,float):return f"{value:g}"
    return str(value)


def _arrow_name(value):
    suffix="".join(character for character in str(value) if character.isdigit())
    return f"箭头 {suffix}" if suffix else str(value)


class NodeList(QWidget):
    nodeSelected = pyqtSignal(str)
    frameRequested = pyqtSignal(int)
    editRequested = pyqtSignal(str)
    sequenceEdited = pyqtSignal()
    undoRequested = pyqtSignal()
    redoRequested = pyqtSignal()
    operationRejected = pyqtSignal(str)

    def __init__(self, session, parent=None):
        super().__init__(parent); self.session = session; self._updating = False; self._copied_node_id = ""
        self.tree = QTreeWidget(); self.tree.setColumnCount(1);self.tree.setHeaderHidden(True)
        font=self.tree.font();font.setPointSizeF(max(10.5,font.pointSizeF()+1.0));self.tree.setFont(font)
        self.tree.setRootIsDecorated(False); self.tree.setUniformRowHeights(True)
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.tree.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)
        self.tree.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.tree.installEventFilter(self)
        self.tree.currentItemChanged.connect(self._selected); self.tree.itemDoubleClicked.connect(self._double_clicked)
        self.tree.model().rowsMoved.connect(self._rows_moved)
        buttons = QHBoxLayout()
        for text, callback in (("复制", self.duplicate), ("删除", self.delete), ("上移", lambda: self.move(-1)), ("下移", lambda: self.move(1))):
            button = QPushButton(text); button.clicked.connect(callback); buttons.addWidget(button)
        buttons.addStretch(1)
        layout = QVBoxLayout(self); layout.setContentsMargins(4, 4, 4, 4); layout.addWidget(self.tree); layout.addLayout(buttons)

    def eventFilter(self, watched, event):
        if watched is self.tree and event.type()==QEvent.Type.KeyPress:
            if event.matches(QKeySequence.StandardKey.Undo):self.undoRequested.emit();return True
            if event.matches(QKeySequence.StandardKey.Redo) or (event.key()==Qt.Key.Key_Z and event.modifiers()==(Qt.KeyboardModifier.ControlModifier|Qt.KeyboardModifier.ShiftModifier)):self.redoRequested.emit();return True
            if event.matches(QKeySequence.StandardKey.Copy):self.copy();return True
            if event.matches(QKeySequence.StandardKey.Paste):self.paste();return True
            if event.key() in (Qt.Key.Key_Delete,Qt.Key.Key_Backspace):self.delete();return True
            if event.key()==Qt.Key.Key_D and event.modifiers()==Qt.KeyboardModifier.ControlModifier:self.duplicate();return True
            if event.key()==Qt.Key.Key_Up and event.modifiers()==Qt.KeyboardModifier.AltModifier:self.move(-1);return True
            if event.key()==Qt.Key.Key_Down and event.modifiers()==Qt.KeyboardModifier.AltModifier:self.move(1);return True
        return super().eventFilter(watched,event)

    def current_id(self):
        item = self.tree.currentItem(); return item.data(0, Qt.ItemDataRole.UserRole) if item else ""

    @staticmethod
    def _target_name(project,definition,target):
        kind=definition.get("target_kind","")
        if kind=="molecule":return molecule_name(project,target)
        if kind=="arrow":return _arrow_name(target)
        if kind=="global_molecule":return "所有分子"
        if kind=="global_arrow":return "所有箭头"
        return str(target)

    @staticmethod
    def _parameter_value(definition,params):
        keys=[field.get("key","") for field in definition.get("fields",[]) if field.get("key") not in
              {"target","frames","easing","snapshot","start_snapshot","end_snapshot","coordinate_space","needs_review","code"}]
        if "x" in keys and "y" in keys:return f'({_number(params.get("x",0))}, {_number(params.get("y",0))})'
        if all(key in keys for key in ("r","g","b")):return f'RGB({_number(params.get("r",0))}, {_number(params.get("g",0))}, {_number(params.get("b",0))})'
        if len(keys)==1:return _number(params.get(keys[0],""))
        return ""

    @classmethod
    def _sentence(cls,node,definition,project):
        node_type=node.get("type","");params=node.get("params",{});label=definition.get("label","节点")
        if node_type=="scene":return "场景设置"
        if node_type=="wait":return f'等待 {_number(params.get("frames",30))} 帧'
        target=cls._target_name(project,definition,params.get("target",""));scope=definition.get("scope","")
        if node_type in LEGACY_STRUCTURE_TYPES:return f'旧版结构节点 · {target}' if target else "旧版结构节点"
        if node_type=="molecule_create":return f"新建{target}"
        if node_type=="arrow_new":return f"新建{target}"
        if scope=="object":return f"{label} {target}".strip()
        value=cls._parameter_value(definition,params);action=definition.get("tool_label") or definition.get("group") or label
        if definition.get("target_kind")=="molecule" and action.startswith("分子"):action=action[2:]
        if definition.get("target_kind")=="arrow" and action.startswith("箭头"):action=action[2:]
        if scope=="transform":
            frames=_number(params.get("frames",30));easing=EASING_NAMES.get(params.get("easing","linear"),params.get("easing","linear"))
            if node_type=="molecule_gradient_structure":return f"{frames} 帧内将{target}结构渐变为终态，{easing}"
            if node_type=="molecule_merge_gradient_structure":return f'{frames} 帧内将{target}与{molecule_name(project,params.get("source",""))}合并并变换结构，{easing}'
            if node_type=="molecule_split_gradient_structure":return f'{frames} 帧内将{target}分裂为自身与{molecule_name(project,params.get("destination",""))}，{easing}'
            destination=f"变为 {value}" if value else "变为目标状态"
            return f"{frames} 帧内将{target}{action}{destination}，{easing}"
        if scope=="set":return f"设定{target}{action}"+(f"为 {value}" if value else "")
        if scope=="global":return label+(f"为 {value}" if value else "")
        return f"{label} {target}".strip()

    def refresh(self, selected_id=""):
        selected_id = selected_id or self.current_id(); project = self.session.project()
        registry = {item["type"]: item for item in self.session.node_registry()}
        self._updating = True; self.tree.clear()
        for node in project.get("nodes", []):
            definition = registry.get(node["type"], {})
            item = QTreeWidgetItem([self._sentence(node,definition,project)])
            item.setFlags(item.flags()&~Qt.ItemFlag.ItemIsUserCheckable)
            item.setData(0, Qt.ItemDataRole.UserRole, node["id"])
            if not node.get("enabled",True):item.setToolTip(0,"此节点已禁用")
            self.tree.addTopLevelItem(item)
            if node["id"] == selected_id: self.tree.setCurrentItem(item)
        if not self.tree.currentItem() and self.tree.topLevelItemCount(): self.tree.setCurrentItem(self.tree.topLevelItem(0))
        self._updating = False

    def _selected(self, item, previous):
        if item and not self._updating: self.nodeSelected.emit(item.data(0, Qt.ItemDataRole.UserRole))

    def _double_clicked(self, item, column):
        node_id = item.data(0, Qt.ItemDataRole.UserRole)
        timing = next((value for value in self.session.node_timings() if value["id"] == node_id), None)
        if timing: self.frameRequested.emit(timing["start"])
        self.editRequested.emit(node_id)

    def _rows_moved(self, *args):
        if self._updating: return
        for index in range(self.tree.topLevelItemCount()):
            node_id = self.tree.topLevelItem(index).data(0, Qt.ItemDataRole.UserRole)
            project = self.session.project(); current = next((i for i, value in enumerate(project["nodes"]) if value["id"] == node_id), -1)
            if current != index:
                if self.session.move_node(node_id, index): self.sequenceEdited.emit()
                else:self.operationRejected.emit("不能把节点移出目标对象的有效生命周期")
                self.refresh(node_id); break

    def duplicate(self):
        if node_id := self.current_id():
            created = self.session.duplicate_node(node_id)
            if created: self.sequenceEdited.emit(); self.refresh(created)

    def copy(self):
        if node_id := self.current_id(): self._copied_node_id = node_id

    def paste(self):
        source=self._copied_node_id;nodes=self.session.project().get("nodes",[])
        if not source or not any(node["id"]==source for node in nodes):return
        current=self.current_id();insertion=next((index+1 for index,node in enumerate(nodes) if node["id"]==current),len(nodes))
        created=self.session.duplicate_node(source,insertion)
        if created:self.sequenceEdited.emit();self.refresh(created)

    def delete(self):
        if node_id := self.current_id():
            if self.session.delete_node(node_id): self.sequenceEdited.emit(); self.refresh()

    def move(self, delta):
        item = self.tree.currentItem()
        if not item: return
        node_id=item.data(0, Qt.ItemDataRole.UserRole);index = self.tree.indexOfTopLevelItem(item); target = max(0, min(self.tree.topLevelItemCount() - 1, index + delta))
        if target != index and self.session.move_node(node_id, target):
            self.sequenceEdited.emit(); self.refresh(node_id)
        elif target != index:self.operationRejected.emit("不能把节点移出目标对象的有效生命周期");self.refresh(node_id)
