from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageFilter
from PyQt6.QtCore import QByteArray, QRectF
from PyQt6.QtGui import QColor, QImage, QPainter
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from chemanim2d.core import CoreSession

MOLECULES = {
    "benzene": "c1ccccc1",
    "acetaminophen": "CC(=O)NC1=CC=C(C=C1)O",
    "ibuprofen_wedge": "CC(C)Cc1ccc(cc1)[C@@H](C)C(=O)O",
    "charged_heteroatoms": "C[N+](C)(C)CC(=O)[O-]",
    "azulene": "C1=CC=C2C=CC=C2C=C1",
    "hexaphenylbenzene": "C1=CC=C(C=C1)C2=C(C(=C(C(=C2C3=CC=CC=C3)C4=CC=CC=C4)C5=CC=CC=C5)C6=CC=CC=C6)C7=CC=CC=C7",
    "phthalocyanine": "C1=CC=C2C(=C1)C3=NC4=NC(=NC5=C6C=CC=CC6=C(N5)N=C7C8=CC=CC=C8C(=N7)N=C2N3)C9=CC=CC=C94",
    "porphyrin": "C1=CC2=CC3=CC=C(N3)C=C4C=CC(=N4)C=C5C=CC(=N5)C=C1N2",
}
WIDTH, HEIGHT = 640, 480


def render_qt_svg(svg: str, path: Path) -> None:
    image = QImage(WIDTH, HEIGHT, QImage.Format.Format_RGBA8888)
    image.fill(QColor("white"))
    painter = QPainter(image)
    QSvgRenderer(QByteArray(svg.encode("utf-8"))).render(painter, QRectF(0, 0, WIDTH, HEIGHT))
    painter.end()
    image.save(str(path))


def write_nanosvg(rgba: bytes, path: Path) -> None:
    raw = Image.frombytes("RGBA", (WIDTH, HEIGHT), rgba)
    white = Image.new("RGBA", raw.size, "white")
    white.alpha_composite(raw)
    white.convert("RGB").save(path)


def ink_mask(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGB")
    gray = image.convert("L")
    return gray.point(lambda value: 255 if value < 245 else 0)


def centered_iou(reference: Path, candidate: Path) -> float:
    first, second = ink_mask(reference), ink_mask(candidate)
    first_box, second_box = first.getbbox(), second.getbbox()
    if not first_box or not second_box:
        return 0.0
    first_crop, second_crop = first.crop(first_box), second.crop(second_box)
    width, height = max(first_crop.width, second_crop.width), max(first_crop.height, second_crop.height)
    aligned_first, aligned_second = Image.new("L", (width, height)), Image.new("L", (width, height))
    aligned_first.paste(first_crop, ((width - first_crop.width) // 2, (height - first_crop.height) // 2))
    aligned_second.paste(second_crop, ((width - second_crop.width) // 2, (height - second_crop.height) // 2))
    # One-pixel tolerance accounts for the expected Cairo/Qt/NanoSVG AA difference.
    broad_first = aligned_first.filter(ImageFilter.MaxFilter(3))
    broad_second = aligned_second.filter(ImageFilter.MaxFilter(3))
    intersection = ImageChops.multiply(aligned_first, broad_second)
    reverse = ImageChops.multiply(aligned_second, broad_first)
    matched = min(sum(intersection.histogram()[1:]), sum(reverse.histogram()[1:]))
    denominator = max(sum(aligned_first.histogram()[1:]), sum(aligned_second.histogram()[1:]))
    return matched / denominator if denominator else 0.0


def display_panel(path: Path, label: str) -> Image.Image:
    image = Image.open(path).convert("RGB")
    mask = ink_mask(path); box = mask.getbbox()
    if box:
        box = (max(0, box[0] - 16), max(0, box[1] - 16), min(WIDTH, box[2] + 16), min(HEIGHT, box[3] + 16))
        crop = image.crop(box)
    else:
        crop = image
    scale = min(600 / crop.width, 420 / crop.height)
    crop = crop.resize((max(1, round(crop.width * scale)), max(1, round(crop.height * scale))),
                       Image.Resampling.LANCZOS)
    panel = Image.new("RGB", (640, 480), "white")
    panel.paste(crop, ((640 - crop.width) // 2, 44 + (420 - crop.height) // 2))
    ImageDraw.Draw(panel).text((18, 14), label, fill="black", font=ImageFont.load_default(18))
    return panel


def main() -> int:
    QApplication.instance() or QApplication([])
    output = ROOT / "media" / "correctness"
    output.mkdir(parents=True, exist_ok=True)
    rdkit_python = ROOT / ".deps" / "rdkit" / "python.exe"
    official_script = ROOT / "tools" / "official_rdkit_acs_reference.py"
    report = {"rdkit_reference": str(official_script), "molecules": {}}

    for name, smiles in MOLECULES.items():
        reference_png = output / f"{name}_official.png"
        reference_svg = output / f"{name}_official.svg"
        subprocess.run([str(rdkit_python), str(official_script), "--smiles", smiles,
                        "--png", str(reference_png), "--svg", str(reference_svg),
                        "--width", str(WIDTH), "--height", str(HEIGHT)], check=True)

        core = CoreSession(); core.import_smiles(name, smiles)
        molecule = core.project()["molecules"][0]
        center_x = (min(atom["x"] for atom in molecule["atoms"]) + max(atom["x"] for atom in molecule["atoms"])) * .5
        center_y = (min(atom["y"] for atom in molecule["atoms"]) + max(atom["y"] for atom in molecule["atoms"])) * .5
        pixels_per_unit = 14.4 / molecule["reference_bond_length"]
        core.set_viewport(WIDTH, HEIGHT, pixels_per_unit, center_x, center_y)
        svg_result = core.depict(False)
        qt_png = output / f"{name}_editor_qt.png"
        (output / f"{name}_chemanim.svg").write_text(svg_result["svg"], encoding="utf-8")
        render_qt_svg(svg_result["svg"], qt_png)
        final_result = core.depict(True)
        nano_png = output / f"{name}_final_nanosvg.png"
        write_nanosvg(final_result["rgba"], nano_png)

        gallery = Image.new("RGB", (1920, 480), "white")
        gallery.paste(display_panel(reference_png, "Official RDKit ACS1996 / Cairo"), (0, 0))
        gallery.paste(display_panel(qt_png, "Chemanim shared SVG / Qt"), (640, 0))
        gallery.paste(display_panel(nano_png, "Chemanim final / NanoSVG"), (1280, 0))
        gallery_path = output / f"{name}_comparison.png"
        gallery.save(gallery_path)
        report["molecules"][name] = {
            "smiles": smiles,
            "qt_iou": centered_iou(reference_png, qt_png),
            "nanosvg_iou": centered_iou(reference_png, nano_png),
            "comparison": str(gallery_path),
        }

    (output / "acs_comparison.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(output / "acs_comparison.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
