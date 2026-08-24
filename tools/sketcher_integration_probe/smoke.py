from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

from PyQt6 import sip
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module-dir", type=Path, required=True)
    parser.add_argument("--screenshot", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    dll_handles = []
    for directory in (
        root / ".deps" / "sketcher-build",
        root / ".deps" / "rdkit" / "Library" / "bin",
        root / ".deps" / "rdkit" / "Library" / "lib",
    ):
        dll_handles.append(os.add_dll_directory(str(directory)))
    sys.path.insert(0, str(args.module_dir.resolve()))
    import sketcher_probe

    application = QApplication(sys.argv)
    pointer = sketcher_probe.create_widget()
    widget = sip.wrapinstance(pointer, QWidget)
    info = sketcher_probe.load_and_inspect(pointer, "c1ccccc1O")
    assert info["atoms"] == 7
    assert info["conformers"] == 1
    assert len(info["positions"]) == 7

    window = QMainWindow()
    window.setWindowTitle("Chemanim / Schrödinger Sketcher ABI probe")
    window.setCentralWidget(widget)
    window.resize(960, 640)
    window.show()
    args.screenshot.parent.mkdir(parents=True, exist_ok=True)
    QTimer.singleShot(750, lambda: (window.grab().save(str(args.screenshot)), window.close()))
    result = application.exec()
    print(info)
    print(args.screenshot.resolve())
    return result


if __name__ == "__main__":
    raise SystemExit(main())
