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


def dominant_pixels(path: Path) -> dict[str, int]:
    image = Image.open(path).convert("RGB")
    result = {"red": 0, "green": 0, "blue": 0, "orange": 0}
    for red, green, blue in image.get_flattened_data():
        if red > green + 35 and red > blue + 35:
            result["red"] += 1
        if green > red + 35 and green > blue + 20:
            result["green"] += 1
        if blue > red + 35 and blue > green + 35:
            result["blue"] += 1
        if red > blue + 35 and red > green + 35 and green > blue:
            result["orange"] += 1
    return result


def main() -> None:
    module = "color_override_acceptance"
    output = ROOT / "media" / module
    mod = ROOT / "mod" / module
    output.mkdir(parents=True, exist_ok=True)
    mod.mkdir(parents=True, exist_ok=True)

    session = CoreSession()
    molecule = session.import_smiles("colored", "c1ccccc1")
    session.add_node("molecule_set_position", json.dumps({"target": molecule, "x": -75, "y": 0}))
    session.add_node("molecule_set_scale", json.dumps({"target": molecule, "value": 1.5}))
    session.add_node("molecule_set_color", json.dumps({"target": molecule, "r": 255, "g": 0, "b": 0}))
    session.add_node("molecule_lerp_color", json.dumps({
        "target": molecule, "r": 0, "g": 200, "b": 120,
        "frames": 20, "easing": "linear",
    }))

    session.add_node("arrow_new", json.dumps({"target": "arrow1"}))
    session.add_node("arrow_set_curve", json.dumps({
        "target": "arrow1", "initialized": True,
        "x1": 20, "y1": -15, "cx1": 45, "cy1": 30,
        "cx2": 75, "cy2": 30, "x2": 105, "y2": -15,
    }))
    session.add_node("arrow_set_progress", json.dumps({"target": "arrow1", "value": 1}))
    session.add_node("arrow_set_color", json.dumps({"target": "arrow1", "r": 0, "g": 210, "b": 40}))
    session.add_node("arrow_lerp_color", json.dumps({
        "target": "arrow1", "r": 80, "g": 40, "b": 220,
        "frames": 20, "easing": "linear",
    }))
    session.add_node("wait", json.dumps({"frames": 20}))

    # Local zero alpha must not make the renderer cull objects once a global
    # alpha override is active.
    session.add_node("molecule_set_alpha", json.dumps({"target": molecule, "value": 0}))
    session.add_node("arrow_set_alpha", json.dumps({"target": "arrow1", "value": 0}))
    session.add_node("arrow_set_width", json.dumps({"target": "arrow1", "value": 9}))
    session.add_node("molecule_global_set_color", json.dumps({"r": 20, "g": 80, "b": 220}))
    session.add_node("molecule_global_set_alpha", json.dumps({"value": 180}))
    session.add_node("molecule_global_set_scale", json.dumps({"value": 2}))
    session.add_node("arrow_global_set_color", json.dumps({"r": 230, "g": 100, "b": 20}))
    session.add_node("arrow_global_set_alpha", json.dumps({"value": 180}))
    session.add_node("arrow_global_set_width", json.dumps({"value": 4}))

    raw = session.project()
    raw["mod"] = module
    session.replace_json(json.dumps(raw, ensure_ascii=False))
    project_path = mod / f"{module}.cmm"
    session.save(str(project_path))
    session.write_mod(str(ROOT))
    reopened = CoreSession()
    reopened.load(str(project_path))
    assert reopened.evaluated_project(20) == session.evaluated_project(20)

    values = {
        "molecule_mid": dict(session.evaluated_molecules(10)[molecule]),
        "arrow_mid": dict(session.evaluated_arrows(10)["arrow1"]),
        "molecule_final": dict(session.evaluated_molecules(20)[molecule]),
        "arrow_final": dict(session.evaluated_arrows(20)["arrow1"]),
    }
    assert (values["molecule_mid"]["r"], values["molecule_mid"]["g"], values["molecule_mid"]["b"]) == (128, 100, 60)
    assert (values["arrow_mid"]["r"], values["arrow_mid"]["g"], values["arrow_mid"]["b"]) == (40, 125, 130)
    assert (values["molecule_final"]["alpha"], values["molecule_final"]["r"], values["molecule_final"]["g"], values["molecule_final"]["b"]) == (180, 20, 80, 220)
    assert values["molecule_final"]["scale_x"] == values["molecule_final"]["scale_y"] == 3
    assert (values["arrow_final"]["alpha"], values["arrow_final"]["r"], values["arrow_final"]["g"], values["arrow_final"]["b"], values["arrow_final"]["width"]) == (180, 230, 100, 20, 4)

    scene = session.project()["scene"]
    session.set_viewport(scene["width"], scene["height"],
                         scene["width"] / scene["logic_width"], 0.0, 0.0)
    executable = ROOT / "build" / "release" / "chemanim.exe"
    comparison: dict[str, object] = {}
    for frame in (0, 10, 20):
        run = subprocess.run([str(executable), module, "--frame", str(frame), "--no-open"],
                             cwd=ROOT, capture_output=True, text=True, timeout=120)
        if run.returncode:
            raise RuntimeError(run.stdout + "\n" + run.stderr)
        engine_source = output / f"{module}_frame_{frame}.png"
        engine_path = output / f"engine-{frame:03d}.png"
        shutil.copy2(engine_source, engine_path)
        drawing = session.depict_at(frame, True)
        core_path = output / f"core-{frame:03d}.png"
        Image.frombytes("RGBA", (drawing["width"], drawing["height"]),
                        bytes(drawing["rgba"])).save(core_path)
        difference = ImageChops.difference(Image.open(core_path).convert("RGBA"),
                                           Image.open(engine_path).convert("RGBA"))
        difference_path = output / f"difference-{frame:03d}.png"
        difference.save(difference_path)
        statistics = ImageStat.Stat(difference)
        comparison[str(frame)] = {
            "rms": statistics.rms,
            "max_rms": max(statistics.rms),
            "dominant_pixels": dominant_pixels(engine_path),
        }

    assert comparison["0"]["dominant_pixels"]["red"] > 100
    assert comparison["0"]["dominant_pixels"]["green"] > 100
    assert comparison["20"]["dominant_pixels"]["blue"] > 100
    assert comparison["20"]["dominant_pixels"]["orange"] > 100
    report = {"values": values, "core_engine": comparison, "saved_reopened": True}
    (output / "acceptance.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
