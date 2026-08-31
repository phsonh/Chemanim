from __future__ import annotations

from PyQt6.QtCore import QByteArray, QPointF, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (QColor, QImage, QKeyEvent, QKeySequence, QMouseEvent,
                         QPainter, QPainterPath, QPen, QPolygonF, QWheelEvent)
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QWidget

from .core import CoreSession


class StructureCanvas(QWidget):
    """Artboard plus editor overlays; pan/zoom are workspace-only state."""

    selectionChanged = pyqtSignal(list, list)
    transactionCommitted = pyqtSignal()
    hoverChanged = pyqtSignal(dict)
    zoomChanged = pyqtSignal(float)
    contextRequested = pyqtSignal(dict, object)
    undoRequested = pyqtSignal()
    redoRequested = pyqtSignal()
    atomTextRequested = pyqtSignal(str, str)
    manipulationChanged = pyqtSignal()

    def __init__(self, session: CoreSession, parent=None):
        super().__init__(parent)
        self.session = session
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.setMinimumSize(640, 420)
        self.view_scale = 1.0
        self.pan = QPointF()
        self.final_effect = False
        self.preview_frame = 0
        self._depiction = self._svg = self._raster = self._onion_raster = None
        self._selected_atoms, self._selected_bonds = [], []
        self._hover = {"kind": "none", "id": ""}
        self._preview = {"active": False, "kind": "none"}
        self._panning = False
        self._pan_press = QPointF()
        self._pan_origin = QPointF()
        self._space_down = False
        self._gesture_active = False
        self._fit_pending = True
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._refresh_now)

    def scene(self):
        return self.session.project().get("scene", {})

    def world_to_screen(self, point: QPointF) -> QPointF:
        center = QPointF(self.width() * .5, self.height() * .5) + self.pan
        return QPointF(center.x() + point.x() * self.view_scale,
                       center.y() - point.y() * self.view_scale)

    def screen_to_world(self, point: QPointF) -> QPointF:
        center = QPointF(self.width() * .5, self.height() * .5) + self.pan
        return QPointF((point.x() - center.x()) / self.view_scale,
                       -(point.y() - center.y()) / self.view_scale)

    def artboard_rect(self) -> QRectF:
        scene = self.scene()
        width, height = scene.get("logic_width", 960), scene.get("logic_height", 540)
        top_left = self.world_to_screen(QPointF(-width * .5, height * .5))
        return QRectF(top_left.x(), top_left.y(), width * self.view_scale,
                      height * self.view_scale).normalized()

    def _scale_limits(self):
        scene = self.scene()
        short_logic = max(1.0, min(scene.get("logic_width", 960), scene.get("logic_height", 540)))
        minimum = 160.0 / short_logic
        short_screen = max(160.0, min(self.width(), self.height()))
        return minimum, max(minimum * 2.0, short_screen / 40.0)

    def fit_artboard(self):
        scene = self.scene()
        width, height = max(1, scene.get("logic_width", 960)), max(1, scene.get("logic_height", 540))
        self.view_scale = min(max(80, self.width() - 96) / width,
                              max(80, self.height() - 96) / height)
        low, high = self._scale_limits()
        self.view_scale = min(high, max(low, self.view_scale))
        self.pan = QPointF()
        self._fit_pending = False
        self.zoomChanged.emit(self.view_scale)
        self.request_refresh()

    def fit_all(self):
        project = self.session.project()
        points = []
        for molecule in project.get("molecules", []):
            for atom in molecule.get("atoms", []):
                if atom.get("alive",True):points.append(QPointF(atom["x"],atom["y"]))
        if not points:
            self.fit_artboard()
            return
        scene = self.scene()
        half_w, half_h = scene.get("logic_width", 960) * .5, scene.get("logic_height", 540) * .5
        xs = [-half_w, half_w] + [p.x() for p in points]
        ys = [-half_h, half_h] + [p.y() for p in points]
        self.view_scale = min(max(80, self.width()-96)/max(1, max(xs)-min(xs)),
                              max(80, self.height()-96)/max(1, max(ys)-min(ys)))
        low, high = self._scale_limits()
        self.view_scale = min(high, max(low, self.view_scale))
        center = QPointF((min(xs)+max(xs))*.5, (min(ys)+max(ys))*.5)
        self.pan = QPointF(-center.x()*self.view_scale, center.y()*self.view_scale)
        self.zoomChanged.emit(self.view_scale)
        self.request_refresh()

    fit = fit_artboard

    def _active_molecule(self):
        active = self.session.active_molecule
        return next((item for item in self.session.project().get("molecules", []) if item["id"] == active), None)

    def _sync_core_viewport(self):
        center=self.screen_to_world(QPointF(self.width()*.5,self.height()*.5))
        self.session.set_viewport(max(1,self.width()),max(1,self.height()),self.view_scale,center.x(),center.y())

    def request_refresh(self):
        if not self._timer.isActive():
            self._timer.start(16)

    def _refresh_now(self):
        self._sync_core_viewport()
        try:
            editable=self.session.edit_target_kind in ("base_structure","structure_snapshot")
            data = self.session.depict(self.final_effect) if editable else self.session.depict_at(self.preview_frame,self.final_effect)
        except RuntimeError:
            self._depiction = self._svg = self._raster = None
            self.update()
            return
        self._depiction = data
        self._onion_raster=None
        comparison=self.session.comparison_frame
        if not self.final_effect and comparison>=0:
            try:
                onion=self.session.depict_at(comparison,False);renderer=QSvgRenderer(QByteArray(onion["svg"].encode("utf-8")));image=QImage(max(1,self.width()),max(1,self.height()),QImage.Format.Format_ARGB32_Premultiplied);image.fill(Qt.GlobalColor.transparent);overlay=QPainter(image);renderer.render(overlay,QRectF(image.rect()));overlay.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn);overlay.fillRect(image.rect(),QColor(55,145,225,92));overlay.end();self._onion_raster=image
            except RuntimeError:pass
        if self.final_effect:
            image = QImage(data["rgba"], data["width"], data["height"], QImage.Format.Format_RGBA8888)
            self._raster, self._svg = image.copy(), None
        else:
            self._svg = QSvgRenderer(QByteArray(data["svg"].encode("utf-8")))
            self._raster = None
        self.update()

    def set_preview_frame(self, frame: int):
        self.preview_frame = max(0, int(frame))
        self.session.preview_timeline(self.preview_frame)
        self.request_refresh()

    def show_edit_frame(self, frame: int):
        """Update the displayed frame without changing Core's edit target."""
        self.preview_frame=max(0,int(frame))
        self.request_refresh()

    def set_final_effect(self, enabled: bool):
        self.final_effect = enabled
        self.request_refresh()

    @property
    def selected_atoms(self):
        return list(self._selected_atoms)

    @property
    def selected_bonds(self):
        return list(self._selected_bonds)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._fit_pending:
            QTimer.singleShot(0, self.fit_artboard)
        else:
            low, high = self._scale_limits()
            self.view_scale = min(high, max(low, self.view_scale))
            self.request_refresh()

    @staticmethod
    def _rgba(value):
        try:
            value = (value or "FFFFFFFF").lstrip("#")
            if len(value) == 6:
                value += "FF"
            return QColor(int(value[0:2],16), int(value[2:4],16), int(value[4:6],16), int(value[6:8],16))
        except (ValueError, IndexError):
            return QColor("white")

    def _draw_grid(self, painter, artboard):
        spacing = 50.0
        while spacing*self.view_scale < 28:
            spacing *= 2
        while spacing*self.view_scale > 90:
            spacing *= .5
        painter.save()
        painter.setClipRect(artboard)
        painter.setPen(QPen(QColor(95,110,125,38),1))
        left = self.screen_to_world(artboard.topLeft()).x()
        right = self.screen_to_world(artboard.topRight()).x()
        bottom = self.screen_to_world(artboard.bottomLeft()).y()
        top = self.screen_to_world(artboard.topLeft()).y()
        x = int(left//spacing)*spacing
        while x <= right:
            painter.drawLine(self.world_to_screen(QPointF(x,bottom)), self.world_to_screen(QPointF(x,top)))
            x += spacing
        y = int(bottom//spacing)*spacing
        while y <= top:
            painter.drawLine(self.world_to_screen(QPointF(left,y)), self.world_to_screen(QPointF(right,y)))
            y += spacing
        painter.restore()

    @staticmethod
    def _cubic(p0, p1, p2, p3, t):
        u=1.0-t
        return QPointF(u**3*p0.x()+3*u*u*t*p1.x()+3*u*t*t*p2.x()+t**3*p3.x(),
                       u**3*p0.y()+3*u*u*t*p1.y()+3*u*t*t*p2.y()+t**3*p3.y())

    def _arrow_shape(self,p0,p1,p2,p3,progress,head_length,head_width):
        progress=max(0.0,min(1.0,progress));path=QPainterPath(p0)
        if progress<=0:return path,QPolygonF()
        samples=192;points=[self._cubic(p0,p1,p2,p3,index/samples) for index in range(samples+1)];cumulative=[0.0]
        for index in range(1,len(points)):
            delta=points[index]-points[index-1];cumulative.append(cumulative[-1]+(delta.x()**2+delta.y()**2)**.5)
        def through_length(target):
            result=[points[0]]
            for index in range(1,len(points)):
                if cumulative[index]<=target:result.append(points[index]);continue
                segment=cumulative[index]-cumulative[index-1]
                if target>cumulative[index-1] and segment>0:
                    local=(target-cumulative[index-1])/segment;a,b=points[index-1],points[index]
                    result.append(QPointF(a.x()+(b.x()-a.x())*local,a.y()+(b.y()-a.y())*local))
                break
            return result
        target_length=cumulative[-1]*progress;tip_points=through_length(target_length)
        if len(tip_points)<2:return path,QPolygonF()
        tip=tip_points[-1];shaft_points=through_length(max(0.0,target_length-head_length));base=shaft_points[-1]
        for point in shaft_points[1:]:path.lineTo(point)
        delta=tip-base;axis_length=max(.001,(delta.x()**2+delta.y()**2)**.5);width_scale=min(1.0,axis_length/max(1.0,head_length))
        normal=QPointF(-delta.y()/axis_length*head_width*width_scale*.5,delta.x()/axis_length*head_width*width_scale*.5)
        return path,QPolygonF([tip,base+normal,base-normal])

    def _draw_arrows(self, painter,frame=None,onion=False):
        edited=next((node for node in self.session.project().get("nodes",[]) if node["id"]==self.session.edit_target_id),None)
        edited_curve=(edited or {}).get("type")=="arrow_set_curve";edited_target=(edited or {}).get("params",{}).get("target","")
        for arrow_id,arrow in self.session.evaluated_arrows(self.preview_frame if frame is None else frame).items():
            curve_context=edited_curve and edited_target==arrow_id and frame is None and not self.final_effect
            progress=1.0 if curve_context else arrow["progress"]
            if not arrow["exists"] or not arrow["visible"] or (arrow["alpha"]<=0 and not curve_context) or progress<=0:
                continue
            pos = arrow["position"]
            def point(name):
                value = arrow[name]
                return self.world_to_screen(QPointF(value["x"]+pos["x"], value["y"]+pos["y"]))
            stroke=max(.7,arrow["width"]*self.view_scale)
            path,head=self._arrow_shape(point("start"),point("control1"),point("control2"),point("end"),progress,stroke*(20.0/3.0),stroke*5.0)
            color = QColor(55,145,225,92) if onion else QColor(*(max(0,min(255,round(arrow[key]))) for key in ("r","g","b","alpha")))
            if curve_context and color.alpha()==0:color=QColor(44,145,235,150)
            painter.setPen(QPen(color,stroke, Qt.PenStyle.SolidLine,
                                Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            painter.setBrush(Qt.BrushStyle.NoBrush);painter.drawPath(path);painter.setPen(Qt.PenStyle.NoPen);painter.setBrush(color);painter.drawPolygon(head)

    def _draw_direct_controls(self,painter):
        controls={item["id"]:self.world_to_screen(QPointF(item["position"]["x"],item["position"]["y"])) for item in self.session.direct_controls()}
        if not controls:return
        painter.save();painter.setBrush(Qt.BrushStyle.NoBrush);painter.setPen(QPen(QColor(76,158,231,145),1.4,Qt.PenStyle.DashLine))
        if "anchor" in controls and self._depiction:
            painter.setPen(QPen(QColor(44,145,235,125),2.2,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap))
            for bond in self._depiction.get("bonds",[]):
                for first,second in self._bond_highlight_segments(bond):painter.drawLine(first,second)
        if "p0" in controls and "c1" in controls:painter.drawLine(controls["p0"],controls["c1"])
        if "c2" in controls and "p3" in controls:painter.drawLine(controls["c2"],controls["p3"])
        for key,point in controls.items():
            endpoint=key in ("p0","p3");painter.setPen(QPen(QColor(44,145,235),2));painter.setBrush(QColor(242,248,255) if endpoint else QColor(44,145,235));radius=6 if endpoint else 5;painter.drawEllipse(point,radius,radius)
        painter.restore()

    def _draw_transform_target_outline(self,painter):
        """Keep a transform target editable even when its visual alpha/progress is zero."""
        if self.session.comparison_frame < 0:return
        project=self.session.project();node=next((item for item in project.get("nodes",[]) if item["id"]==self.session.edit_target_id),None)
        definition=next((item for item in self.session.node_registry() if node and item["type"]==node["type"]),{})
        target_kind=definition.get("target_kind","");target=(node or {}).get("params",{}).get("target","")
        painter.save();painter.setBrush(Qt.BrushStyle.NoBrush);painter.setPen(QPen(QColor(38,157,235,175),1.35,Qt.PenStyle.DashLine,Qt.PenCapStyle.RoundCap,Qt.PenJoinStyle.RoundJoin))
        if target_kind=="molecule" and self._depiction:
            for bond in self._depiction.get("bonds",[]):
                for first,second in self._bond_highlight_segments(bond):painter.drawLine(first,second)
            for atom in self._depiction.get("atoms",[]):
                center=QPointF(atom["center"]["x"],atom["center"]["y"]);painter.drawEllipse(center,4.5,4.5)
        elif target_kind=="arrow":
            arrow=self.session.evaluated_arrows(self.preview_frame).get(target)
            if arrow and arrow.get("exists"):
                position=arrow["position"]
                def point(key):
                    value=arrow[key];return self.world_to_screen(QPointF(value["x"]+position["x"],value["y"]+position["y"]))
                path=QPainterPath(point("start"));path.cubicTo(point("control1"),point("control2"),point("end"));painter.drawPath(path)
        painter.restore()

    @staticmethod
    def _bond_highlight_segments(bond):
        """Return the visible strokes, not merely the bond centre line."""
        first = QPointF(bond["first"]["x"], bond["first"]["y"])
        second = QPointF(bond["second"]["x"], bond["second"]["y"])
        dx, dy = second.x()-first.x(), second.y()-first.y()
        length = max(1e-9, (dx*dx+dy*dy)**.5)
        tangent = QPointF(dx/length, dy/length)
        normal = QPointF(-dy/length, dx/length)
        spacing = float(bond.get("line_spacing", 0.0))
        kind = bond.get("type", "single")
        side = bond.get("secondary_line_side", "center")

        def shifted(offset, trim=0.0):
            delta = normal*offset
            inward = tangent*trim
            return first+delta+inward, second+delta-inward

        if kind == "triple":
            return [shifted(-spacing), shifted(0.0), shifted(spacing)]
        if kind != "double":
            return [shifted(0.0)]
        if side == "center":
            first_extensions=bond.get("first_extensions",(0.0,0.0))
            second_extensions=bond.get("second_extensions",(0.0,0.0))
            segments=[]
            # Core stores extension slots by model-space normal sign. Canvas Y
            # is inverted, so screen-space negative uses model-space positive.
            for index,offset in enumerate((-spacing*.5,spacing*.5)):
                model_index=1-index
                delta=normal*offset
                segments.append((first+delta+tangent*float(first_extensions[model_index]),
                                 second+delta+tangent*float(second_extensions[model_index])))
            return segments
        # Core Left is defined in model coordinates; the screen Y axis is
        # inverted, so its signed screen normal is negative.
        sign = -1.0 if side == "left" else 1.0
        return [shifted(0.0), shifted(spacing*sign, length*.16)]

    def _draw_bond_highlight(self, painter, bond):
        painter.save()
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(42,145,235,190),5,
                            Qt.PenStyle.SolidLine,Qt.PenCapStyle.FlatCap))
        for first,second in self._bond_highlight_segments(bond):
            painter.drawLine(first,second)
        painter.restore()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(43,47,53))
        artboard = self.artboard_rect()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0,0,0,55))
        painter.drawRoundedRect(artboard.adjusted(6,7,10,11),3,3)
        painter.setBrush(self._rgba(self.scene().get("background","FFFFFFFF")))
        painter.setPen(QPen(QColor(125,135,145),1))
        painter.drawRect(artboard)
        if not self.final_effect:
            self._draw_grid(painter,artboard)
        painter.save()
        if self.final_effect:
            painter.setClipRect(artboard)
        if self._onion_raster is not None:painter.drawImage(QRectF(self.rect()),self._onion_raster)
        if self._raster:
            painter.drawImage(QRectF(self.rect()),self._raster)
        elif self._svg:
            self._svg.render(painter,QRectF(self.rect()))
        comparison=self.session.comparison_frame
        if not self.final_effect and comparison>=0:self._draw_arrows(painter,comparison,True)
        self._draw_arrows(painter)
        painter.restore()
        if self.final_effect:
            return
        self._draw_transform_target_outline(painter)
        self._draw_direct_controls(painter)
        if self._depiction:
            points = {item["id"]:item["center"] for item in self._depiction.get("atoms",[])}
            bonds={item["id"]:item for item in self._depiction.get("bonds",[])}
            # ChemDraw-style blue feedback follows the pointer.  Creation
            # tools do not leave their result selected; moving away therefore
            # removes the highlight immediately.
            hover_kind,hover_id=self._hover.get("kind","none"),self._hover.get("id","")
            if hover_kind=="atom" and hover_id in points:
                point=points[hover_id]
                painter.setPen(QPen(QColor(42,145,235),2))
                painter.setBrush(QColor(42,145,235,38))
                painter.drawEllipse(QPointF(point["x"],point["y"]),10,10)
            elif hover_kind=="bond" and hover_id in bonds:
                self._draw_bond_highlight(painter,bonds[hover_id])
            painter.setPen(QPen(QColor(42,145,235),2))
            painter.setBrush(QColor(42,145,235,38))
            for atom_id in self._selected_atoms:
                if atom_id in points:
                    point=points[atom_id]
                    painter.drawEllipse(QPointF(point["x"],point["y"]),10,10)
            for bond_id in self._selected_bonds:
                if bond_id in bonds:
                    self._draw_bond_highlight(painter,bonds[bond_id])
        if self._preview.get("active"):
            kind=self._preview.get("kind","none")
            start,current=self._preview.get("start"),self._preview.get("current")
            painter.setPen(QPen(QColor(45,145,235,210),2,Qt.PenStyle.DashLine))
            painter.setBrush(QColor(45,145,235,35))
            if kind=="rectangle" and start and current:
                painter.drawRect(QRectF(QPointF(start["x"],start["y"]),QPointF(current["x"],current["y"])).normalized())
            elif kind in ("lasso","ring"):
                polygon=[QPointF(item["x"],item["y"]) for item in self._preview.get("polygon",[])]
                if polygon:
                    if kind=="ring":
                        painter.drawPolygon(QPolygonF(polygon))
                    else:
                        path=QPainterPath(polygon[0])
                        for point in polygon[1:]:
                            path.lineTo(point)
                        painter.drawPath(path)
            elif kind=="bond" and start and current:
                painter.drawLine(QPointF(start["x"],start["y"]),QPointF(current["x"],current["y"]))
            elif kind=="arrow_curve":
                points=[QPointF(item["x"],item["y"]) for item in self._preview.get("polygon",[])]
                if len(points)==4:
                    path=QPainterPath(points[0]);path.cubicTo(points[1],points[2],points[3]);painter.drawPath(path)
                    painter.setPen(QPen(QColor(230,145,45,185),1.2,Qt.PenStyle.DashLine));painter.drawLine(points[0],points[1]);painter.drawLine(points[3],points[2])
            elif kind=="adornment" and current:
                center=QPointF(current["x"],current["y"]);radius=8.0
                painter.setBrush(QColor(45,145,235,24));painter.drawEllipse(center,radius,radius)
                painter.setPen(QPen(QColor(45,145,235,230),1.8,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap))
                painter.drawLine(QPointF(center.x()-4,center.y()),QPointF(center.x()+4,center.y()))
                if self._preview.get("text")=="⊕":
                    painter.drawLine(QPointF(center.x(),center.y()-4),QPointF(center.x(),center.y()+4))
            elif kind=="text" and start and current:
                first=QPointF(start["x"],start["y"]);second=QPointF(current["x"],current["y"])
                painter.setPen(QPen(QColor(45,145,235,230),2,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap))
                painter.drawLine(first,second);painter.drawEllipse(second,4,4)

    @staticmethod
    def _mods(event):
        mods=event.modifiers()
        return bool(mods&Qt.KeyboardModifier.AltModifier),bool(mods&Qt.KeyboardModifier.ControlModifier),bool(mods&Qt.KeyboardModifier.ShiftModifier)

    def _consume(self,result):
        self._selected_atoms=list(result["selected_atoms"])
        self._selected_bonds=list(result["selected_bonds"])
        self._hover=dict(result["hover"])
        self._preview=result["preview"]
        self.selectionChanged.emit(self._selected_atoms,self._selected_bonds)
        self.hoverChanged.emit(result["hover"])
        self.update()

    def leaveEvent(self,event):
        self._hover={"kind":"none","id":""}
        self.hoverChanged.emit(self._hover)
        self.update()
        super().leaveEvent(event)

    def _begin_pan(self, position):
        self._panning=True
        self._pan_press=QPointF(position)
        self._pan_origin=QPointF(self.pan)
        self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mousePressEvent(self,event:QMouseEvent):
        if event.button()==Qt.MouseButton.MiddleButton or (event.button()==Qt.MouseButton.LeftButton and self._space_down):
            self._begin_pan(event.position());event.accept();return
        if event.button()==Qt.MouseButton.RightButton:
            self._sync_core_viewport();self.contextRequested.emit(self.session.hit_test(event.position().x(),event.position().y()),event.globalPosition().toPoint());event.accept();return
        if event.button()!=Qt.MouseButton.LeftButton:
            return
        if self.final_effect:
            event.accept();return
        self.setFocus();self._sync_core_viewport()
        alt,control,shift=self._mods(event)
        self._gesture_active=True;self._consume(self.session.pointer_down(event.position().x(),event.position().y(),alt,control,shift))

    def mouseMoveEvent(self,event:QMouseEvent):
        if self._panning:
            self.pan=self._pan_origin+(event.position()-self._pan_press)
            self.request_refresh();event.accept();return
        self._sync_core_viewport()
        alt,control,shift=self._mods(event)
        result=self.session.pointer_move(event.position().x(),event.position().y(),alt,control,shift);self._consume(result)
        if not self._gesture_active and self.session.can_direct_manipulate and result["hover"]["kind"] in ("atom","bond","molecule"):self.setCursor(Qt.CursorShape.SizeAllCursor)
        elif not self._gesture_active and result["hover"]["kind"]=="control":self.setCursor(Qt.CursorShape.CrossCursor)
        elif not self._panning:self.unsetCursor()
        if self._gesture_active:self.manipulationChanged.emit()
        self.request_refresh()

    def mouseReleaseEvent(self,event:QMouseEvent):
        if self._panning and event.button() in (Qt.MouseButton.MiddleButton,Qt.MouseButton.LeftButton):
            self._panning=False;self.unsetCursor();event.accept();return
        if event.button()!=Qt.MouseButton.LeftButton:
            return
        self._sync_core_viewport()
        alt,control,shift=self._mods(event)
        result=self.session.pointer_up(event.position().x(),event.position().y(),alt,control,shift)
        self._gesture_active=False;self._consume(result);self.request_refresh()
        if result.get("message","").startswith("atom_text|"):
            _,atom_id,side=result["message"].split("|",2);self.atomTextRequested.emit(atom_id,side)
        if result["changed"]:
            self.transactionCommitted.emit()

    def wheelEvent(self,event:QWheelEvent):
        direction=1 if event.angleDelta().y()>0 else -1
        if event.angleDelta().y() and self.session.adjust_arrow_curve_bend(direction):
            if not self._gesture_active:self.transactionCommitted.emit()
            else:self.manipulationChanged.emit()
            self.request_refresh();event.accept();return
        before=self.screen_to_world(event.position())
        factor=1.12 if event.angleDelta().y()>0 else 1/1.12
        low,high=self._scale_limits()
        new_scale=min(high,max(low,self.view_scale*factor))
        if abs(new_scale-self.view_scale)<1e-12:
            return
        self.view_scale=new_scale
        if abs(new_scale-low)<1e-12 and factor<1:
            self.pan=QPointF()
        else:
            self.pan=QPointF(event.position().x()-self.width()*.5-before.x()*new_scale,
                             event.position().y()-self.height()*.5+before.y()*new_scale)
        self.zoomChanged.emit(self.view_scale)
        self.request_refresh();event.accept()

    def keyPressEvent(self,event:QKeyEvent):
        if event.matches(QKeySequence.StandardKey.SelectAll):
            self._consume(self.session.select_all());self.request_refresh();event.accept();return
        if event.matches(QKeySequence.StandardKey.Undo):
            self.undoRequested.emit();event.accept();return
        if event.matches(QKeySequence.StandardKey.Redo) or (event.key()==Qt.Key.Key_Z and event.modifiers()==(Qt.KeyboardModifier.ControlModifier|Qt.KeyboardModifier.ShiftModifier)):
            self.redoRequested.emit();event.accept();return
        if event.key()==Qt.Key.Key_Space and not event.isAutoRepeat():
            self._space_down=True;self.setCursor(Qt.CursorShape.OpenHandCursor);event.accept();return
        if event.key() in (Qt.Key.Key_F,Qt.Key.Key_Home):
            self.fit_all() if event.modifiers()&Qt.KeyboardModifier.ShiftModifier else self.fit_artboard();return
        if event.key() in (Qt.Key.Key_Delete,Qt.Key.Key_Backspace):
            if self.session.delete_selection():
                self._selected_atoms.clear();self._selected_bonds.clear();self.selectionChanged.emit([],[])
                self.request_refresh();self.transactionCommitted.emit()
            return
        if event.key()==Qt.Key.Key_Escape:
            self.session.cancel_gesture();self._gesture_active=False;self._preview={"active":False,"kind":"none"};self.request_refresh();return
        super().keyPressEvent(event)

    def keyReleaseEvent(self,event:QKeyEvent):
        if event.key()==Qt.Key.Key_Space and not event.isAutoRepeat():
            self._space_down=False
            if not self._panning:
                self.unsetCursor()
            event.accept();return
        super().keyReleaseEvent(event)
