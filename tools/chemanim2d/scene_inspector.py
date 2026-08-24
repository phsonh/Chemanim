from __future__ import annotations

import json

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (QColorDialog, QComboBox, QDoubleSpinBox, QFormLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox,
                             QWidget)


def color_from_rgba(value: str) -> QColor:
    value = (value or "FFFFFFFF").lstrip("#")
    if len(value) == 6:
        value += "FF"
    try:
        return QColor(int(value[0:2], 16), int(value[2:4], 16),
                      int(value[4:6], 16), int(value[6:8], 16))
    except (ValueError, IndexError):
        return QColor("white")


def rgba_text(color: QColor) -> str:
    return f"{color.red():02X}{color.green():02X}{color.blue():02X}{color.alpha():02X}"


class SceneInspector(QWidget):
    sceneEdited = pyqtSignal()

    PRESETS = {
        "1920 × 1080 · 横屏": (1920, 1080),
        "1080 × 1920 · 竖屏": (1080, 1920),
        "1080 × 1080 · 方形": (1080, 1080),
        "自定义": None,
    }

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self._updating = False
        self.title_label = QLabel("场景设置")
        self.title_label.setObjectName("inspectorTitle")
        self.preset = QComboBox(); self.preset.addItems(self.PRESETS)
        self.width = QSpinBox(); self.height = QSpinBox()
        self.logic_width = QSpinBox(); self.logic_height = QSpinBox()
        self.fps = QSpinBox(); self.view_zoom = QDoubleSpinBox()
        for box in (self.width, self.height, self.logic_width, self.logic_height):
            box.setRange(16, 16384)
        self.fps.setRange(1, 240)
        self.view_zoom.setRange(.05, 32); self.view_zoom.setDecimals(2); self.view_zoom.setSingleStep(.1)
        self.title = QLineEdit()
        self.color_text = QLineEdit(); self.color_button = QPushButton("选择…")
        color_row = QWidget(); row = QHBoxLayout(color_row); row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self.color_text, 1); row.addWidget(self.color_button)
        layout = QFormLayout(self); layout.addRow(self.title_label); layout.addRow("输出预设", self.preset)
        layout.addRow("输出宽度", self.width); layout.addRow("输出高度", self.height)
        layout.addRow("逻辑宽度", self.logic_width); layout.addRow("逻辑高度", self.logic_height)
        layout.addRow("FPS", self.fps); layout.addRow("背景 RGBA", color_row)
        layout.addRow("标题", self.title); layout.addRow("渲染缩放", self.view_zoom)
        self.preset.currentTextChanged.connect(self._preset_changed)
        for box in (self.width, self.height, self.logic_width, self.logic_height, self.fps, self.view_zoom):
            box.editingFinished.connect(self.apply)
        self.title.editingFinished.connect(self.apply); self.color_text.editingFinished.connect(self.apply)
        self.color_button.clicked.connect(self.choose_color)

    def refresh(self):
        scene = self.session.project().get("scene", {})
        self._updating = True
        self.width.setValue(scene.get("width", 1920)); self.height.setValue(scene.get("height", 1080))
        self.logic_width.setValue(scene.get("logic_width", 960)); self.logic_height.setValue(scene.get("logic_height", 540))
        self.fps.setValue(scene.get("fps", 60)); self.view_zoom.setValue(scene.get("view_zoom", 2.2))
        self.title.setText(scene.get("title", "Chemanim")); self.color_text.setText(scene.get("background", "FFFFFFFF"))
        size = (self.width.value(), self.height.value())
        match = next((name for name, value in self.PRESETS.items() if value == size), "自定义")
        self.preset.setCurrentText(match); self._update_color_button(); self._updating = False

    def _preset_changed(self, name):
        if self._updating: return
        value = self.PRESETS.get(name)
        if value:
            self.width.setValue(value[0]); self.height.setValue(value[1]); self.apply()

    def choose_color(self):
        dialog = QColorDialog(color_from_rgba(self.color_text.text()), self)
        dialog.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel, True)
        if dialog.exec():
            self.color_text.setText(rgba_text(dialog.selectedColor())); self.apply()

    def _update_color_button(self):
        color = color_from_rgba(self.color_text.text())
        contrast = "black" if color.lightness() > 135 else "white"
        self.color_button.setStyleSheet(f"background: {color.name()}; color: {contrast};")

    def apply(self):
        if self._updating: return
        color = color_from_rgba(self.color_text.text()); self.color_text.setText(rgba_text(color)); self._update_color_button()
        value = {"width": self.width.value(), "height": self.height.value(),
                 "logic_width": self.logic_width.value(), "logic_height": self.logic_height.value(),
                 "fps": self.fps.value(), "background": self.color_text.text().upper(),
                 "title": self.title.text(), "view_zoom": self.view_zoom.value()}
        if self.session.update_scene(json.dumps(value)):
            self.sceneEdited.emit()
