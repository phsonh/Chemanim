from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_DLL_HANDLES = []
for directory in (ROOT / ".deps" / "rdkit" / "Library" / "bin",
                  ROOT / ".deps" / "rdkit" / "Library" / "lib"):
    if directory.exists():
        _DLL_HANDLES.append(os.add_dll_directory(str(directory)))

try:
    from chemanim_core import CoreSession
except ImportError as error:
    raise RuntimeError("共享 C++ Core 尚未构建，请先运行 .\\build.ps1。") from error

__all__ = ["CoreSession", "ROOT"]
