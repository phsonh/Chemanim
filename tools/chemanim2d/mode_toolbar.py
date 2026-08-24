from __future__ import annotations

from math import cos, pi, sin

from PyQt6.QtCore import QPointF, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QActionGroup, QColor, QIcon, QPainter, QPen, QPixmap, QPolygonF
from PyQt6.QtWidgets import (QButtonGroup, QFrame, QHBoxLayout, QLabel, QMenu,
                             QPushButton, QScrollArea, QToolButton, QVBoxLayout,
                             QWidget)


def icon_for(kind: str, text="") -> QIcon:
    pixmap = QPixmap(30, 30); pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor(225, 230, 238), 2))
    if kind.startswith("ring") or kind == "benzene":
        count = 6 if kind == "benzene" else int(kind[-1]); points = [QPointF(15+11*cos(-pi/2+i*2*pi/count),15+11*sin(-pi/2+i*2*pi/count)) for i in range(count)]
        painter.drawPolygon(QPolygonF(points));
        if kind == "benzene": painter.drawLine(points[0]*.78+QPointF(3.3,3.3), points[1]*.78+QPointF(3.3,3.3))
    elif "bond" in kind or "wedge" in kind:
        if kind == "double_bond": painter.drawLine(4, 11, 26, 11); painter.drawLine(4, 19, 26, 19)
        elif kind == "triple_bond":
            for y in (9, 15, 21): painter.drawLine(4, y, 26, y)
        elif kind == "solid_wedge": painter.setBrush(QColor(225,230,238)); painter.drawPolygon(QPolygonF([QPointF(4,15),QPointF(26,7),QPointF(26,23)]))
        else: painter.drawLine(4, 22, 26, 8)
    elif kind == "select_lasso": painter.drawEllipse(4, 6, 22, 18)
    elif kind == "select_rectangle": painter.drawRect(4, 6, 22, 18)
    elif kind == "eraser": painter.drawRect(7, 8, 17, 14)
    else: painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, text or kind[:2].upper())
    painter.end(); return QIcon(pixmap)


class ModeToolPanel(QWidget):
    nodeRequested = pyqtSignal(str)
    drawToolRequested = pyqtSignal(str)
    elementRequested = pyqtSignal(str)
    periodicTableRequested = pyqtSignal()
    groupPanelRequested = pyqtSignal()

    SCRIPT_CATEGORIES = ["通用", "分子", "箭头"]
    DRAW_CATEGORIES = ["工具", "结构", "元素", "电荷"]

    def __init__(self, session, parent=None):
        super().__init__(parent); self.session = session; self.mode = "脚本"; self.category = "通用"; self._active_draw_tool = "select_rectangle"
        self.setObjectName("modeToolPanel"); self.setFixedHeight(126)
        layout = QVBoxLayout(self); layout.setContentsMargins(8, 4, 8, 4); layout.setSpacing(2)
        self.primary = QWidget(); self.primary_layout = QHBoxLayout(self.primary); self.primary_layout.setContentsMargins(0,0,0,0); self.primary_layout.setSpacing(4)
        self.secondary = QWidget(); self.secondary_layout = QHBoxLayout(self.secondary); self.secondary_layout.setContentsMargins(0,0,0,0); self.secondary_layout.setSpacing(4)
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True); self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded); self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff); self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.tertiary = QWidget(); self.tertiary_layout = QHBoxLayout(self.tertiary); self.tertiary_layout.setContentsMargins(0,0,0,0); self.tertiary_layout.setSpacing(4); self.scroll.setWidget(self.tertiary)
        layout.addWidget(self.primary); layout.addWidget(self.secondary); layout.addWidget(self.scroll,1)
        self.mode_group = QButtonGroup(self); self.mode_group.setExclusive(True)
        for name in ("脚本", "绘制"):
            button=QPushButton(name);button.setCheckable(True);button.setProperty("level","primary");button.clicked.connect(lambda checked,n=name:self.set_mode(n) if checked else None);self.mode_group.addButton(button);self.primary_layout.addWidget(button)
            if name==self.mode:button.setChecked(True)
        self.primary_layout.addStretch(1); self._build_secondary()

    def _clear(self, layout):
        while layout.count():
            item=layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def set_mode(self, mode):
        self.mode=mode;self.category=(self.SCRIPT_CATEGORIES if mode=="脚本" else self.DRAW_CATEGORIES)[0];self._build_secondary()

    def _build_secondary(self):
        self._clear(self.secondary_layout);group=QButtonGroup(self);group.setExclusive(True)
        for name in (self.SCRIPT_CATEGORIES if self.mode=="脚本" else self.DRAW_CATEGORIES):
            button=QPushButton(name);button.setCheckable(True);button.setProperty("level","secondary");button.clicked.connect(lambda checked,n=name:self.set_category(n) if checked else None);group.addButton(button);self.secondary_layout.addWidget(button)
            if name==self.category:button.setChecked(True)
        self.secondary_layout.addStretch(1);self._build_tertiary()

    def set_category(self, category): self.category=category;self._build_tertiary()

    def _tool(self, kind, tooltip, signal, text="", checkable=False):
        is_draw = getattr(signal, "signal", None) == getattr(self.drawToolRequested, "signal", None)
        button=QToolButton();button.setIcon(icon_for(kind,text));button.setIconSize(QPixmap(30,30).size());button.setToolTip(tooltip);button.setCheckable(checkable or is_draw);button.setChecked(is_draw and kind==self._active_draw_tool)
        def clicked(checked=False):
            if is_draw:
                self._active_draw_tool=kind
                for child in self.tertiary.findChildren(QToolButton): child.setChecked(child.property("drawKind")==kind)
            signal.emit(kind)
        if is_draw: button.setProperty("drawKind",kind)
        button.clicked.connect(clicked);self.tertiary_layout.addWidget(button);return button

    def _label(self, text):
        label=QLabel(text);label.setProperty("toolGroup",True);self.tertiary_layout.addWidget(label)

    def _separator(self):
        line=QFrame();line.setFrameShape(QFrame.Shape.VLine);line.setFrameShadow(QFrame.Shadow.Sunken);self.tertiary_layout.addWidget(line)

    def _build_tertiary(self):
        self._clear(self.tertiary_layout)
        if self.mode=="脚本":
            definitions=[item for item in self.session.node_registry() if item["category"]==self.category]
            last_group=None
            for definition in definitions:
                group=definition.get("group","")
                if group!=last_group:
                    if last_group is not None:self._separator()
                    self._label(group);last_group=group
                self._tool(definition["type"],definition["label"],self.nodeRequested,definition["label"][:2])
        elif self.category=="工具":
            for key,label,shortcut in (("select_rectangle","框选","V"),("select_lasso","套索","L"),("eraser","橡皮擦","E")):
                self._tool(key,f"{label} · {shortcut}",self.drawToolRequested,checkable=True)
        elif self.category=="结构":
            self._label("键")
            for key,label,shortcut in (("single_bond","单键","1"),("double_bond","双键","2"),("triple_bond","三键","3")):self._tool(key,f"{label} · {shortcut}",self.drawToolRequested)
            more=QToolButton();more.setIcon(icon_for("wavy_bond"));more.setToolTip("更多键型");menu=QMenu(more)
            for key,label in (("aromatic_bond","芳香键"),("solid_wedge","实楔键"),("dashed_wedge","虚楔键"),("wavy_bond","波浪键")):
                action=QAction(label,menu);action.triggered.connect(lambda checked=False,k=key:self.drawToolRequested.emit(k));menu.addAction(action)
            more.setMenu(menu);more.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup);self.tertiary_layout.addWidget(more)
            self._separator();self._label("环")
            for count in range(3,9):self._tool(f"ring{count}",f"{count} 元环",self.drawToolRequested)
            self._tool("benzene","苯环 · B",self.drawToolRequested)
            self._separator();self._label("基团");button=QToolButton();button.setIcon(icon_for("groups","R"));button.setToolTip("打开数据驱动基团面板");button.clicked.connect(self.groupPanelRequested);self.tertiary_layout.addWidget(button)
        elif self.category=="元素":
            for element in ("C","N","O","S","P","F","Cl","Br","I"):
                button=QToolButton();button.setIcon(icon_for("element",element));button.setToolTip(f"元素 {element}");button.clicked.connect(lambda checked=False,e=element:self.elementRequested.emit(e));self.tertiary_layout.addWidget(button)
            self._separator();button=QToolButton();button.setIcon(icon_for("periodic","…"));button.setToolTip("周期表…");button.clicked.connect(self.periodicTableRequested);self.tertiary_layout.addWidget(button)
        else:
            self._tool("charge_positive","形式电荷 +：修改 atom.formal_charge",self.drawToolRequested,"+")
            self._tool("charge_negative","形式电荷 −：修改 atom.formal_charge",self.drawToolRequested,"−")
        self.tertiary_layout.addStretch(1)
