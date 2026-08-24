from __future__ import annotations

from PyQt6.QtCore import QByteArray, QPointF, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QImage, QKeyEvent, QMouseEvent, QPainter, QPen, QPolygonF, QWheelEvent
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QWidget

from .core import CoreSession


class StructureCanvas(QWidget):
    selectionChanged = pyqtSignal(list, list)
    transactionCommitted = pyqtSignal()
    hoverChanged = pyqtSignal(dict)

    def __init__(self, session: CoreSession, parent=None):
        super().__init__(parent)
        self.session = session
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.setMinimumSize(640, 420)
        self.pixels_per_unit = 48.0
        self.center_x = 0.0
        self.center_y = 0.0
        self.final_effect = False
        self._depiction = None
        self._svg = None
        self._raster = None
        self._selected_atoms = []
        self._selected_bonds = []
        self._preview = {"active": False}
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._refresh_now)

    def _sync_viewport(self):
        self.session.set_viewport(max(1, self.width()), max(1, self.height()),
                                  self.pixels_per_unit, self.center_x, self.center_y)

    def request_refresh(self):
        if not self._timer.isActive(): self._timer.start(16)

    def _refresh_now(self):
        self._sync_viewport()
        try: data = self.session.depict(self.final_effect)
        except RuntimeError:
            self._depiction = self._svg = self._raster = None
            self.update(); return
        self._depiction = data
        if self.final_effect:
            image = QImage(data["rgba"], data["width"], data["height"], QImage.Format.Format_RGBA8888)
            self._raster = image.copy(); self._svg = None
        else:
            self._svg = QSvgRenderer(QByteArray(data["svg"].encode("utf-8"))); self._raster = None
        self.update()

    def set_final_effect(self, enabled: bool):
        self.final_effect = enabled; self.request_refresh()

    @property
    def selected_atoms(self): return list(self._selected_atoms)

    def fit(self):
        project = self.session.project(); active = self.session.active_molecule
        molecule = next((item for item in project.get("molecules", []) if item["id"] == active), None)
        if not molecule or not molecule["atoms"]:
            self.center_x = self.center_y = 0.0; self.pixels_per_unit = 48.0
        else:
            xs = [atom["x"] for atom in molecule["atoms"]]; ys = [atom["y"] for atom in molecule["atoms"]]
            self.center_x = (min(xs) + max(xs)) * .5; self.center_y = (min(ys) + max(ys)) * .5
            span_x = max(max(xs) - min(xs), 2.0); span_y = max(max(ys) - min(ys), 2.0)
            self.pixels_per_unit = max(12.0, min(110.0, min(self.width() * .72 / span_x, self.height() * .72 / span_y)))
        self.request_refresh()

    def resizeEvent(self, event):
        super().resizeEvent(event); self.request_refresh()

    def _background(self):
        value = self.session.project().get("scene", {}).get("background", "FFFFFFFF")
        try: return QColor(int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16), int(value[6:8], 16))
        except (ValueError, IndexError): return QColor("white")

    def paintEvent(self, event):
        painter = QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), self._background())
        painter.setPen(QPen(QColor(120, 135, 150, 32), 1)); spacing = max(24, int(self.pixels_per_unit))
        ox = int(self.width() * .5 - self.center_x * self.pixels_per_unit) % spacing
        oy = int(self.height() * .5 + self.center_y * self.pixels_per_unit) % spacing
        for x in range(ox, self.width(), spacing): painter.drawLine(x, 0, x, self.height())
        for y in range(oy, self.height(), spacing): painter.drawLine(0, y, self.width(), y)
        if self._raster: painter.drawImage(QRectF(self.rect()), self._raster)
        elif self._svg: self._svg.render(painter, QRectF(self.rect()))
        if self._depiction:
            points = {item["id"]: item["center"] for item in self._depiction["atoms"]}
            painter.setPen(QPen(QColor(0, 120, 215), 2)); painter.setBrush(QColor(0, 120, 215, 34))
            for atom_id in self._selected_atoms:
                if atom_id in points:
                    point = points[atom_id]; painter.drawEllipse(QPointF(point["x"], point["y"]), 10, 10)
        if self._preview.get("active"):
            polygon = self._preview.get("polygon", [])
            painter.setPen(QPen(QColor(0, 120, 215, 170), 2, Qt.PenStyle.DashLine)); painter.setBrush(QColor(0, 120, 215, 28))
            if polygon: painter.drawPolygon(QPolygonF([QPointF(item["x"], item["y"]) for item in polygon]))
            else:
                start, current = self._preview.get("start"), self._preview.get("current")
                if start and current: painter.drawLine(QPointF(start["x"], start["y"]), QPointF(current["x"], current["y"]))

    @staticmethod
    def _mods(event):
        mods = event.modifiers()
        return bool(mods & Qt.KeyboardModifier.AltModifier), bool(mods & Qt.KeyboardModifier.ControlModifier), bool(mods & Qt.KeyboardModifier.ShiftModifier)

    def _consume(self, result):
        self._selected_atoms = list(result["selected_atoms"]); self._selected_bonds = list(result["selected_bonds"]); self._preview = result["preview"]
        self.selectionChanged.emit(self._selected_atoms, self._selected_bonds); self.hoverChanged.emit(result["hover"]); self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() != Qt.MouseButton.LeftButton: return
        self.setFocus(); alt, control, shift = self._mods(event)
        self._consume(self.session.pointer_down(event.position().x(), event.position().y(), alt, control, shift))

    def mouseMoveEvent(self, event: QMouseEvent):
        alt, control, shift = self._mods(event)
        self._consume(self.session.pointer_move(event.position().x(), event.position().y(), alt, control, shift))
        self.request_refresh()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() != Qt.MouseButton.LeftButton: return
        alt, control, shift = self._mods(event)
        result = self.session.pointer_up(event.position().x(), event.position().y(), alt, control, shift)
        self._consume(result); self.request_refresh()
        if result["changed"]: self.transactionCommitted.emit()

    def wheelEvent(self, event: QWheelEvent):
        self.pixels_per_unit = max(10.0, min(180.0, self.pixels_per_unit * (1.12 if event.angleDelta().y() > 0 else 1 / 1.12)))
        self.request_refresh()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            if self.session.delete_selection():
                self._selected_atoms.clear(); self._selected_bonds.clear(); self.selectionChanged.emit([], [])
                self.request_refresh(); self.transactionCommitted.emit()
            return
        if event.key() == Qt.Key.Key_Escape:
            self.session.cancel_gesture(); self._preview = {"active": False}; self.request_refresh(); return
        super().keyPressEvent(event)
