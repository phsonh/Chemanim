from __future__ import annotations

import math

from PyQt6.QtCore import QByteArray, QPoint, QPointF, QRect, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QMouseEvent, QPainter, QPaintEvent, QPen, QWheelEvent
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QWidget

from .depiction import AcsDepiction, render_acs1996
from .model import Molecule


class StructureCanvas(QWidget):
    selectionChanged = pyqtSignal(object)
    coordinatesChanged = pyqtSignal()
    dragCommitted = pyqtSignal(object, object)

    def __init__(self, parent=None):
        super().__init__(parent); self.setMinimumSize(620, 420); self.setMouseTracking(True); self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.molecule: Molecule | None = None; self.selected: set[str] = set(); self.zoom = 3.0; self.pan = QPointF()
        self._depiction: AcsDepiction | None = None; self._positions: dict[str,QPointF] = {}
        self._drag_start: QPoint | None = None; self._original: dict[str,tuple[float,float]] = {}
        self._box_start: QPoint | None = None; self._box_end: QPoint | None = None

    def set_molecule(self, molecule: Molecule | None):
        self.molecule=molecule; self.selected.clear(); self.invalidate(); self.fit(); self.selectionChanged.emit(set()); self.update()

    def invalidate(self):
        self._depiction = render_acs1996(self.molecule) if self.molecule else None

    def _canvas_rect(self): return self.rect().adjusted(28,28,-28,-28)
    def _svg_rect(self):
        if not self._depiction: return QRectF()
        center=QPointF(self.width()/2,self.height()/2)+self.pan
        size=QPointF(self._depiction.width*self.zoom,self._depiction.height*self.zoom)
        return QRectF(center.x()-size.x()/2,center.y()-size.y()/2,size.x(),size.y())

    def fit(self):
        self.pan=QPointF()
        if self.molecule:
            self.invalidate()
            if self._depiction:
                canvas=self._canvas_rect(); self.zoom=max(.5,min(12,min(canvas.width()*.62/self._depiction.width,canvas.height()*.62/self._depiction.height)))
        self.update()

    def paintEvent(self, event: QPaintEvent):
        painter=QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing); painter.fillRect(self.rect(),QColor(35,39,45))
        canvas=self._canvas_rect(); painter.fillRect(canvas,QColor(255,255,255)); painter.setClipRect(canvas)
        painter.setPen(QPen(QColor(237,239,241),1))
        for x in range(canvas.left(),canvas.right(),64): painter.drawLine(x,canvas.top(),x,canvas.bottom())
        for y in range(canvas.top(),canvas.bottom(),64): painter.drawLine(canvas.left(),y,canvas.right(),y)
        self._positions={}
        if self._depiction:
            target=self._svg_rect(); QSvgRenderer(QByteArray(self._depiction.svg.encode("utf-8"))).render(painter,target)
            self._positions={atom_id:target.topLeft()+QPointF(x*self.zoom,y*self.zoom) for atom_id,(x,y) in self._depiction.atom_points.items()}
        painter.setBrush(QColor(0,120,215,38)); painter.setPen(QPen(QColor(0,120,215),2))
        for atom_id in self.selected:
            if atom_id in self._positions: painter.drawEllipse(self._positions[atom_id],9,9)
        if self._box_start and self._box_end:
            box=QRect(self._box_start,self._box_end).normalized(); painter.setPen(QPen(QColor(0,120,215),1,Qt.PenStyle.DashLine)); painter.setBrush(QColor(0,120,215,24)); painter.drawRect(box)

    def _hit(self, point: QPoint) -> str | None:
        nearest=None; distance=1e9
        for atom_id,p in self._positions.items():
            d=math.hypot(p.x()-point.x(),p.y()-point.y())
            if d<13 and d<distance: nearest,distance=atom_id,d
        return nearest

    def _pixels_per_model_unit(self) -> float:
        if not self.molecule or not self._depiction: return self.zoom
        atoms={a.id:a for a in self.molecule.atoms}; ratios=[]
        for bond in self.molecule.bonds:
            if bond.a in atoms and bond.b in atoms and bond.a in self._depiction.atom_points and bond.b in self._depiction.atom_points:
                a,b=atoms[bond.a],atoms[bond.b]; model=math.hypot(a.x-b.x,a.y-b.y)
                pa,pb=self._depiction.atom_points[bond.a],self._depiction.atom_points[bond.b]; drawn=math.hypot(pa[0]-pb[0],pa[1]-pb[1])
                if model>.001: ratios.append(drawn/model)
        return (sum(ratios)/len(ratios) if ratios else 1.0)*self.zoom

    def mousePressEvent(self,event:QMouseEvent):
        if event.button()!=Qt.MouseButton.LeftButton or not self.molecule: return
        atom_id=self._hit(event.position().toPoint())
        if atom_id:
            if event.modifiers()&Qt.KeyboardModifier.ControlModifier: self.selected.symmetric_difference_update({atom_id})
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
            factor=self._pixels_per_model_unit(); dx=(point.x()-self._drag_start.x())/factor; dy=-(point.y()-self._drag_start.y())/factor
            for atom in self.molecule.atoms:
                if atom.id in self._original:
                    ox,oy=self._original[atom.id]; atom.x=round(ox+dx,4); atom.y=round(oy+dy,4)
            self.invalidate(); self.coordinatesChanged.emit(); self.update()
        elif self._box_start: self._box_end=point; self.update()
        else: self.setCursor(Qt.CursorShape.OpenHandCursor if self._hit(point) else Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self,event:QMouseEvent):
        if not self.molecule: return
        if self._drag_start and self._original:
            after={a.id:(a.x,a.y) for a in self.molecule.atoms if a.id in self._original}; self.dragCommitted.emit(dict(self._original),after)
        elif self._box_start and self._box_end:
            box=QRect(self._box_start,self._box_end).normalized(); self.selected={atom_id for atom_id,p in self._positions.items() if box.contains(p.toPoint())}; self.selectionChanged.emit(set(self.selected))
        self._drag_start=None; self._original={}; self._box_start=None; self._box_end=None; self.update()

    def wheelEvent(self,event:QWheelEvent):
        self.zoom=max(.4,min(18,self.zoom*(1.15 if event.angleDelta().y()>0 else 1/1.15))); self.update()
