from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
if module_directory := os.environ.get("CHEMANIM_CORE_MODULE_DIR"):
    sys.path.insert(0, module_directory)
_DLL_HANDLES = []
for directory in (ROOT / ".deps" / "rdkit" / "Library" / "bin",):
    if directory.exists():
        _DLL_HANDLES.append(os.add_dll_directory(str(directory)))

try:
    import chemanim_core as _native
    CoreSession = _native.CoreSession
    BUILD_COMMIT = _native.BUILD_COMMIT
    DOCUMENT_VERSION = _native.DOCUMENT_VERSION
    try:
        source_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        source_commit = ""
    if source_commit and BUILD_COMMIT not in {"", "unknown", source_commit}:
        raise RuntimeError(
            "chemanim_core.pyd 与当前源码提交不一致："
            f"Core={BUILD_COMMIT[:12]}，源码={source_commit[:12]}。"
            "请先运行 .\\build.ps1 -Configuration Release。"
        )
except ImportError as error:
    raise RuntimeError("共享 C++ Core 尚未构建，请先运行 .\\build.ps1。") from error
finally:
    # RDKit's conda bin directory also contains Qt DLLs.  Keeping it in the
    # process search path can make a later PyQt6 import pick up a different Qt
    # ABI.  The native dependencies are already loaded with the module, so the
    # temporary search handles must be closed immediately.
    for handle in _DLL_HANDLES:
        handle.close()
    _DLL_HANDLES.clear()

__all__ = ["CoreSession", "ROOT", "BUILD_COMMIT", "DOCUMENT_VERSION"]
