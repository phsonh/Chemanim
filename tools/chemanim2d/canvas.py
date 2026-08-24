from __future__ import annotations

from PyQt6.QtCore import QPoint, QPointF, QRect, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QMouseEvent, QPainter, QPaintEvent, QPen, QWheelEvent
from PyQt6.QtWidgets import QWidget

from .drawing import median_bond_length, molecule_bounds, paint_molecule
from .model import Molecule


class StructureCanvas(QWidget):
    selectionChanged = pyqtSignal(object)
    coordinatesChanged = pyqtSignal()
    dragCommitted = pyqtSignal(object, object)

    def __init__(self, parent=None):
        super().__init__(parent); self.setMinimumSize(620, 420); self.setMouseTracking(True); self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.molecule: Molecule | None = None; self.selected: set[str] = set(); self.zoom = 2.0
        self.pan = QPointF(); self._positions: dict[str,QPointF] = {}; self._drag_start: QPoint | None = None
        self._original: dict[str,tuple[float,float]] = {}; self._box_start: QPoint | None = None; self._box_end: QPoint | None = None
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def set_molecule(self, molecule: Molecule | None):
        self.molecule=molecule; self.selected.clear(); self.fit(); self.selectionChanged.emit(set()); self.update()

    def origin(self): return QPointF(self.width()/2, self.height()/2)+self.pan

    def fit(self):
        self.pan=QPointF(); self.zoom=2.0
        if self.molecule and self.molecule.atoms:
            b=molecule_bounds(self.molecule); nominal=max(b.width(), b.height())*19.2/median_bond_length(self.molecule)*self.molecule.scale
            if nominal>1: self.zoom=max(.45,min(4.5,min(self.width()*.58,self.height()*.58)/nominal))
        self.update()

    def paintEvent(self, event: QPaintEvent):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing); p.fillRect(self.rect(), QColor(35,39,45))
        margin=28; canvas=self.rect().adjusted(margin,margin,-margin,-margin); p.fillRect(canvas,QColor(255,255,255)); p.setClipRect(canvas)
        p.setPen(QPen(QColor(232,235,238),1))
        for x in range(canvas.left(),canvas.right(),64): p.drawLine(x,canvas.top(),x,canvas.bottom())
        for y in range(canvas.top(),canvas.bottom(),64): p.drawLine(canvas.left(),y,canvas.right(),y)
        if self.molecule: self._positions=paint_molecule(p,self.molecule,self.origin(),self.zoom,self.selected)
        if self._box_start and self._box_end:
            box=QRect(self._box_start,self._box_end).normalized(); p.setPen(QPen(QColor(0,120,215),1,Qt.PenStyle.DashLine)); p.setBrush(QColor(0,120,215,24)); p.drawRect(box)

    def _hit(self, point: QPoint) -> str | None:
        limit=max(10,10*self.zoom)
        nearest=None; distance=1e9
        for atom_id,p in self._positions.items():
            d=((p.x()-point.x())**2+(p.y()-point.y())**2)**.5
            if d<limit and d<distance: nearest,distance=atom_id,d
        return nearest

    def mousePressEvent(self,event:QMouseEvent):
        if event.button()!=Qt.MouseButton.LeftButton or not self.molecule: return
        atom_id=self._hit(event.position().toPoint())
        if atom_id:
            if event.modifiers()&Qt.KeyboardModifier.ControlModifier:
                self.selected.symmetric_difference_update({atom_id})
            elif atom_id not in self.selected: self.selected={atom_id}
            self.selectionChanged.emit(set(self.selected)); self._drag_start=event.position().toPoint()
            self._original={a.id:(a.x,a.y) for a in self.molecule.atoms if a.id in self.selected}; self.setCursor(Qt.CursorShape.ClosedHandCursor)
        else:
            if not event.modifiers()&Qt.KeyboardModifier.ControlModifier: self.selected.clear(); self.selectionChanged.emit(set())
            self._box_start=event.position().toPoint(); self._box_end=self._box_start
        self.update()

    def mouseMoveEvent(self,event:QMouseEvent):
        if not self.molecule: return
        point=event.position().toPoint()
        if self._drag_start and self._original:
            dx=(point.x()-self._drag_start.x()); dy=-(point.y()-self._drag_start.y())
            # Convert screen delta through the same molecule/view scale. RDKit coordinates use median bond ~= 1.5.
            factor=19.2/median_bond_length(self.molecule)*self.molecule.scale*self.zoom
            for atom in self.molecule.atoms:
                if atom.id in self._original:
                    ox,oy=self._original[atom.id]; atom.x=round(ox+dx/factor,4); atom.y=round(oy+dy/factor,4)
            self.coordinatesChanged.emit(); self.update()
        elif self._box_start:
            self._box_end=point; self.update()
        else: self.setCursor(Qt.CursorShape.OpenHandCursor if self._hit(point) else Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self,event:QMouseEvent):
        if not self.molecule: return
        if self._drag_start and self._original:
            after={a.id:(a.x,a.y) for a in self.molecule.atoms if a.id in self._original}; self.dragCommitted.emit(dict(self._original),after)
        elif self._box_start and self._box_end:
            box=QRect(self._box_start,self._box_end).normalized()
            self.selected={atom_id for atom_id,p in self._positions.items() if box.contains(p.toPoint())}; self.selectionChanged.emit(set(self.selected))
        self._drag_start=None; self._original={}; self._box_start=None; self._box_end=None; self.setCursor(Qt.CursorShape.ArrowCursor); self.update()

    def wheelEvent(self,event:QWheelEvent):
        factor=1.15 if event.angleDelta().y()>0 else 1/1.15; self.zoom=max(.35,min(8,self.zoom*factor)); self.update()
