from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QDialog, QGridLayout, QHBoxLayout, QLabel,
                             QSizePolicy, QToolButton, QVBoxLayout, QWidget)


MAIN_PERIODS = {
    1: ((1, "H", 1), (2, "He", 18)),
    2: ((3, "Li", 1), (4, "Be", 2), (5, "B", 13), (6, "C", 14),
        (7, "N", 15), (8, "O", 16), (9, "F", 17), (10, "Ne", 18)),
    3: ((11, "Na", 1), (12, "Mg", 2), (13, "Al", 13), (14, "Si", 14),
        (15, "P", 15), (16, "S", 16), (17, "Cl", 17), (18, "Ar", 18)),
    4: tuple((z, symbol, group) for z, symbol, group in zip(
        range(19, 37),
        ("K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr"),
        range(1, 19))),
    5: tuple((z, symbol, group) for z, symbol, group in zip(
        range(37, 55),
        ("Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn", "Sb", "Te", "I", "Xe"),
        range(1, 19))),
    6: ((55, "Cs", 1), (56, "Ba", 2), (72, "Hf", 4), (73, "Ta", 5),
        (74, "W", 6), (75, "Re", 7), (76, "Os", 8), (77, "Ir", 9),
        (78, "Pt", 10), (79, "Au", 11), (80, "Hg", 12), (81, "Tl", 13),
        (82, "Pb", 14), (83, "Bi", 15), (84, "Po", 16), (85, "At", 17), (86, "Rn", 18)),
    7: ((87, "Fr", 1), (88, "Ra", 2), (104, "Rf", 4), (105, "Db", 5),
        (106, "Sg", 6), (107, "Bh", 7), (108, "Hs", 8), (109, "Mt", 9),
        (110, "Ds", 10), (111, "Rg", 11), (112, "Cn", 12), (113, "Nh", 13),
        (114, "Fl", 14), (115, "Mc", 15), (116, "Lv", 16), (117, "Ts", 17), (118, "Og", 18)),
}

LANTHANIDES = tuple(zip(range(57, 72),
    ("La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu")))
ACTINIDES = tuple(zip(range(89, 104),
    ("Ac", "Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr")))


def element_color(symbol: str) -> str:
    if symbol in {"He", "Ne", "Ar", "Kr", "Xe", "Rn", "Og"}: return "#4b6284"
    if symbol in {"F", "Cl", "Br", "I", "At", "Ts"}: return "#416b61"
    if symbol in {"H", "C", "N", "O", "P", "S", "Se"}: return "#4e5965"
    if symbol in {"B", "Si", "Ge", "As", "Sb", "Te", "Po"}: return "#6b6045"
    if symbol in {"Li", "Na", "K", "Rb", "Cs", "Fr"}: return "#704c55"
    if symbol in {"Be", "Mg", "Ca", "Sr", "Ba", "Ra"}: return "#6a5a43"
    if any(symbol == value for _, value in LANTHANIDES): return "#5d4f75"
    if any(symbol == value for _, value in ACTINIDES): return "#654a67"
    return "#445d70"


class PeriodicTableDialog(QDialog):
    """Compact real periodic-table picker with later periods folded by default."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_element = ""
        self.buttons: dict[str, QToolButton] = {}
        self.setWindowTitle("选择元素")
        self.setModal(True)

        layout = QVBoxLayout(self);layout.setContentsMargins(14,12,14,12);layout.setSpacing(8)
        title=QLabel("元素周期表");title.setObjectName("inspectorTitle");layout.addWidget(title)
        note=QLabel("默认显示第 1–3 周期；展开后可选择其余元素。");note.setStyleSheet("color:#aeb7c2");layout.addWidget(note)

        self.table=QWidget();self.table_layout=QGridLayout(self.table);self.table_layout.setContentsMargins(0,0,0,0);self.table_layout.setHorizontalSpacing(4);self.table_layout.setVerticalSpacing(4)
        self.table_layout.addWidget(QLabel("周期 / 族"),0,0)
        for group in range(1,19):
            label=QLabel(str(group));label.setAlignment(Qt.AlignmentFlag.AlignCenter);label.setStyleSheet("color:#8f9aa6");self.table_layout.addWidget(label,0,group)
        for row,period in enumerate((1,2,3),start=1):self._add_period(self.table_layout,row,period)
        layout.addWidget(self.table)

        self.expand_button=QToolButton();self.expand_button.setText("展开第 4–7 周期");self.expand_button.setCheckable(True);self.expand_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly);self.expand_button.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed);self.expand_button.toggled.connect(self._set_expanded);layout.addWidget(self.expand_button)

        self.expanded=QWidget();expanded_layout=QGridLayout(self.expanded);expanded_layout.setContentsMargins(0,0,0,0);expanded_layout.setHorizontalSpacing(4);expanded_layout.setVerticalSpacing(4)
        for row,period in enumerate((4,5,6,7)):
            self._add_period(expanded_layout,row,period)
            if period in (6,7):
                marker=QLabel("57–71" if period==6 else "89–103");marker.setAlignment(Qt.AlignmentFlag.AlignCenter);marker.setStyleSheet("color:#aeb7c2;border:1px dashed #505862");expanded_layout.addWidget(marker,row,3)
        self._add_series(expanded_layout,5,"镧系",LANTHANIDES)
        self._add_series(expanded_layout,6,"锕系",ACTINIDES)
        self.expanded.setVisible(False);layout.addWidget(self.expanded)
        self.setMinimumWidth(1040)

    def _button(self, atomic_number: int, symbol: str) -> QToolButton:
        button=QToolButton();button.setText(f"{atomic_number}\n{symbol}");button.setToolTip(f"原子序数 {atomic_number} · {symbol}")
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly);button.setMinimumSize(48,48);button.setStyleSheet(
            f"QToolButton{{background:{element_color(symbol)};border:1px solid #71808e;border-radius:3px;color:#f0f3f6;padding:2px}}"
            "QToolButton:hover{border:2px solid #65aaf2;background:#376b99}")
        button.clicked.connect(lambda _checked=False,value=symbol:self._choose(value));self.buttons[symbol]=button;return button

    def _add_period(self, layout: QGridLayout, row: int, period: int):
        label=QLabel(str(period));label.setAlignment(Qt.AlignmentFlag.AlignCenter);label.setStyleSheet("color:#aeb7c2;font-weight:600");layout.addWidget(label,row,0)
        for atomic_number,symbol,group in MAIN_PERIODS[period]:layout.addWidget(self._button(atomic_number,symbol),row,group)

    def _add_series(self, layout: QGridLayout, row: int, label_text: str, series):
        label=QLabel(label_text);label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter);label.setStyleSheet("color:#aeb7c2");layout.addWidget(label,row,0,1,3)
        for column,(atomic_number,symbol) in enumerate(series,start=4):layout.addWidget(self._button(atomic_number,symbol),row,column)

    def _set_expanded(self, expanded: bool):
        self.expanded.setVisible(expanded);self.expand_button.setText(("收起第 4–7 周期" if expanded else "展开第 4–7 周期"));self.adjustSize()

    def _choose(self, symbol: str):
        self.selected_element=symbol;self.accept()
