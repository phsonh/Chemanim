from __future__ import annotations

from pathlib import Path
import re

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QDoubleValidator, QIcon, QImageReader, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (
    QColorDialog, QComboBox, QHBoxLayout, QLineEdit,
    QLabel, QPushButton, QSpinBox,
    QTableWidget, QHeaderView, QVBoxLayout, QWidget,
)


NODE_SUBCATEGORIES = {
    "module": "通用", "scene": "通用", "load_texture": "通用",
    "load_textures": "通用",
    "wait": "通用", "raw_lua": "通用",

    "new_object": "创建", "delete": "删除",
    "set_image": "设定", "set_pos": "设定", "set_pos_x": "设定",
    "set_pos_y": "设定", "set_alpha": "设定", "mol_color": "设定",
    "set_scale": "设定", "set_scale_x": "设定", "set_scale_y": "设定",
    "set_rotation": "设定", "set_layer": "设定", "set_visible": "设定",
    "set_anchor": "设定",
    "change_image": "插值", "lerp_pos": "插值", "lerp_pos_x": "插值",
    "lerp_pos_y": "插值", "lerp_alpha": "插值", "lerp_mol_color": "插值",
    "lerp_scale": "插值", "lerp_scale_x": "插值", "lerp_scale_y": "插值",
    "lerp_rotation": "插值",

    "new_arrow": "创建", "delete_arrow": "删除", "arrow_curve": "曲线",
    "arrow_set_pos": "设定", "arrow_color": "设定", "arrow_width": "设定",
    "arrow_progress": "设定", "arrow_lerp_pos": "插值",
    "lerp_arrow_color": "插值", "lerp_arrow": "插值",
    "lerp_arrow_alpha": "插值",

}

SUBCATEGORY_ORDER = {
    "通用": ["通用"],
    "分子": ["创建", "设定", "插值", "删除"],
    "箭头": ["创建", "曲线", "设定", "插值", "删除"],
}


def node_subcategory(node_type: str) -> str:
    return NODE_SUBCATEGORIES.get(node_type, "其他")


def ordered_subcategories(category: str, node_types: list[str]) -> list[str]:
    available = {node_subcategory(node_type) for node_type in node_types}
    preferred = SUBCATEGORY_ORDER.get(category, [])
    result = [name for name in preferred if name in available]
    result.extend(sorted(available.difference(result)))
    return result


_texture_preview_cache: dict[tuple[str, int, int, int, int], QPixmap] = {}


def _texture_preview(
    path: Path, background: QColor | None = None,
    width: int = 132, height: int = 70,
) -> QPixmap:
    background = QColor(background or QColor("white"))
    try:
        timestamp = path.stat().st_mtime_ns
    except OSError:
        timestamp = -1
    key = (str(path.resolve()), timestamp, background.rgba(), width, height)
    cached = _texture_preview_cache.get(key)
    if cached is not None:
        return cached

    preview = QPixmap(width, height)
    preview.fill(background)
    painter = QPainter(preview)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    source = QPixmap(str(path))
    if source.isNull():
        painter.setPen(QColor("#b91c1c"))
        painter.drawText(preview.rect(), Qt.AlignmentFlag.AlignCenter, "PNG 不存在")
    else:
        fitted = source.scaled(
            width - 10, height - 10,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        x = (width - fitted.width()) // 2
        y = (height - fitted.height()) // 2
        painter.drawPixmap(x, y, fitted)
    painter.setPen(QPen(QColor("#94a3b8"), 1))
    painter.drawRect(0, 0, width - 1, height - 1)
    painter.end()
    _texture_preview_cache[key] = preview
    return preview


class TextureResourcePicker(QComboBox):
    """Resource-name picker whose options render the corresponding PNG."""

    def __init__(
        self, resources: list[dict], current: str,
        background: QColor | None = None, parent=None,
    ) -> None:
        super().__init__(parent)
        self.setEditable(False)
        self.setIconSize(QSize(132, 70))
        self.setMinimumHeight(76)
        self.setMaxVisibleItems(7)
        self.view().setMinimumWidth(460)
        self.view().setSpacing(3)

        for resource in resources:
            name = str(resource.get("name", ""))
            file_name = str(resource.get("file", ""))
            path = Path(resource.get("path", file_name))
            image_size = QImageReader(str(path)).size()
            dimensions = (
                f"{image_size.width()}×{image_size.height()}"
                if image_size.isValid() else "文件不存在"
            )
            self.addItem(
                QIcon(_texture_preview(path, background)),
                f"{name}    ·    {file_name}    ·    {dimensions} px"
                if image_size.isValid()
                else f"{name}    ·    {file_name}    ·    {dimensions}",
                name,
            )
            index = self.count() - 1
            self.setItemData(index, f"资源名：{name}\n文件：{file_name}\n尺寸：{dimensions}", Qt.ItemDataRole.ToolTipRole)

        selected = self.findData(str(current), Qt.ItemDataRole.UserRole)
        if selected < 0 and current:
            self.addItem(str(current), str(current))
            selected = self.count() - 1
        if selected >= 0:
            self.setCurrentIndex(selected)

    def resource_name(self) -> str:
        value = self.currentData(Qt.ItemDataRole.UserRole)
        return str(value if value is not None else self.currentText())

    def showPopup(self) -> None:
        super().showPopup()
        self.view().window().setMinimumWidth(max(460, self.width()))


class TextureFileEditor(QWidget):
    """PNG path editor with an always-visible texture preview."""

    def __init__(
        self, mod_directory: Path, current: str,
        background: QColor | None = None, parent=None,
    ) -> None:
        super().__init__(parent)
        self.mod_directory = Path(mod_directory)
        self.background = QColor(background or QColor("white"))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.preview = QLabel()
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumHeight(72)
        layout.addWidget(self.preview)

        self.dimensions = QLabel("—")
        self.dimensions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dimensions.setStyleSheet("font-weight: 600; color: #94a3b8;")
        layout.addWidget(self.dimensions)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        self.edit = QLineEdit(str(current))
        self.button = QPushButton("…")
        self.button.setFixedWidth(34)
        row.addWidget(self.edit, 1)
        row.addWidget(self.button)
        layout.addLayout(row)

        self.edit.editingFinished.connect(self.refresh_preview)
        self.refresh_preview()

    def resolved_path(self) -> Path:
        path = Path(self.edit.text().strip())
        return path if path.is_absolute() else self.mod_directory / path

    def refresh_preview(self) -> None:
        path = self.resolved_path()
        preview = _texture_preview(path, self.background)
        self.preview.setPixmap(preview)
        image_size = QImageReader(str(path)).size()
        dimensions = (
            f"{image_size.width()}×{image_size.height()}"
            if image_size.isValid() else "文件不存在"
        )
        self.dimensions.setText(
            f"{dimensions} px" if image_size.isValid() else dimensions)
        self.preview.setToolTip(f"{path}\n{dimensions}")


class MultiTextureFileEditor(QWidget):
    """Multi-PNG list with a separate normalized anchor for every texture."""

    filesChanged = pyqtSignal(list)

    def __init__(
        self, mod_directory: Path, files: list,
        background: QColor | None = None, parent=None,
    ) -> None:
        super().__init__(parent)
        self.mod_directory = Path(mod_directory)
        self.background = QColor(background or QColor("white"))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.choose_button = QPushButton("选择多个 PNG…")
        layout.addWidget(self.choose_button)
        self.summary = QLabel()
        self.summary.setStyleSheet("font-weight: 600; color: #94a3b8;")
        layout.addWidget(self.summary)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["纹理", "锚点 X", "锚点 Y"])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setMinimumHeight(280)
        self.table.setMaximumHeight(680)
        layout.addWidget(self.table)
        self.set_files(files)

    @staticmethod
    def _normalize(files: list) -> list[dict]:
        result: list[dict] = []
        for value in files:
            if isinstance(value, dict):
                file_name = str(value.get("file", "")).strip()
                anchor_x = float(value.get("anchor_x", 0.5))
                anchor_y = float(value.get("anchor_y", 0.5))
            else:
                file_name = str(value).strip()
                anchor_x = anchor_y = 0.5
            if file_name:
                result.append({
                    "file": file_name,
                    "anchor_x": max(0.0, min(1.0, anchor_x)),
                    "anchor_y": max(0.0, min(1.0, anchor_y)),
                })
        return result

    def set_files(self, files: list) -> None:
        self.files = self._normalize(files)
        self.table.setRowCount(len(self.files))
        for row, entry in enumerate(self.files):
            file_name = entry["file"]
            path = Path(file_name)
            if not path.is_absolute():
                path = self.mod_directory / path
            size = QImageReader(str(path)).size()
            dimensions = (
                f"{size.width()}×{size.height()} px" if size.isValid()
                else "文件不存在"
            )
            texture_cell = QWidget()
            texture_layout = QHBoxLayout(texture_cell)
            texture_layout.setContentsMargins(6, 5, 8, 5)
            texture_layout.setSpacing(10)
            preview = QLabel()
            preview.setFixedSize(280, 158)
            preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
            preview.setPixmap(_texture_preview(path, self.background, 280, 158))
            preview.setStyleSheet("border: 1px solid #526071;")
            preview.setToolTip(
                f"纹理名：{Path(file_name).stem}\n文件：{path}\n尺寸：{dimensions}")
            details = QLabel(
                f"{Path(file_name).stem}\n{Path(file_name).name}\n{dimensions}")
            details.setWordWrap(True)
            details.setMinimumWidth(90)
            texture_layout.addWidget(preview, 0)
            texture_layout.addWidget(details, 1)
            self.table.setCellWidget(row, 0, texture_cell)
            self.table.setRowHeight(row, 170)
            for column, key in ((1, "anchor_x"), (2, "anchor_y")):
                edit = QLineEdit(f"{float(entry[key]):.2f}")
                edit.setValidator(QDoubleValidator(0.0, 1.0, 2, edit))
                edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
                edit.editingFinished.connect(self._anchors_changed)
                self.table.setCellWidget(row, column, edit)
        self.summary.setText(f"共 {len(self.files)} 张 PNG" if self.files else "尚未选择 PNG")

    def values(self) -> list[dict]:
        result: list[dict] = []
        for row, entry in enumerate(self.files):
            x_widget = self.table.cellWidget(row, 1)
            y_widget = self.table.cellWidget(row, 2)
            try:
                anchor_x = float(x_widget.text()) if isinstance(x_widget, QLineEdit) else 0.5
            except ValueError:
                anchor_x = 0.5
            try:
                anchor_y = float(y_widget.text()) if isinstance(y_widget, QLineEdit) else 0.5
            except ValueError:
                anchor_y = 0.5
            result.append({
                "file": entry["file"],
                "anchor_x": max(0.0, min(1.0, anchor_x)),
                "anchor_y": max(0.0, min(1.0, anchor_y)),
            })
        return result

    def _anchors_changed(self) -> None:
        self.files = self.values()
        self.filesChanged.emit(self.files)


def parse_color_text(value: str) -> tuple[QColor, bool] | None:
    text = str(value).strip()
    function = re.fullmatch(
        r"(?i)(rgba?|RGBA?)\s*\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})"
        r"(?:\s*,\s*(\d{1,3}))?\s*\)", text)
    if function:
        channels = [int(function.group(index)) for index in range(2, 6) if function.group(index) is not None]
        if any(channel > 255 for channel in channels):
            return None
        has_alpha = function.group(1).lower() == "rgba"
        if has_alpha and len(channels) != 4:
            return None
        if not has_alpha and len(channels) != 3:
            return None
        return QColor(*channels, 255) if len(channels) == 3 else QColor(*channels), has_alpha

    comma_channels = [part.strip() for part in text.split(",")]
    if len(comma_channels) in (3, 4) and all(part.isdigit() for part in comma_channels):
        channels = [int(part) for part in comma_channels]
        if any(channel > 255 for channel in channels):
            return None
        return QColor(*channels, 255) if len(channels) == 3 else QColor(*channels), len(channels) == 4

    compact = text.removeprefix("#")
    if re.fullmatch(r"(?i)[0-9a-f]{6}", compact):
        return QColor("#" + compact), False
    if re.fullmatch(r"(?i)[0-9a-f]{8}", compact):
        return QColor(
            int(compact[0:2], 16), int(compact[2:4], 16),
            int(compact[4:6], 16), int(compact[6:8], 16)), True
    return None


def format_color_text(color: QColor, include_alpha: bool) -> str:
    rgb = f"{color.red():02X}{color.green():02X}{color.blue():02X}"
    return rgb + (f"{color.alpha():02X}" if include_alpha else "")


class ColorValueEditor(QWidget):
    """Visual HEX/RGB/RGBA editor that emits an engine-ready color string."""

    colorChanged = pyqtSignal(str)

    def __init__(self, current: str, parent=None) -> None:
        super().__init__(parent)
        parsed = parse_color_text(str(current)) or (QColor(255, 255, 255, 255), True)
        self.color, self.include_alpha = parsed
        self.updating = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        first_row = QHBoxLayout()
        first_row.setContentsMargins(0, 0, 0, 0)
        self.swatch = QPushButton()
        self.swatch.setFixedSize(32, 26)
        self.swatch.setToolTip("打开系统颜色选择器")
        self.text = QLineEdit(format_color_text(self.color, self.include_alpha))
        self.text.setPlaceholderText("RRGGBB / RRGGBBAA / rgb(...) / rgba(...)")
        self.text.setToolTip(
            "支持 RRGGBB、RRGGBBAA、rgb(r,g,b)、rgba(r,g,b,a) 和逗号分隔 RGB(A)")
        self.choose = QPushButton("选择…")
        first_row.addWidget(self.swatch)
        first_row.addWidget(self.text, 1)
        first_row.addWidget(self.choose)
        layout.addLayout(first_row)

        channel_row = QHBoxLayout()
        channel_row.setContentsMargins(0, 0, 0, 0)
        channel_row.setSpacing(3)
        self.channels: list[QSpinBox] = []
        for prefix, value in zip(
            ("R ", "G ", "B ", "A "),
            (self.color.red(), self.color.green(), self.color.blue(), self.color.alpha()),
        ):
            spin = QSpinBox()
            spin.setRange(0, 255)
            spin.setPrefix(prefix)
            spin.setValue(value)
            spin.valueChanged.connect(self._channels_changed)
            channel_row.addWidget(spin)
            self.channels.append(spin)
        layout.addLayout(channel_row)

        self.swatch.clicked.connect(self._choose_color)
        self.choose.clicked.connect(self._choose_color)
        self.text.editingFinished.connect(self._text_finished)
        self._update_swatch()

    def _update_swatch(self) -> None:
        self.swatch.setStyleSheet(
            "QPushButton {"
            f"background-color: rgba({self.color.red()}, {self.color.green()}, "
            f"{self.color.blue()}, {self.color.alpha()});"
            "border: 1px solid #94a3b8; border-radius: 3px;"
            "}")

    def _sync_widgets(self) -> None:
        self.updating = True
        try:
            self.text.setText(format_color_text(self.color, self.include_alpha))
            for spin, value in zip(
                self.channels,
                (self.color.red(), self.color.green(), self.color.blue(), self.color.alpha()),
            ):
                spin.setValue(value)
            self.text.setStyleSheet("")
            self._update_swatch()
        finally:
            self.updating = False

    def _emit(self) -> None:
        self._sync_widgets()
        self.colorChanged.emit(format_color_text(self.color, self.include_alpha))

    def _channels_changed(self) -> None:
        if self.updating:
            return
        self.color = QColor(*(spin.value() for spin in self.channels))
        if self.color.alpha() != 255:
            self.include_alpha = True
        self._emit()

    def _text_finished(self) -> None:
        parsed = parse_color_text(self.text.text())
        if parsed is None:
            self.text.setStyleSheet("border: 1px solid #dc2626;")
            self.text.setToolTip("颜色格式无效。请输入 HEX、RGB 或 RGBA。")
            return
        self.color, self.include_alpha = parsed
        self._emit()

    def _choose_color(self) -> None:
        selected = QColorDialog.getColor(
            self.color, self, "选择场景背景颜色",
            QColorDialog.ColorDialogOption.ShowAlphaChannel)
        if not selected.isValid():
            return
        self.color = selected
        self.include_alpha = True
        self._emit()


def compact_nepy_stylesheet() -> str:
    return """
        QLabel#panelTitle { font-weight: 600; padding: 4px 5px; }
        QLabel#inspectorTitle { font-size: 16px; font-weight: 600; padding: 5px; }
        QTabBar#nodeCategoryTabs::tab {
            padding: 7px 16px; margin-right: 1px; border: 1px solid #454b54;
            border-bottom: 0; border-top-left-radius: 4px; border-top-right-radius: 4px;
        }
        QTabBar#nodeCategoryTabs::tab:selected { background: #334155; color: #f8fafc; }
        QTabBar#nodeSubcategoryTabs {
            background: #20242a; border-bottom: 1px solid #454b54;
        }
        QTabBar#nodeSubcategoryTabs::tab {
            min-width: 70px; padding: 5px 14px; margin: 3px 2px 2px 2px;
            border-radius: 3px; color: #cbd5e1;
        }
        QTabBar#nodeSubcategoryTabs::tab:hover { background: #374151; }
        QTabBar#nodeSubcategoryTabs::tab:selected {
            background: #475569; color: white; font-weight: 600;
        }
        QToolBar { spacing: 4px; padding: 3px; border-bottom: 1px solid #454b54; }
        QToolButton { padding: 5px 8px; border-radius: 3px; }
        QToolButton:hover { background: #374151; }
        QTreeWidget { outline: 0; }
        QTreeWidget::item { min-height: 29px; padding: 2px 6px; }
        QTreeWidget::item:selected { background: #1d4ed8; color: white; }
        QTableWidget::item { padding: 4px; }
    """
