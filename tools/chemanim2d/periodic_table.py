from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QDialog, QGridLayout, QLabel, QScrollArea,
                             QToolButton, QVBoxLayout, QWidget)


# Complete 32-column long form.  The f-block stays in periods 6 and 7 instead
# of being detached into two footnote rows.
_SYMBOLS = (
    "H", "He",
    "Li", "Be", "B", "C", "N", "O", "F", "Ne",
    "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar",
    "K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr",
    "Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn", "Sb", "Te", "I", "Xe",
    "Cs", "Ba", "La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu", "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg", "Tl", "Pb", "Bi", "Po", "At", "Rn",
    "Fr", "Ra", "Ac", "Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr", "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds", "Rg", "Cn", "Nh", "Fl", "Mc", "Lv", "Ts", "Og",
)


def _long_period(period: int, symbols: tuple[str, ...], start: int):
    if period == 1:
        columns = (1, 32)
    elif period in (2, 3):
        columns = (1, 2, 27, 28, 29, 30, 31, 32)
    elif period in (4, 5):
        columns = (1, 2, *range(17, 33))
    else:
        columns = tuple(range(1, 33))
    return tuple((start + index, symbol, columns[index]) for index, symbol in enumerate(symbols))


LONG_PERIODS = {
    1: _long_period(1, _SYMBOLS[0:2], 1),
    2: _long_period(2, _SYMBOLS[2:10], 3),
    3: _long_period(3, _SYMBOLS[10:18], 11),
    4: _long_period(4, _SYMBOLS[18:36], 19),
    5: _long_period(5, _SYMBOLS[36:54], 37),
    6: _long_period(6, _SYMBOLS[54:86], 55),
    7: _long_period(7, _SYMBOLS[86:118], 87),
}


def element_color(symbol: str) -> str:
    if symbol in {"He", "Ne", "Ar", "Kr", "Xe", "Rn", "Og"}: return "#4b6284"
    if symbol in {"F", "Cl", "Br", "I", "At", "Ts"}: return "#416b61"
    if symbol in {"H", "C", "N", "O", "P", "S", "Se"}: return "#4e5965"
    if symbol in {"B", "Si", "Ge", "As", "Sb", "Te", "Po"}: return "#6b6045"
    if symbol in {"Li", "Na", "K", "Rb", "Cs", "Fr"}: return "#704c55"
    if symbol in {"Be", "Mg", "Ca", "Sr", "Ba", "Ra"}: return "#6a5a43"
    if symbol in _SYMBOLS[56:71]: return "#5d4f75"
    if symbol in _SYMBOLS[88:103]: return "#654a67"
    return "#445d70"


class PeriodicTableDialog(QDialog):
    """Complete 32-column long-form periodic-table element picker."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_element = ""
        self.buttons: dict[str, QToolButton] = {}
        self.setWindowTitle("选择元素")
        self.setModal(True)

        layout = QVBoxLayout(self);layout.setContentsMargins(14,12,14,12);layout.setSpacing(8)
        title=QLabel("元素周期表");title.setObjectName("inspectorTitle");layout.addWidget(title)
        note=QLabel("完整长周期表；点击元素即可选择。");note.setStyleSheet("color:#aeb7c2");layout.addWidget(note)

        self.table=QWidget();self.table_layout=QGridLayout(self.table);self.table_layout.setContentsMargins(0,0,0,0);self.table_layout.setHorizontalSpacing(2);self.table_layout.setVerticalSpacing(3)
        self.table_layout.addWidget(QLabel("周期"),0,0)
        group_columns={1:1,2:2,**{group:group+14 for group in range(3,19)}}
        for group,column in group_columns.items():
            label=QLabel(str(group));label.setAlignment(Qt.AlignmentFlag.AlignCenter);label.setStyleSheet("color:#8f9aa6");self.table_layout.addWidget(label,0,column)
        f_label=QLabel("f 区");f_label.setAlignment(Qt.AlignmentFlag.AlignCenter);f_label.setStyleSheet("color:#737f8b");self.table_layout.addWidget(f_label,0,3,1,14)
        for period in range(1,8):self._add_period(period)

        scroll=QScrollArea();scroll.setWidgetResizable(False);scroll.setFrameShape(QScrollArea.Shape.NoFrame);scroll.setWidget(self.table);layout.addWidget(scroll)
        self.resize(1540,570);self.setMinimumSize(980,500)

    def _button(self, atomic_number: int, symbol: str) -> QToolButton:
        button=QToolButton();button.setText(f"{atomic_number}\n{symbol}");button.setToolTip(f"原子序数 {atomic_number} · {symbol}")
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly);button.setFixedSize(40,46);button.setStyleSheet(
            f"QToolButton{{background:{element_color(symbol)};border:1px solid #71808e;border-radius:3px;color:#f0f3f6;padding:1px}}"
            "QToolButton:hover{border:2px solid #65aaf2;background:#376b99}")
        button.clicked.connect(lambda _checked=False,value=symbol:self._choose(value));self.buttons[symbol]=button;return button

    def _add_period(self, period: int):
        label=QLabel(str(period));label.setAlignment(Qt.AlignmentFlag.AlignCenter);label.setStyleSheet("color:#aeb7c2;font-weight:600");self.table_layout.addWidget(label,period,0)
        for atomic_number,symbol,column in LONG_PERIODS[period]:self.table_layout.addWidget(self._button(atomic_number,symbol),period,column)

    def _choose(self, symbol: str):
        self.selected_element=symbol;self.accept()
