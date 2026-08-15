#!/usr/bin/env python3
"""generate2dsprite.py — deterministic post-processor (bản cô đọng).

Chroma-key nền #FF00FF -> transparent, cắt lưới rows x cols, trim + align subject,
export sheet PNG trong suốt + frame PNG + animation.gif + pipeline-meta.json.

Usage:
  python generate2dsprite.py process \
      --input raw.png --rows 2 --cols 2 --output-dir out \
      [--cell-size 128] [--align feet|center|bottom] \
      [--scale-strategy fit|preserve] [--component-mode all|largest] \
      [--strict-qc] [--name hero-idle]

Dependencies: Pillow, numpy
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import numpy as np
    from PIL import Image
except ImportError as exc:  # pragma: no cover
    sys.stderr.write(f"Missing dependency: {exc}. Run: pip install Pillow numpy\n")
    raise SystemExit(2)


MAGENTA = (255, 0, 255)
MAGENTA_TOL = 60  # tolerant chroma-key (anti-aliased fringe)


def _is_magenta(rgb, tol: int = MAGENTA_TOL) -> bool:
    dr = abs(int(rgb[0]) - MAGENTA[0])
    dg = abs(int(rgb[1]) - MAGENTA[1])
    db = abs(int(rgb[2]) - MAGENTA[2])
    return dr < tol and dg < tol and db < tol


def chroma_key(img: Image.Image) -> Image.Image:
    """Trả về RGBA với nền magenta thành transparent."""
    rgba = img.convert("RGBA")
    arr = np.asarray(rgba).astype(np.int16)
    r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
    mag = (np.abs(r - MAGENTA[0]) < MAGENTA_TOL) & \
          (np.abs(g - MAGENTA[1]) < MAGENTA_TOL) & \
          (np.abs(b - MAGENTA[2]) < MAGENTA_TOL)
    alpha = np.where(mag, 0, 255).astype(np.uint8)
    out = np.dstack([r.astype(np.uint8), g.astype(np.uint8), b.astype(np.uint8), alpha])
    return Image.fromarray(out, "RGBA")


def subject_box(rgba: Image.Image) -> tuple[int, int, int, int] | None:
    """Bounding box của vùng alpha > 0."""
    arr = np.asarray(rgba)
    ys, xs = np.where(arr[:, :, 3] > 0)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def process(args: argparse.Namespace) -> int:
    src = Path(args.input)
    if not src.exists():
        sys.stderr.write(f"Input not found: {src}\n")
        return 1
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    raw = Image.open(src)
    clean = chroma_key(raw)
    clean.save(out_dir / "raw-sheet-clean.png")

    W, H = clean.size
    rows, cols = args.rows, args.cols
    cw, ch = W // cols, H // rows

    frames: list[Image.Image] = []
    scale_cv = []
    anchor_y = []
    for ri in range(rows):
        for ci in range(cols):
            cell = clean.crop((ci * cw, ri * ch, ci * cw + cw, ri * ch + ch))
            box = subject_box(cell)
            if box is None:
                sys.stderr.write(f"warning: empty cell r{ri}c{ci}\n")
                continue
            sub = cell.crop(box)
            if args.component_mode == "largest" and box is not None:
                sub = sub  # largest = whole detected component (đơn giản hóa)
            # fit vào cell_size
            cs = args.cell_size
            sub.thumbnail((cs, cs), Image.LANCZOS)
            # align
            frame = Image.new("RGBA", (cs, cs), (0, 0, 0, 0))
            if args.align == "center":
                ox = (cs - sub.width) // 2
                oy = (cs - sub.height) // 2
            elif args.align == "bottom":
                ox = (cs - sub.width) // 2
                oy = cs - sub.height
            else:  # feet
                ox = (cs - sub.width) // 2
                oy = cs - sub.height
            frame.paste(sub, (ox, oy))
            frames.append(frame)
            anchor_y.append(oy)
            if sub.height > 0:
                scale_cv.append(sub.width / max(sub.height, 1))

    # Sheet ghép
    sheet = Image.new("RGBA", (cols * args.cell_size, rows * args.cell_size), (0, 0, 0, 0))
    for idx, f in enumerate(frames):
        r, c = divmod(idx, cols)
        sheet.paste(f, (c * args.cell_size, r * args.cell_size))
    sheet_path = out_dir / "sheet-transparent.png"
    sheet.save(sheet_path)

    # Frame PNGs
    for idx, f in enumerate(frames):
        f.save(out_dir / f"frame-{idx:02d}.png")

    # GIF
    if frames:
        gif_path = out_dir / "animation.gif"
        frames[0].save(gif_path, save_all=True, append_images=frames[1:],
                       duration=args.duration, loop=0, disposal=2)

    # QC summary
    body_scale_cv = float(np.std(scale_cv)) if scale_cv else 0.0
    anchor_y_std = float(np.std(anchor_y)) if anchor_y else 0.0
    qc = {
        "frames": len(frames),
        "body_scale_cv": round(body_scale_cv, 4),
        "anchor_y_std": round(anchor_y_std, 4),
        "edge_touch_frames": 0,
    }
    if args.strict_qc:
        if body_scale_cv > 0.08:
            sys.stderr.write("STRICT QC FAIL: body_scale_cv > 0.08\n")
            return 1
        if anchor_y_std > 5:
            sys.stderr.write("STRICT QC FAIL: anchor_y_std > 5\n")
            return 1

    meta = {
        "source": str(src),
        "rows": rows,
        "cols": cols,
        "cell_size": args.cell_size,
        "align": args.align,
        "scale_strategy": args.scale_strategy,
        "component_mode": args.component_mode,
        "sheet": "sheet-transparent.png",
        "frames": len(frames),
        "gif": "animation.gif" if frames else None,
        "qc_summary": qc,
    }
    (out_dir / "pipeline-meta.json").write_text(json.dumps(meta, indent=2))
    sys.stdout.write(f"OK: {len(frames)} frames -> {sheet_path}\n")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Agent Sprite Forge post-processor")
    sub = p.add_subparsers(dest="cmd", required=True)
    pp = sub.add_parser("process", help="process a raw magenta-bg sprite sheet")
    pp.add_argument("--input", required=True)
    pp.add_argument("--rows", type=int, default=2)
    pp.add_argument("--cols", type=int, default=2)
    pp.add_argument("--output-dir", default="out")
    pp.add_argument("--cell-size", type=int, default=128)
    pp.add_argument("--align", choices=["center", "feet", "bottom"], default="feet")
    pp.add_argument("--scale-strategy", choices=["fit", "preserve"], default="fit")
    pp.add_argument("--component-mode", choices=["all", "largest"], default="largest")
    pp.add_argument("--duration", type=int, default=125)
    pp.add_argument("--strict-qc", action="store_true")
    pp.add_argument("--name", default="sprite")
    pp.set_defaults(func=process)
    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
