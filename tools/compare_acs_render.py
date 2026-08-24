from __future__ import annotations

import argparse
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageStat


def main() -> int:
    parser=argparse.ArgumentParser(description="比较 RDKit golden 与 C++ SVG 合成结果")
    parser.add_argument("reference",type=Path); parser.add_argument("actual",type=Path); parser.add_argument("output",type=Path)
    parser.add_argument("--sheet",type=Path,help="额外输出 reference / C++ / amplified diff 并排图")
    args=parser.parse_args(); reference=Image.open(args.reference).convert("RGB"); actual=Image.open(args.actual).convert("RGB")
    if reference.size!=actual.size: raise SystemExit(f"尺寸不同: {reference.size} != {actual.size}")
    difference=ImageChops.difference(reference,actual); stat=ImageStat.Stat(difference)
    rms=(sum(value*value for value in stat.rms)/3)**.5
    # Black means identical. Differences are amplified to remain visible in a 1920x1080 review image.
    amplified=difference.point(lambda value:min(255,value*5)); args.output.parent.mkdir(parents=True,exist_ok=True); amplified.save(args.output)
    if args.sheet:
        panels=[]
        for source in (reference,actual,amplified):
            panel=source.copy(); panel.thumbnail((640,360),Image.Resampling.LANCZOS); panels.append(panel)
        sheet=Image.new("RGB",(1920,400),"#20242a"); draw=ImageDraw.Draw(sheet)
        for index,(panel,label) in enumerate(zip(panels,("RDKit ACS1996 reference","C++ SVG composition","difference x5"))):
            x=index*640+(640-panel.width)//2; sheet.paste(panel,(x,36)); draw.text((index*640+12,10),label,fill="white")
        args.sheet.parent.mkdir(parents=True,exist_ok=True); sheet.save(args.sheet)
    print(f"RMS pixel difference: {rms:.4f}")
    return 0


if __name__=="__main__": raise SystemExit(main())
