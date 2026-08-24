from __future__ import annotations

from math import cos, pi, sin
from PyQt6.QtCore import QPointF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QIcon, QPainter, QPen, QPixmap, QPolygonF
from PyQt6.QtWidgets import (QButtonGroup, QFrame, QHBoxLayout, QLabel, QMenu,
                             QPushButton, QScrollArea, QToolButton, QVBoxLayout, QWidget)


def icon_for(kind: str, text="") -> QIcon:
    pixmap=QPixmap(28,28);pixmap.fill(Qt.GlobalColor.transparent)
    painter=QPainter(pixmap);painter.setRenderHint(QPainter.RenderHint.Antialiasing);painter.setPen(QPen(QColor(225,230,238),2))
    if kind.startswith("ring") or kind=="benzene":
        count=6 if kind=="benzene" else int(kind[-1]);points=[QPointF(14+10*cos(-pi/2+i*2*pi/count),14+10*sin(-pi/2+i*2*pi/count)) for i in range(count)];painter.drawPolygon(QPolygonF(points))
        if kind=="benzene":
            for i in (0,2,4):painter.drawLine(points[i]*.72+QPointF(3.9,3.9),points[(i+1)%6]*.72+QPointF(3.9,3.9))
    elif kind in ("single_bond","double_bond","triple_bond","solid_wedge","dashed_wedge","wavy_bond"):
        if kind=="double_bond":painter.drawLine(4,10,24,10);painter.drawLine(4,18,24,18)
        elif kind=="triple_bond":
            for y in (8,14,20):painter.drawLine(4,y,24,y)
        elif kind=="solid_wedge":painter.setBrush(QColor(225,230,238));painter.drawPolygon(QPolygonF([QPointF(4,14),QPointF(24,7),QPointF(24,21)]))
        elif kind=="dashed_wedge":
            for i in range(5):painter.drawLine(5+i*4,14-i,5+i*4,14+i)
        elif kind=="wavy_bond":painter.drawLine(4,18,9,10);painter.drawLine(9,10,14,18);painter.drawLine(14,18,19,10);painter.drawLine(19,10,24,18)
        else:painter.drawLine(4,20,24,8)
    elif kind=="select_lasso":painter.drawEllipse(4,6,20,16)
    elif kind=="select_rectangle":painter.drawRect(4,6,20,16)
    elif kind=="eraser":painter.drawRect(7,8,15,12)
    else:painter.drawText(pixmap.rect(),Qt.AlignmentFlag.AlignCenter,text or "•")
    painter.end();return QIcon(pixmap)


class ModeToolPanel(QWidget):
    nodeRequested=pyqtSignal(str);drawToolRequested=pyqtSignal(str);elementRequested=pyqtSignal(str);periodicTableRequested=pyqtSignal()
    SCRIPT_CATEGORIES=("通用","分子","箭头");DRAW_CATEGORIES=("工具","结构","元素","电荷")

    def __init__(self,session,parent=None):
        super().__init__(parent);self.session=session;self.mode="脚本";self.category="通用";self._active_draw_tool="select_rectangle"
        self.setObjectName("modeToolPanel");layout=QVBoxLayout(self);layout.setContentsMargins(8,6,8,6);layout.setSpacing(4)
        self.primary=QWidget();self.primary_layout=QHBoxLayout(self.primary);self.primary_layout.setContentsMargins(0,0,0,0);self.primary_layout.setSpacing(6)
        self.secondary=QWidget();self.secondary_layout=QHBoxLayout(self.secondary);self.secondary_layout.setContentsMargins(0,0,0,0);self.secondary_layout.setSpacing(6)
        self.scroll=QScrollArea();self.scroll.setWidgetResizable(True);self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded);self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff);self.scroll.setFrameShape(QFrame.Shape.NoFrame);self.scroll.setMinimumHeight(58);self.scroll.setMaximumHeight(68)
        self.tertiary=QWidget();self.tertiary_layout=QHBoxLayout(self.tertiary);self.tertiary_layout.setContentsMargins(0,2,0,2);self.tertiary_layout.setSpacing(6);self.scroll.setWidget(self.tertiary)
        layout.addWidget(self.primary);layout.addWidget(self.secondary);layout.addWidget(self.scroll)
        group=QButtonGroup(self);group.setExclusive(True)
        for name in ("脚本","绘制"):
            button=QPushButton(name);button.setCheckable(True);button.setProperty("level","primary");button.clicked.connect(lambda checked,n=name:self.set_mode(n) if checked else None);group.addButton(button);self.primary_layout.addWidget(button);button.setChecked(name==self.mode)
        self.primary_layout.addStretch();self._build_secondary()

    @staticmethod
    def _clear(layout):
        while layout.count():
            item=layout.takeAt(0)
            if item.widget():item.widget().deleteLater()

    def set_mode(self,mode):self.mode=mode;self.category=(self.SCRIPT_CATEGORIES if mode=="脚本" else self.DRAW_CATEGORIES)[0];self._build_secondary()
    def set_category(self,category):self.category=category;self._build_tertiary()

    def _build_secondary(self):
        self._clear(self.secondary_layout);group=QButtonGroup(self);group.setExclusive(True)
        for name in (self.SCRIPT_CATEGORIES if self.mode=="脚本" else self.DRAW_CATEGORIES):
            button=QPushButton(name);button.setCheckable(True);button.setProperty("level","secondary");button.clicked.connect(lambda checked,n=name:self.set_category(n) if checked else None);group.addButton(button);self.secondary_layout.addWidget(button);button.setChecked(name==self.category)
        self.secondary_layout.addStretch();self._build_tertiary()

    def _separator(self):line=QFrame();line.setFrameShape(QFrame.Shape.VLine);self.tertiary_layout.addWidget(line)
    def _label(self,text):label=QLabel(text);label.setProperty("toolGroup",True);self.tertiary_layout.addWidget(label)
    def _tool(self,kind,label,signal,checkable=False,tooltip=""):
        is_draw=getattr(signal,"signal",None)==getattr(self.drawToolRequested,"signal",None)
        button=QToolButton();button.setIcon(icon_for(kind,label));button.setIconSize(QSize(26,26));button.setText(label);button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon);button.setToolTip(tooltip or label);button.setCheckable(checkable);button.setMinimumHeight(40);button.setMinimumWidth(button.fontMetrics().horizontalAdvance(label)+50)
        if checkable:button.setChecked(kind==self._active_draw_tool);button.setProperty("drawKind",kind)
        def clicked(_checked=False):
            if is_draw:
                self._active_draw_tool=kind
                for child in self.tertiary.findChildren(QToolButton):child.setChecked(child.property("drawKind")==kind)
            signal.emit(kind)
        button.clicked.connect(clicked);self.tertiary_layout.addWidget(button);return button

    def _node_menu(self,label,definitions):
        button=QToolButton();button.setText(label);button.setIcon(icon_for("node",label[:1]));button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon);button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup);button.setMinimumHeight(40);button.setMinimumWidth(button.fontMetrics().horizontalAdvance(label)+54);menu=QMenu(button)
        for definition in definitions:
            action=QAction(definition["label"],menu);action.triggered.connect(lambda checked=False,t=definition["type"]:self.nodeRequested.emit(t));menu.addAction(action)
        button.setMenu(menu);self.tertiary_layout.addWidget(button)

    def _build_tertiary(self):
        self._clear(self.tertiary_layout)
        if self.mode=="脚本":
            definitions=[item for item in self.session.node_registry() if item["category"]==self.category];groups=[]
            for item in definitions:
                if item.get("group","") not in groups:groups.append(item.get("group",""))
            for index,group in enumerate(groups):
                if index:self._separator()
                self._label(group);items=[item for item in definitions if item.get("group","")==group]
                if len(items)<=4:
                    for item in items:self._tool(item["type"],item["label"],self.nodeRequested)
                else:
                    sets=[item for item in items if "_set_" in item["type"] or item["type"].startswith("adornment_set")]
                    lerps=[item for item in items if "_lerp_" in item["type"] or item["type"].startswith("adornment_lerp")]
                    others=[item for item in items if item not in sets and item not in lerps]
                    if others:self._node_menu("创建/事件",others)
                    if sets:self._node_menu("设定…",sets)
                    if lerps:self._node_menu("插值…",lerps)
        elif self.category=="工具":
            for key,label,shortcut in (("select_rectangle","框选","V"),("select_lasso","套索","L"),("eraser","橡皮擦","E")):self._tool(key,label,self.drawToolRequested,True,f"{label} · {shortcut}")
        elif self.category=="结构":
            self._label("键")
            for key,label in (("single_bond","单键"),("double_bond","双键"),("triple_bond","三键"),("solid_wedge","实楔"),("dashed_wedge","虚楔"),("wavy_bond","波浪键")):self._tool(key,label,self.drawToolRequested,True)
            self._separator();self._label("环")
            for count in range(3,9):self._tool(f"ring{count}",f"{count} 元环",self.drawToolRequested,True)
            self._tool("benzene","单双键苯环",self.drawToolRequested,True)
        elif self.category=="元素":
            for element in ("C","N","O","S","P","F","Cl","Br","I"):self._tool("element",element,self.elementRequested)
            self._separator();button=QToolButton();button.setText("周期表…");button.setIcon(icon_for("periodic","…"));button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon);button.clicked.connect(self.periodicTableRequested);self.tertiary_layout.addWidget(button)
        else:
            self._tool("charge_positive","视觉标记 +",self.drawToolRequested,True,"在原子上创建可自由移动的 + 标记")
            self._tool("charge_negative","视觉标记 −",self.drawToolRequested,True,"在原子上创建可自由移动的 − 标记")
        self.tertiary_layout.addStretch()
