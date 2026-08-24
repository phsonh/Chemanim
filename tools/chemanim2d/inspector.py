from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QDoubleSpinBox, QFormLayout, QLabel, QWidget

from .model import Molecule


class AtomInspector(QWidget):
    atomEdited = pyqtSignal()
    def __init__(self,parent=None):
        super().__init__(parent); self.molecule=None; self.atom_id=None; self._updating=False
        self.title=QLabel("未选择原子"); self.x=QDoubleSpinBox(); self.y=QDoubleSpinBox()
        for box in (self.x,self.y): box.setRange(-10000,10000); box.setDecimals(2); box.setSingleStep(.1); box.valueChanged.connect(self._apply)
        layout=QFormLayout(self); layout.addRow(self.title); layout.addRow("X",self.x); layout.addRow("Y",self.y)
        self.x.setEnabled(False); self.y.setEnabled(False)
    def set_selection(self,molecule:Molecule|None, selected:set[str]):
        self.molecule=molecule; self.atom_id=next(iter(selected)) if len(selected)==1 else None; self._refresh()
    def _refresh(self):
        self._updating=True
        atom=next((a for a in self.molecule.atoms if a.id==self.atom_id),None) if self.molecule else None
        if atom: self.title.setText(f"{atom.id} · {atom.element}"); self.x.setValue(atom.x); self.y.setValue(atom.y)
        else: self.title.setText("选择一个原子以精确输入坐标")
        self.x.setEnabled(bool(atom)); self.y.setEnabled(bool(atom)); self._updating=False
    def refresh_values(self): self._refresh()
    def _apply(self):
        if self._updating or not self.molecule or not self.atom_id: return
        atom=next((a for a in self.molecule.atoms if a.id==self.atom_id),None)
        if atom: atom.x=round(self.x.value(),4); atom.y=round(self.y.value(),4); self.atomEdited.emit()
