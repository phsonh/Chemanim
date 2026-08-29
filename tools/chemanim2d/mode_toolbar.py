from __future__ import annotations

from math import cos, pi, sin
from PyQt6.QtCore import QPointF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap, QPolygonF
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QScrollArea,
                             QTabBar, QToolButton, QVBoxLayout, QWidget)


def icon_for(kind: str, text="") -> QIcon:
    pixmap=QPixmap(28,28);pixmap.fill(Qt.GlobalColor.transparent)
    painter=QPainter(pixmap);painter.setRenderHint(QPainter.RenderHint.Antialiasing);painter.setPen(QPen(QColor(225,230,238),2))
    if kind.startswith("ring") or kind=="benzene":
        count=6 if kind=="benzene" else int(kind[-1]);points=[QPointF(14+10*cos(-pi/2+i*2*pi/count),14+10*sin(-pi/2+i*2*pi/count)) for i in range(count)];painter.drawPolygon(QPolygonF(points))
        if kind=="benzene":
            for i in (0,2,4):painter.drawLine(points[i]*.72+QPointF(3.9,3.9),points[(i+1)%6]*.72+QPointF(3.9,3.9))
    elif kind in ("single_bond","double_bond","triple_bond","solid_wedge","dashed_wedge","solid_bar","hashed_bar","wavy_bond"):
        if kind=="double_bond":painter.drawLine(4,10,24,10);painter.drawLine(4,18,24,18)
        elif kind=="triple_bond":
            for y in (8,14,20):painter.drawLine(4,y,24,y)
        elif kind=="solid_wedge":painter.setBrush(QColor(225,230,238));painter.drawPolygon(QPolygonF([QPointF(4,14),QPointF(24,7),QPointF(24,21)]))
        elif kind=="dashed_wedge":
            for i in range(5):painter.drawLine(5+i*4,14-i,5+i*4,14+i)
        elif kind=="solid_bar":
            painter.setPen(QPen(QColor(225,230,238),6,Qt.PenStyle.SolidLine,Qt.PenCapStyle.FlatCap));painter.drawLine(4,14,24,14)
        elif kind=="hashed_bar":
            for x in (4,8,12,16,20,24):painter.drawLine(x,9,x,19)
        elif kind=="wavy_bond":painter.drawLine(4,18,9,10);painter.drawLine(9,10,14,18);painter.drawLine(14,18,19,10);painter.drawLine(19,10,24,18)
        else:painter.drawLine(4,20,24,8)
    elif kind=="select_lasso":painter.drawEllipse(4,6,20,16)
    elif kind=="select_rectangle":painter.drawRect(4,6,20,16)
    elif kind=="eraser":painter.drawRect(7,8,15,12)
    elif kind in ("charge_positive","charge_negative"):
        painter.drawEllipse(5,5,18,18);painter.drawLine(9,14,19,14)
        if kind=="charge_positive":painter.drawLine(14,9,14,19)
    elif kind=="atom_text":
        painter.drawText(7,21,"A")
    else:
        # Generic script-node icon.  Never squeeze the localized label into a
        # 28 px pixmap: at high DPI that looked like duplicated/garbled text.
        painter.drawRoundedRect(5,5,18,18,3,3)
        painter.drawLine(9,10,19,10);painter.drawLine(9,14,19,14);painter.drawLine(9,18,16,18)
    painter.end();return QIcon(pixmap)


class ModeToolPanel(QWidget):
    nodeRequested=pyqtSignal(str);drawToolRequested=pyqtSignal(str);elementRequested=pyqtSignal(str);periodicTableRequested=pyqtSignal()
    SCRIPT_CATEGORIES=("通用","分子","箭头");DRAW_CATEGORIES=("绘制",)
    STRUCTURE_WRITE_TOOLS={"eraser","atom_label","atom_text","charge_positive","charge_negative",
        "single_bond","double_bond","triple_bond","solid_wedge","dashed_wedge","solid_bar",
        "hashed_bar","wavy_bond","ring3","ring4","ring5","ring6","ring7","ring8","benzene"}

    def __init__(self,session,parent=None):
        super().__init__(parent);self.session=session;self.mode="脚本";self.category="通用";self.script_scope="对象";self._active_draw_tool="select_rectangle";self._structure_enabled=False
        self.recent_elements=["C","N","O","H","S","P","F","Cl","Br","I"]
        self.text_number_style="subscript"
        self.setObjectName("modeToolPanel");layout=QVBoxLayout(self);layout.setContentsMargins(0,4,0,0);layout.setSpacing(0)
        self.primary=QTabBar();self.primary.setObjectName("primaryTabs");self.primary.setShape(QTabBar.Shape.RoundedNorth);self.primary.setExpanding(False);self.primary.setDrawBase(False)
        for name in ("脚本","绘制"):self.primary.addTab(name)
        self.primary.currentChanged.connect(lambda index:self.set_mode(self.primary.tabText(index)) if index>=0 else None)
        primary_row=QWidget();primary_layout=QHBoxLayout(primary_row);primary_layout.setContentsMargins(8,0,8,0);primary_layout.setSpacing(0);primary_layout.addWidget(self.primary);primary_layout.addStretch()
        self.secondary=QTabBar();self.secondary.setObjectName("secondaryTabs");self.secondary.setShape(QTabBar.Shape.RoundedNorth);self.secondary.setExpanding(False);self.secondary.setDrawBase(False);self.secondary.currentChanged.connect(lambda index:self.set_category(self.secondary.tabText(index)) if index>=0 else None)
        self.secondary_row=QWidget();self.secondary_row.setObjectName("secondaryRow");self.secondary_layout=QHBoxLayout(self.secondary_row);self.secondary_layout.setContentsMargins(22,0,8,0);self.secondary_layout.setSpacing(0);self.secondary_layout.addWidget(self.secondary);self.secondary_layout.addStretch()
        self.scope_tabs=QTabBar();self.scope_tabs.setObjectName("scriptScopeTabs");self.scope_tabs.setShape(QTabBar.Shape.RoundedNorth);self.scope_tabs.setExpanding(False);self.scope_tabs.setDrawBase(False);self.scope_tabs.currentChanged.connect(lambda index:self.set_script_scope(self.scope_tabs.tabText(index)) if index>=0 else None)
        self.scope_row=QWidget();self.scope_row.setObjectName("scriptScopeRow");scope_layout=QHBoxLayout(self.scope_row);scope_layout.setContentsMargins(38,0,8,0);scope_layout.setSpacing(0);scope_layout.addWidget(self.scope_tabs);scope_layout.addStretch()
        self.scroll=QScrollArea();self.scroll.setWidgetResizable(True);self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded);self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff);self.scroll.setFrameShape(QFrame.Shape.NoFrame);self.scroll.setMinimumHeight(58);self.scroll.setMaximumHeight(68)
        self.tertiary=QWidget();self.tertiary.setObjectName("tertiaryTools");self.tertiary_layout=QHBoxLayout(self.tertiary);self.tertiary_layout.setContentsMargins(10,6,10,6);self.tertiary_layout.setSpacing(6);self.scroll.setWidget(self.tertiary)
        layout.addWidget(primary_row);layout.addWidget(self.secondary_row);layout.addWidget(self.scope_row);layout.addWidget(self.scroll)
        self._build_secondary()

    @staticmethod
    def _clear(layout):
        while layout.count():
            item=layout.takeAt(0)
            if item.widget():item.widget().hide();item.widget().deleteLater()

    def set_mode(self,mode):
        if mode not in ("脚本","绘制"):return
        self.mode=mode;index=("脚本","绘制").index(mode)
        if self.primary.currentIndex()!=index:self.primary.blockSignals(True);self.primary.setCurrentIndex(index);self.primary.blockSignals(False)
        self.category=(self.SCRIPT_CATEGORIES if mode=="脚本" else self.DRAW_CATEGORIES)[0];self._build_secondary()
    def set_category(self,category):
        categories=self.SCRIPT_CATEGORIES if self.mode=="脚本" else self.DRAW_CATEGORIES
        if self.mode=="绘制" and category in ("工具","结构","元素"):category="绘制"
        if category not in categories:return
        self.category=category;self.script_scope="对象";index=categories.index(category)
        if self.secondary.currentIndex()!=index:self.secondary.blockSignals(True);self.secondary.setCurrentIndex(index);self.secondary.blockSignals(False)
        self._build_tertiary()

    def set_script_scope(self,scope):
        if scope not in ("对象","设定","变换"):return
        self.script_scope=scope
        if self.scope_tabs.currentIndex()!=("对象","设定","变换").index(scope):
            self.scope_tabs.blockSignals(True);self.scope_tabs.setCurrentIndex(("对象","设定","变换").index(scope));self.scope_tabs.blockSignals(False)
        self._build_tertiary()

    def _build_secondary(self):
        categories=self.SCRIPT_CATEGORIES if self.mode=="脚本" else self.DRAW_CATEGORIES
        self.secondary_row.setVisible(self.mode=="脚本")
        self.secondary.blockSignals(True)
        while self.secondary.count():self.secondary.removeTab(0)
        for name in categories:self.secondary.addTab(name)
        self.secondary.setCurrentIndex(categories.index(self.category));self.secondary.blockSignals(False);self._build_tertiary()

    def record_element(self,element):
        if not element:return
        self.recent_elements=[element]+[value for value in self.recent_elements if value!=element]
        self.recent_elements=self.recent_elements[:10]
        if self.mode=="绘制":self._build_tertiary()

    def set_structure_enabled(self,enabled):
        self._structure_enabled=bool(enabled)
        for button in self.tertiary.findChildren(QToolButton):
            if button.property("structureWrite"):
                button.setEnabled(self._structure_enabled)

    def _separator(self):line=QFrame();line.setFrameShape(QFrame.Shape.VLine);self.tertiary_layout.addWidget(line)
    def _tool(self,kind,label,signal,checkable=False,tooltip="",show_icon=True,icon_only=False):
        is_draw=getattr(signal,"signal",None)==getattr(self.drawToolRequested,"signal",None)
        button=QToolButton();button.setText(label);button.setToolTip(tooltip or label);button.setCheckable(checkable);button.setMinimumHeight(40)
        structure_write=kind in self.STRUCTURE_WRITE_TOOLS or (self.mode=="绘制" and not is_draw)
        button.setProperty("structureWrite",structure_write)
        if show_icon:
            button.setIcon(icon_for(kind,label));button.setIconSize(QSize(28,28))
            if icon_only:button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly);button.setFixedWidth(46)
            else:button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon);button.setMinimumWidth(button.fontMetrics().horizontalAdvance(label)+50)
        else:button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly);button.setMinimumWidth(max(44,button.fontMetrics().horizontalAdvance(label)+26))
        if checkable:button.setChecked(kind==self._active_draw_tool);button.setProperty("drawKind",kind)
        def clicked(_checked=False):
            if is_draw:
                self._active_draw_tool=kind
                for child in self.tertiary.findChildren(QToolButton):child.setChecked(child.property("drawKind")==kind)
                self._update_text_style_buttons()
            signal.emit(kind)
        button.clicked.connect(clicked);self.tertiary_layout.addWidget(button);return button

    def _text_style_button(self,label,style,tooltip):
        button=QToolButton();button.setText(label);button.setToolTip(tooltip);button.setCheckable(True)
        button.setProperty("textNumberStyle",style);button.setMinimumHeight(40);button.setFixedWidth(42)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        button.clicked.connect(lambda _checked=False,value=style:self._set_text_number_style(value))
        self.tertiary_layout.addWidget(button);return button

    def _set_text_number_style(self,style):
        if self._active_draw_tool!="atom_text" or style not in ("normal","subscript","superscript"):return
        self.text_number_style=style;self._update_text_style_buttons()

    def _update_text_style_buttons(self):
        enabled=self._active_draw_tool=="atom_text"
        for button in self.tertiary.findChildren(QToolButton):
            style=button.property("textNumberStyle")
            if style:
                button.setEnabled(enabled);button.setChecked(enabled and style==self.text_number_style)

    @staticmethod
    def _script_scope_for(node_type):
        if "_lerp_" in node_type or node_type=="selection_fade":return "变换"
        if "_set_" in node_type or node_type.startswith("adornment_set_"):return "设定"
        return "对象"

    def _build_tertiary(self):
        self._clear(self.tertiary_layout)
        scoped=self.mode=="脚本" and self.category in ("分子","箭头")
        self.scope_row.setVisible(scoped)
        if scoped:
            self.scope_tabs.blockSignals(True)
            while self.scope_tabs.count():self.scope_tabs.removeTab(0)
            for name in ("对象","设定","变换"):self.scope_tabs.addTab(name)
            self.scope_tabs.setCurrentIndex(("对象","设定","变换").index(self.script_scope));self.scope_tabs.blockSignals(False)
        if self.mode=="脚本":
            definitions=[item for item in self.session.node_registry() if item["category"]==self.category]
            if scoped:definitions=[item for item in definitions if self._script_scope_for(item["type"])==self.script_scope]
            for item in definitions:self._tool(item["type"],item["label"],self.nodeRequested,show_icon=False)
        else:
            for key,label,shortcut in (("select_rectangle","框选","V"),("select_lasso","套索","L"),("eraser","橡皮擦","E")):self._tool(key,label,self.drawToolRequested,True,f"{label} · {shortcut}",icon_only=True)
            self._separator()
            for key,label in (("single_bond","单键"),("double_bond","双键"),("triple_bond","三键"),("solid_wedge","渐宽实楔"),("dashed_wedge","渐宽虚楔"),("solid_bar","等宽实键"),("hashed_bar","等宽虚键"),("wavy_bond","波浪键")):self._tool(key,label,self.drawToolRequested,True,label,icon_only=True)
            self._separator()
            for count in range(3,9):self._tool(f"ring{count}",f"{count} 元环",self.drawToolRequested,True,f"{count} 元环",icon_only=True)
            self._tool("benzene","单双键苯环",self.drawToolRequested,True,"显式单双键苯环",icon_only=True)
            self._separator()
            self._tool("charge_positive","⊕",self.drawToolRequested,True,"形式正电荷（带圈 +）",icon_only=True)
            self._tool("charge_negative","⊖",self.drawToolRequested,True,"形式负电荷（带圈 −）",icon_only=True)
            self._separator()
            self._tool("atom_text","文字",self.drawToolRequested,True,"原子文字：点击后输入，左右拖动决定排版",icon_only=True)
            self._text_style_button("X2","normal","数字正常排列")
            self._text_style_button("X₂","subscript","数字作为下标")
            self._text_style_button("X²","superscript","数字作为上标")
            self._update_text_style_buttons()
            self._separator()
            for element in self.recent_elements:self._tool(element,element,self.elementRequested,show_icon=False)
            self._separator();button=QToolButton();button.setText("周期表…");button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly);button.clicked.connect(self.periodicTableRequested);self.tertiary_layout.addWidget(button)
            button.setProperty("structureWrite",True)
        self.tertiary_layout.addStretch()
        self.set_structure_enabled(self._structure_enabled)
