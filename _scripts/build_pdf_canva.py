#!/usr/bin/env python3
"""Build the monthly AGHC Canva-ready PDF (77 pages) from the manifest.
White divider pages (centered bold black text) + full-bleed 16:9 image pages."""
import json, os
from PIL import Image, ImageDraw, ImageFont

REPO = "/tmp/aghc_work/report-aghc-monthly"
MANIFEST = f"{REPO}/_data/manifest-2026-07.json"
OUT = f"{REPO}/assets/luglio-2026/Report-AGHC-Luglio-2026.pdf"

W, H = 1280, 720
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]
def load_font(size):
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def wrap(draw, text, font, max_w):
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=font) <= max_w or not cur:
            cur = test
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def divider_page(text):
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)
    size = 64
    while size > 24:
        font = load_font(size)
        lines = wrap(d, text, font, int(W * 0.82))
        line_h = int(size * 1.3)
        total_h = line_h * len(lines)
        widest = max(d.textlength(l, font=font) for l in lines)
        if total_h <= int(H * 0.7) and widest <= int(W * 0.85):
            break
        size -= 4
    font = load_font(size)
    lines = wrap(d, text, font, int(W * 0.82))
    line_h = int(size * 1.3)
    total_h = line_h * len(lines)
    y = (H - total_h) // 2
    for l in lines:
        lw = d.textlength(l, font=font)
        d.text(((W - lw) / 2, y), l, font=font, fill=BLACK)
        y += line_h
    return img

def image_page(path, fit=1.0):
    canvas = Image.new("RGB", (W, H), WHITE)
    im = Image.open(path).convert("RGB")
    scale = min(W / im.width, H / im.height) * fit
    nw, nh = int(im.width * scale), int(im.height * scale)
    im = im.resize((nw, nh), Image.LANCZOS)
    canvas.paste(im, ((W - nw) // 2, (H - nh) // 2))
    return canvas

m = json.load(open(MANIFEST))
import tempfile, img2pdf
tmpdir = tempfile.mkdtemp(prefix="aghc_pdf_")
page_paths = []
idx = 0
for client in m["clients"]:
    for pg in client["pages"]:
        if pg["type"] == "divider":
            img = divider_page(pg["text"])
        else:
            # tabella budget ridotta del 25% sulla pagina (su richiesta)
            fit = 0.75 if pg.get("kind") == "budget" else 1.0
            img = image_page(pg["local_path"], fit)
        p = os.path.join(tmpdir, f"p{idx:03d}.png")
        # slides are flat-color → quantize to 256 colors for a much smaller, still-crisp PDF
        img.convert("RGB").quantize(colors=256, method=Image.MEDIANCUT, dither=Image.NONE).save(p, "PNG", optimize=True)
        page_paths.append(p)
        idx += 1

print(f"Built {len(page_paths)} pages (manifest total_pages={m['total_pages']})")
# img2pdf: lossless PNG embed, uniform 1920x1080 pages (96 dpi)
layout = img2pdf.get_layout_fun((img2pdf.px_to_pt(W, 96), img2pdf.px_to_pt(H, 96)))
with open(OUT, "wb") as f:
    f.write(img2pdf.convert(page_paths, layout_fun=layout))
print("WROTE", OUT, os.path.getsize(OUT), "bytes")
