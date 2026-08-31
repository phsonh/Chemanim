from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys

from PIL import Image, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from chemanim2d.core import CoreSession


def main() -> None:
    session = CoreSession()
    primary = session.import_smiles("主分子", "CC")
    secondary = session.import_smiles("并入分子", "O")
    session.set_active_molecule(primary)
    session.add_node("molecule_set_position", json.dumps({"target": primary, "x": -75, "y": 15}))
    session.add_node("molecule_set_rotation", json.dumps({"target": primary, "value": 18}))
    session.add_node("molecule_set_position", json.dumps({"target": secondary, "x": 85, "y": -20}))
    session.add_node("molecule_merge_gradient_structure", json.dumps({"source": secondary, "frames": 30, "easing": "linear"}))
    session.add_node("wait", json.dumps({"frames": 30}))

    raw = json.loads(session.json())
    raw["mod"] = "multi_structure_acceptance"
    session.replace_json(json.dumps(raw, ensure_ascii=False))
    mod = ROOT / "mod" / raw["mod"]
    output = ROOT / "media" / "multi_structure_acceptance"
    mod.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    session.save(str(mod / "multi_structure_acceptance.cmm"))
    session.write_mod(str(ROOT))

    scene = session.project()["scene"]
    session.set_viewport(scene["width"], scene["height"], 2.0, 0.0, 0.0)
    executable = ROOT / "build" / "release" / "chemanim.exe"
    comparisons = {}
    for frame in (0, 15, 30):
        run = subprocess.run([str(executable), raw["mod"], "--frame", str(frame), "--no-open"], cwd=ROOT, capture_output=True, text=True, timeout=120)
        if run.returncode:
            raise RuntimeError(run.stdout + "\n" + run.stderr)
        engine_source = ROOT / "media" / raw["mod"] / f'{raw["mod"]}_frame_{frame}.png'
        engine_path = output / f"engine-{frame:03d}.png"
        shutil.copy2(engine_source, engine_path)
        drawing = session.depict_at(frame, True)
        core_path = output / f"core-{frame:03d}.png"
        Image.frombytes("RGBA", (drawing["width"], drawing["height"]), bytes(drawing["rgba"])).save(core_path)
        difference = ImageChops.difference(Image.open(core_path).convert("RGBA"), Image.open(engine_path).convert("RGBA"))
        difference.save(output / f"difference-{frame:03d}.png")
        stats = ImageStat.Stat(difference)
        comparisons[str(frame)] = {"bbox": difference.getbbox(), "mean": stats.mean, "rms": stats.rms, "max_rms": max(stats.rms)}
    report = {"frames": comparisons, "lua_has_parallel_structure_tracks": session.generate_lua().count("LerpStructure(") >= 2, "saved_reopened": False}
    reopened = CoreSession();reopened.load(str(mod / "multi_structure_acceptance.cmm"))
    report["saved_reopened"] = reopened.evaluated_project(30) == session.evaluated_project(30)
    (output / "acceptance.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
