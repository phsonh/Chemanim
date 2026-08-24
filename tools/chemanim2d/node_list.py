from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QHBoxLayout, QPushButton, QTreeWidget,
                             QTreeWidgetItem, QVBoxLayout, QWidget)


class NodeList(QWidget):
    nodeSelected = pyqtSignal(str)
    frameRequested = pyqtSignal(int)
    sequenceEdited = pyqtSignal()

    def __init__(self, session, parent=None):
        super().__init__(parent); self.session = session; self._updating = False
        self.tree = QTreeWidget(); self.tree.setHeaderLabels(["节点", "目标", "时长", "起止帧"])
        self.tree.setRootIsDecorated(False); self.tree.setUniformRowHeights(True)
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.tree.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)
        self.tree.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.tree.currentItemChanged.connect(self._selected); self.tree.itemDoubleClicked.connect(self._double_clicked)
        self.tree.itemChanged.connect(self._enabled_changed); self.tree.model().rowsMoved.connect(self._rows_moved)
        buttons = QHBoxLayout()
        for text, callback in (("复制", self.duplicate), ("删除", self.delete), ("上移", lambda: self.move(-1)), ("下移", lambda: self.move(1))):
            button = QPushButton(text); button.clicked.connect(callback); buttons.addWidget(button)
        buttons.addStretch(1)
        layout = QVBoxLayout(self); layout.setContentsMargins(4, 4, 4, 4); layout.addWidget(self.tree); layout.addLayout(buttons)

    def current_id(self):
        item = self.tree.currentItem(); return item.data(0, Qt.ItemDataRole.UserRole) if item else ""

    def refresh(self, selected_id=""):
        selected_id = selected_id or self.current_id(); project = self.session.project(); timings = {item["id"]: item for item in self.session.node_timings()}
        registry = {item["type"]: item for item in self.session.node_registry()}
        self._updating = True; self.tree.clear()
        for node in project.get("nodes", []):
            timing = timings.get(node["id"], {}); definition = registry.get(node["type"], {})
            duration = max(0, timing.get("end", 0) - timing.get("start", 0))
            item = QTreeWidgetItem([definition.get("label", node["type"]), timing.get("target", ""),
                                    f"{duration} 帧" if duration else "—",
                                    f'{timing.get("start", 0)} → {timing.get("end", 0)}'])
            item.setData(0, Qt.ItemDataRole.UserRole, node["id"])
            item.setCheckState(0, Qt.CheckState.Checked if node.get("enabled", True) else Qt.CheckState.Unchecked)
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

    def _enabled_changed(self, item, column):
        if self._updating: return
        node_id=item.data(0, Qt.ItemDataRole.UserRole)
        if self.session.enable_node(node_id, item.checkState(0) == Qt.CheckState.Checked):
            self.sequenceEdited.emit(); self.refresh(node_id)

    def _rows_moved(self, *args):
        if self._updating: return
        for index in range(self.tree.topLevelItemCount()):
            node_id = self.tree.topLevelItem(index).data(0, Qt.ItemDataRole.UserRole)
            project = self.session.project(); current = next((i for i, value in enumerate(project["nodes"]) if value["id"] == node_id), -1)
            if current != index:
                if self.session.move_node(node_id, index): self.sequenceEdited.emit()
                self.refresh(node_id); break

    def duplicate(self):
        if node_id := self.current_id():
            created = self.session.duplicate_node(node_id)
            if created: self.sequenceEdited.emit(); self.refresh(created)

    def delete(self):
        if node_id := self.current_id():
            if self.session.delete_node(node_id): self.sequenceEdited.emit(); self.refresh()

    def move(self, delta):
        item = self.tree.currentItem()
        if not item: return
        node_id=item.data(0, Qt.ItemDataRole.UserRole);index = self.tree.indexOfTopLevelItem(item); target = max(0, min(self.tree.topLevelItemCount() - 1, index + delta))
        if target != index and self.session.move_node(node_id, target):
            self.sequenceEdited.emit(); self.refresh(node_id)
