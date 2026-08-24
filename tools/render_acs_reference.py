from __future__ import annotations

import argparse
from pathlib import Path
import sys

from PyQt6.QtCore import QByteArray, QRectF
from PyQt6.QtGui import QColor, QImage, QPainter
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QApplication

from chemanim2d.depiction import render_acs1996
from chemanim2d.model import load_project


def main() -> int:
    parser=argparse.ArgumentParser(description="输出 RDKit ACS1996 golden reference")
    parser.add_argument("project",type=Path); parser.add_argument("output",type=Path)
    args=parser.parse_args(); application=QApplication(sys.argv)
    project=load_project(args.project)
    if not project.molecules: raise SystemExit("工程中没有分子")
    molecule=project.molecules[0]; depiction=render_acs1996(molecule); scene=project.scene
    image=QImage(scene.width,scene.height,QImage.Format.Format_ARGB32_Premultiplied); image.fill(QColor("white"))
    scale=scene.view_zoom*molecule.scale; width=depiction.width*scale; height=depiction.height*scale
    target=QRectF((scene.width-width)/2,(scene.height-height)/2,width,height)
    painter=QPainter(image); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    QSvgRenderer(QByteArray(depiction.svg.encode("utf-8"))).render(painter,target); painter.end()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    if not image.save(str(args.output)): raise SystemExit(f"无法写入 {args.output}")
    return 0


if __name__=="__main__": raise SystemExit(main())
