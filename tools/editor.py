from __future__ import annotations

import argparse
from pathlib import Path
import sys

from PyQt6.QtWidgets import QApplication

from chemanim2d.app import MainWindow, save_window_screenshot


def main() -> int:
    parser=argparse.ArgumentParser(description="Chemanim 原生二维结构式编辑器")
    parser.add_argument("document",nargs="?",type=Path)
    parser.add_argument("--screenshot",type=Path)
    args=parser.parse_args(); root=Path(__file__).resolve().parents[1]
    application=QApplication(sys.argv); application.setStyle("Fusion")
    window=MainWindow(root)
    if args.document: window.load(args.document.resolve())
    if args.screenshot: save_window_screenshot(window,args.screenshot.resolve())
    else: window.show()
    return application.exec()


if __name__=="__main__": raise SystemExit(main())
