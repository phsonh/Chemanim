from __future__ import annotations

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import (QDialog, QDialogButtonBox, QDoubleSpinBox,
                             QFormLayout, QGroupBox, QLabel, QPushButton,
                             QSpinBox, QVBoxLayout)


DEFAULT_PREFERENCES = {
    "canvas_width": 1920,
    "canvas_height": 1080,
    "logic_width": 960,
    "logic_height": 540,
    "default_arrow_width": 1.5,
    "charge_adornment_distance": 20.0,
    "electron_dot_radius_pt": 0.75,
    "electron_adornment_distance": 20.0,
}

PREFERENCE_RANGES = {
    "canvas_width": (64, 16384),
    "canvas_height": (64, 16384),
    "logic_width": (64, 16384),
    "logic_height": (64, 16384),
    "default_arrow_width": (0.1, 50.0),
    "charge_adornment_distance": (1.0, 200.0),
    "electron_dot_radius_pt": (0.1, 10.0),
    "electron_adornment_distance": (1.0, 200.0),
}


class PreferenceStore:
    """Persistent application defaults, separated from document state."""

    PREFIX = "preferences/"

    def __init__(self, settings: QSettings | None = None):
        self.settings = settings or QSettings("Chemanim", "Chemanim")

    def values(self) -> dict:
        result = {}
        for key, default in DEFAULT_PREFERENCES.items():
            raw = self.settings.value(self.PREFIX + key, default)
            try:
                value = int(raw) if isinstance(default, int) else float(raw)
                minimum, maximum = PREFERENCE_RANGES[key]
                result[key] = min(max(value, minimum), maximum)
            except (TypeError, ValueError):
                result[key] = default
        return result

    def save(self, values: dict) -> None:
        for key, default in DEFAULT_PREFERENCES.items():
            value = values.get(key, default)
            self.settings.setValue(self.PREFIX + key, value)
        self.settings.sync()

    def restore_defaults(self) -> None:
        self.settings.remove(self.PREFIX.rstrip("/"))
        self.settings.sync()


class PreferencesDialog(QDialog):
    def __init__(self, store: PreferenceStore, parent=None):
        super().__init__(parent)
        self.setWindowTitle("首选项")
        self.store = store
        self.fields: dict[str, QSpinBox | QDoubleSpinBox] = {}

        canvas_group = QGroupBox("新工程画布")
        canvas_form = QFormLayout(canvas_group)
        for key, label in (("canvas_width", "默认画布宽度（px）"),
                           ("canvas_height", "默认画布高度（px）"),
                           ("logic_width", "默认逻辑宽度"),
                           ("logic_height", "默认逻辑高度")):
            field = QSpinBox()
            field.setObjectName(key)
            field.setRange(*PREFERENCE_RANGES[key])
            canvas_form.addRow(label, field)
            self.fields[key] = field

        drawing_group = QGroupBox("结构绘制")
        drawing_form = QFormLayout(drawing_group)
        for key, label in (
            ("default_arrow_width", "默认箭头线宽"),
            ("charge_adornment_distance", "电荷离原子默认距离"),
            ("electron_dot_radius_pt", "电子点半径（pt）"),
            ("electron_adornment_distance", "电子对/单电子离原子默认距离"),
        ):
            field = QDoubleSpinBox()
            field.setObjectName(key)
            field.setDecimals(2)
            field.setSingleStep(0.1 if key in ("default_arrow_width", "electron_dot_radius_pt") else 1.0)
            field.setRange(*PREFERENCE_RANGES[key])
            drawing_form.addRow(label, field)
            self.fields[key] = field

        note = QLabel("画布与逻辑分辨率只用于之后新建的工程；绘制参数会同时应用到当前工程，并随 .cmm 保存。")
        note.setWordWrap(True)
        self.restore_button = QPushButton("恢复默认值")
        self.restore_button.setObjectName("restore_defaults")
        self.restore_button.clicked.connect(self.reset_fields)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                        QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(canvas_group)
        layout.addWidget(drawing_group)
        layout.addWidget(note)
        layout.addWidget(self.restore_button)
        layout.addWidget(self.buttons)
        self.set_values(store.values())
        self.resize(520, 430)

    def set_values(self, values: dict) -> None:
        for key, field in self.fields.items():
            field.setValue(values.get(key, DEFAULT_PREFERENCES[key]))

    def reset_fields(self) -> None:
        self.set_values(DEFAULT_PREFERENCES)

    def values(self) -> dict:
        return {key: field.value() for key, field in self.fields.items()}
