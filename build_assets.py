"""Genera bg/*.webp, bg/list.js, logo.png y fonts/ desde la carpeta de recursos.
Uso: python build_assets.py  (volver a correr al agregar un Anverso nuevo)"""
import glob, json, os, shutil
from PIL import Image

SRC = r"G:\Mi unidad\Medaunbrauni\MEDAUNBRAUNI SITIO WEB\Landing Page"
os.makedirs("bg", exist_ok=True)
os.makedirs("fonts", exist_ok=True)


def lum(c):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = c
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def palette(im):
    """Panel = color claro dominante, acento = el color de la paleta con más contraste
    y algo de saturación (legibilidad AA >= 4.5)."""
    q = im.resize((200, 114)).quantize(10, method=Image.Quantize.MEDIANCUT)
    pal = q.getpalette()
    counts = sorted(q.getcolors(), reverse=True)
    colors = [(n, tuple(pal[i * 3:i * 3 + 3])) for n, i in counts]
    light = [c for n, c in colors if lum(c) > 0.25] or [max((c for _, c in colors), key=lum)]
    panel = light[0]
    sat = lambda c: max(c) - min(c)
    ok = [c for _, c in colors if contrast(c, panel) >= 4.5]
    accent = max(ok, key=sat) if ok else min((c for _, c in colors), key=lum)
    if contrast(accent, panel) < 4.5:  # ponytail: fallback a tono oscurecido del acento
        accent = tuple(int(v * 0.35) for v in accent)
    return panel, accent


hexc = lambda c: "#%02x%02x%02x" % c
items = []
for f in sorted(glob.glob(os.path.join(SRC, "Anverso*.png"))):
    name = os.path.splitext(os.path.basename(f))[0].lower() + ".webp"
    im = Image.open(f).convert("RGB")
    panel, accent = palette(im)
    im.thumbnail((2560, 2560), Image.Resampling.LANCZOS)
    im.save(os.path.join("bg", name), "WEBP", quality=78, method=6)
    items.append({"src": "bg/" + name, "panel": hexc(panel), "accent": hexc(accent)})
    print(name, hexc(panel), hexc(accent), "contraste %.1f" % contrast(panel, accent))

with open("bg/list.js", "w") as fh:
    fh.write("const BGS = " + json.dumps(items, indent=1) + ";\n")

logo = Image.open(os.path.join(SRC, "Logo_Medaunbrauni_ (2).png")).convert("RGBA")
logo = logo.crop(logo.getbbox())
logo.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
logo.save("logo.png", optimize=True)

shutil.copy(os.path.join(SRC, "MEDAUNBRAUNI (1).otf"), "fonts/medaunbrauni.otf")
shutil.copy(os.path.join(SRC, "MEDAUNBRAUNI-Bold (1).otf"), "fonts/medaunbrauni-bold.otf")

# Favicon: logo compacto dentro de un círculo mostaza
MOSTAZA = (220, 168, 46, 255)  # el tono del panel en Anverso1
N = 512
fav = Image.new("RGBA", (N * 4, N * 4))  # se dibuja a 4x y se reduce para bordes suaves
from PIL import ImageDraw
ImageDraw.Draw(fav).ellipse((0, 0, N * 4 - 1, N * 4 - 1), fill=MOSTAZA)
mark = Image.open(os.path.join(SRC, "Logo_Medaunbrauni_COMPACTO.png")).convert("RGBA")
mark = mark.crop(mark.getbbox())
mark.thumbnail((int(N * 4 * 0.64),) * 2, Image.Resampling.LANCZOS)  # 64% cabe dentro del círculo
fav.alpha_composite(mark, ((N * 4 - mark.width) // 2, (N * 4 - mark.height) // 2))
fav = fav.resize((N, N), Image.Resampling.LANCZOS)
fav.save("favicon.png", optimize=True)
fav.save("favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
