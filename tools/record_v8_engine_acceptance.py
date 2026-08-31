from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys

from PIL import Image, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from chemanim2d.core import BUILD_COMMIT, DOCUMENT_VERSION, CoreSession


def main() -> None:
    project_path = ROOT / "mod" / "visual_events" / "visual_events.cmm"
    lua_path = ROOT / "mod" / "visual_events" / "main.lua"
    executable = ROOT / "build" / "release" / "chemanim.exe"
    output = ROOT / "media" / "v8_engine_acceptance"
    output.mkdir(parents=True, exist_ok=True)

    session = CoreSession()
    session.load(str(project_path))
    generated = session.generate_lua()
    if generated != lua_path.read_text(encoding="utf-8"):
        raise RuntimeError("visual_events.cmm 与提交的 main.lua 不一致")
    scene = session.project()["scene"]
    session.set_viewport(scene["width"], scene["height"], 2.0, 0.0, 0.0)

    comparisons: dict[str, object] = {}
    for frame in (0, 30, 52, 75, 120):
        run = subprocess.run(
            [str(executable), "visual_events", "--frame", str(frame), "--no-open"],
            cwd=ROOT, capture_output=True, text=True, timeout=120,
        )
        if run.returncode:
            raise RuntimeError(run.stdout + "\n" + run.stderr)
        engine_source = ROOT / "media" / "visual_events" / f"visual_events_frame_{frame}.png"
        engine_path = output / f"engine-{frame:03d}.png"
        shutil.copy2(engine_source, engine_path)

        drawing = session.depict_at(frame, True)
        core_path = output / f"core-{frame:03d}.png"
        Image.frombytes(
            "RGBA", (drawing["width"], drawing["height"]), bytes(drawing["rgba"])
        ).save(core_path)
        core_image = Image.open(core_path).convert("RGBA")
        engine_image = Image.open(engine_path).convert("RGBA")
        difference = ImageChops.difference(core_image, engine_image)
        difference_path = output / f"difference-{frame:03d}.png"
        difference.save(difference_path)
        statistics = ImageStat.Stat(difference)
        comparisons[str(frame)] = {
            "bbox": difference.getbbox(),
            "mean": statistics.mean,
            "rms": statistics.rms,
            "max_rms": max(statistics.rms),
            "core": core_path.name,
            "engine": engine_path.name,
            "difference": difference_path.name,
        }

    before = set((ROOT / "media" / "visual_events").glob("visual_events_*.mp4"))
    run = subprocess.run(
        [str(executable), "visual_events", "--no-open"],
        cwd=ROOT, capture_output=True, text=True, timeout=240,
    )
    if run.returncode:
        raise RuntimeError(run.stdout + "\n" + run.stderr)
    created = sorted(
        set((ROOT / "media" / "visual_events").glob("visual_events_*.mp4")) - before,
        key=lambda path: path.stat().st_mtime,
    )
    if not created:
        raise RuntimeError("最终引擎没有生成 visual_events MP4")
    mp4 = output / "visual_events-v8.mp4"
    shutil.copy2(created[-1], mp4)

    report = {
        "core": BUILD_COMMIT,
        "document_version": DOCUMENT_VERSION,
        "project": str(project_path.relative_to(ROOT)),
        "generated_lua_matches": True,
        "frames": comparisons,
        "mp4": mp4.name,
    }
    (output / "acceptance.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
