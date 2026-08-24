from __future__ import annotations

import math
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QFontMetricsF, QPainter, QPen, QPolygonF

from .model import Atom, Molecule


def atom_label(atom: Atom) -> str:
    if atom.hidden: return ""
    if atom.alias: return atom.alias
    if atom.element == "C" and not atom.isotope and not atom.formal_charge and not atom.radical_electrons:
        return ""
    text = (str(atom.isotope) if atom.isotope else "") + atom.element
    if atom.implicit_hydrogens:
        text += "H" + (str(atom.implicit_hydrogens) if atom.implicit_hydrogens > 1 else "")
    if atom.formal_charge:
        text += (str(abs(atom.formal_charge)) if abs(atom.formal_charge) > 1 else "") + ("+" if atom.formal_charge > 0 else "−")
    if atom.radical_electrons: text += "·"
    return text


def median_bond_length(molecule: Molecule) -> float:
    atoms = {atom.id: atom for atom in molecule.atoms}; values = []
    for bond in molecule.bonds:
        if bond.a in atoms and bond.b in atoms:
            a, b = atoms[bond.a], atoms[bond.b]
            length = math.hypot(a.x - b.x, a.y - b.y)
            if length > 1e-6: values.append(length)
    if not values: return 1.5
    values.sort(); return values[len(values) // 2]


def molecule_bounds(molecule: Molecule) -> QRectF:
    if not molecule.atoms: return QRectF(-1, -1, 2, 2)
    xs = [a.x for a in molecule.atoms]; ys = [a.y for a in molecule.atoms]
    return QRectF(min(xs), min(ys), max(max(xs)-min(xs), .1), max(max(ys)-min(ys), .1))


def paint_molecule(painter: QPainter, molecule: Molecule, origin: QPointF, zoom: float,
                   selected: set[str] | None = None) -> dict[str, QPointF]:
    selected = selected or set(); median = median_bond_length(molecule)
    unit = 19.2 / median * molecule.scale * zoom
    angle = math.radians(molecule.rotation); ca, sa = math.cos(angle), math.sin(angle)
    positions: dict[str, QPointF] = {}
    by_id = {a.id: a for a in molecule.atoms}
    for atom in molecule.atoms:
        x, y = atom.x * unit, atom.y * unit
        positions[atom.id] = origin + QPointF(x * ca - y * sa, -(x * sa + y * ca))

    font = QFont("Arial"); font.setPointSizeF(10.0 * zoom)
    painter.setFont(font); metrics = QFontMetricsF(font); labels: dict[str, QRectF] = {}
    for atom in molecule.atoms:
        text = atom_label(atom); p = positions[atom.id]
        if text:
            size = metrics.size(0, text); labels[atom.id] = QRectF(p.x()-size.width()/2, p.y()-size.height()/2, size.width(), size.height())
        else: labels[atom.id] = QRectF(p, p)

    color = QColor(22, 22, 22); width = max(.8, .8 * zoom); gap = 1.5 * zoom
    pen = QPen(color, width); pen.setCapStyle(Qt.PenCapStyle.RoundCap); painter.setPen(pen); painter.setBrush(color)
    double_gap = 19.2 * molecule.scale * zoom * .18

    def clipped(start: QPointF, end: QPointF, box: QRectF) -> QPointF:
        if box.width() <= 0: return end
        dx, dy = end.x()-start.x(), end.y()-start.y(); length = math.hypot(dx, dy)
        if length < .001: return end
        dx /= length; dy /= length
        tx = (box.width()/2 + gap) / abs(dx) if abs(dx) > 1e-5 else 1e9
        ty = (box.height()/2 + gap) / abs(dy) if abs(dy) > 1e-5 else 1e9
        distance = min(tx, ty); return QPointF(end.x()-dx*distance, end.y()-dy*distance)

    def line(a: QPointF, b: QPointF): painter.drawLine(a, b)
    for bond in molecule.bonds:
        if not bond.visible or bond.a not in positions or bond.b not in positions: continue
        a = clipped(positions[bond.b], positions[bond.a], labels[bond.a])
        b = clipped(positions[bond.a], positions[bond.b], labels[bond.b])
        dx, dy = b.x()-a.x(), b.y()-a.y(); length = math.hypot(dx, dy)
        if length < .01: continue
        nx, ny = -dy/length, dx/length
        if bond.stereo == "wedge":
            w = 5 * zoom; painter.drawPolygon(QPolygonF([a, QPointF(b.x()+nx*w,b.y()+ny*w), QPointF(b.x()-nx*w,b.y()-ny*w)]))
        elif bond.stereo == "dash":
            for i in range(7):
                t=(i+1)/8; c=a+(b-a)*t; w=t*5*zoom; line(QPointF(c.x()-nx*w,c.y()-ny*w), QPointF(c.x()+nx*w,c.y()+ny*w))
        elif bond.order >= 2.8:
            line(a,b); off=double_gap*.55; o=QPointF(nx*off,ny*off); line(a+o,b+o); line(a-o,b-o)
        elif bond.order >= 1.8:
            off=double_gap*.35; o=QPointF(nx*off,ny*off); line(a+o,b+o); line(a-o,b-o)
        else: line(a,b)

    painter.setPen(color)
    for atom in molecule.atoms:
        text=atom_label(atom)
        if text: painter.drawText(labels[atom.id], 0x0084, text)
    for atom_id in selected:
        if atom_id in positions:
            painter.setPen(QPen(QColor(0,120,215), max(1.2,1.2*zoom))); painter.setBrush(QColor(0,120,215,35))
            painter.drawEllipse(positions[atom_id], 8*zoom, 8*zoom)
    return positions
