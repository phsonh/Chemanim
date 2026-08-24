from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QComboBox, QDoubleSpinBox, QFormLayout, QLabel, QPushButton, QHBoxLayout, QWidget

from .core import CoreSession


class AtomInspector(QWidget):
    atomEdited = pyqtSignal()

    def __init__(self, session: CoreSession, parent=None):
        super().__init__(parent); self.session = session; self.atom_id = None; self._updating = False
        self.title = QLabel("未选择原子")
        self.element = QComboBox(); self.element.setEditable(True)
        self.element.addItems(["C", "H", "N", "O", "F", "P", "S", "Cl", "Br", "I", "B", "Si"])
        self.x = QDoubleSpinBox(); self.y = QDoubleSpinBox()
        for box in (self.x, self.y): box.setRange(-10000, 10000); box.setDecimals(2); box.setSingleStep(.1); box.editingFinished.connect(self._apply_position)
        self.element.currentTextChanged.connect(self._apply_element)
        plus = QPushButton("+"); minus = QPushButton("−"); plus.clicked.connect(lambda: self._charge(1)); minus.clicked.connect(lambda: self._charge(-1))
        charge = QWidget(); row = QHBoxLayout(charge); row.setContentsMargins(0, 0, 0, 0); row.addWidget(plus); row.addWidget(minus)
        layout = QFormLayout(self); layout.addRow(self.title); layout.addRow("元素", self.element); layout.addRow("X", self.x); layout.addRow("Y", self.y); layout.addRow("电荷", charge)
        self._enable(False)

    def _enable(self, enabled):
        self.element.setEnabled(enabled); self.x.setEnabled(enabled); self.y.setEnabled(enabled)

    def set_selection(self, atom_ids, bond_ids):
        self.atom_id = atom_ids[0] if len(atom_ids) == 1 else None; self.refresh_values()

    def _atom(self):
        project = self.session.project(); active = self.session.active_molecule
        molecule = next((item for item in project.get("molecules", []) if item["id"] == active), None)
        return next((atom for atom in molecule["atoms"] if atom["id"] == self.atom_id), None) if molecule else None

    def refresh_values(self):
        self._updating = True; atom = self._atom()
        if atom:
            self.title.setText(f'{atom["id"]} · 电荷 {atom["formal_charge"]:+d}')
            self.element.setCurrentText(atom["element"]); self.x.setValue(atom["x"]); self.y.setValue(atom["y"])
        else: self.title.setText("选择一个原子以编辑属性")
        self._enable(bool(atom)); self._updating = False

    def _apply_position(self):
        if self._updating or not self.atom_id: return
        if self.session.set_atom_position(self.atom_id, round(self.x.value(), 2), round(self.y.value(), 2)): self.atomEdited.emit()

    def _apply_element(self, value):
        if self._updating or not self.atom_id or not value.strip(): return
        if self.session.set_atom_element(self.atom_id, value.strip()): self.atomEdited.emit()

    def _charge(self, delta):
        if self.atom_id and self.session.change_atom_charge(self.atom_id, delta): self.refresh_values(); self.atomEdited.emit()
