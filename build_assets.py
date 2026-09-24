"""Genera bg/*.webp, bg/list.js, logo.png y fonts/ desde la carpeta de recursos.
Uso: python build_assets.py  (volver a correr al agregar un Anverso nuevo)"""
import colorsys, glob, json, os, shutil
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


PANEL_MIX = 0.68   # peor caso de cálculo; el panel real ondula 50-85% y el texto lleva halo del color del panel
MIN_CONTRAST = 4.5  # WCAG AA texto normal
MIN_ACCENT_LUM = 0.03  # piso para que el acento no termine en casi negro


def hls(c):
    return colorsys.rgb_to_hls(*(v / 255 for v in c))


def rgb(h, l, s):
    return tuple(round(v * 255) for v in colorsys.hls_to_rgb(h, l, s))


def mix(a, b, t):
    return tuple(round(x * t + y * (1 - t)) for x, y in zip(a, b))


def palette(im):
    """Panel = color claro dominante. Acento = color de la paleta ajustado en claridad (mismo tono)
    hasta cumplir MIN_CONTRAST contra el peor caso: el panel al PANEL_MIX sobre el pixel más
    oscuro de la imagen. Entre los candidatos gana el que conserva más color."""
    small = im.resize((200, 114))
    q = small.quantize(16, method=Image.Quantize.MEDIANCUT)
    pal = q.getpalette()
    total = small.width * small.height
    colors = [(n, tuple(pal[i * 3:i * 3 + 3])) for n, i in sorted(q.getcolors(), reverse=True)]
    darkest = sorted(small.getdata(), key=lum)[total // 50]  # percentil 2, ignora píxeles sueltos

    light = [c for n, c in colors if lum(c) > 0.25] or [max((c for _, c in colors), key=lum)]
    panel = light[0]
    # Si el panel es muy oscuro para el peor caso, se aclara conservando su tono
    h, l, s = hls(panel)
    need = MIN_CONTRAST * (MIN_ACCENT_LUM + 0.05) - 0.05
    while lum(mix(panel, darkest, PANEL_MIX)) < need and l < 0.95:
        l += 0.01
        panel = rgb(h, l, s)
    worst = mix(panel, darkest, PANEL_MIX)

    # Acento: cada color con presencia real (>= 1% de la imagen) se ajusta en claridad hasta cumplir el contraste; gana el que conserva más color (croma) después del ajuste.
    def fit(c):
        h, _, s = hls(c)
        l, s = 0.6, max(s, 0.6)  # desde tono medio hacia abajo: el más claro que cumpla
        while contrast(rgb(h, l, s), worst) < MIN_CONTRAST and l > 0:
            l -= 0.005
        return rgb(h, max(l, 0), s)
    chroma = lambda c: max(c) - min(c)
    accent = max((fit(c) for n, c in colors if n >= total * 0.01), key=chroma)
    assert contrast(accent, worst) >= MIN_CONTRAST and contrast(accent, panel) >= MIN_CONTRAST, (panel, accent)
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
    print(name, "panel", hexc(panel), "acento", hexc(accent), "contraste %.1f" % contrast(panel, accent))

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

# Foto de perfil (arriba del link de Instagram): reemplazar el archivo al cambiar de foto
av = Image.open(os.path.join(SRC, "Autorretrato 2026.png")).convert("RGB")
side = min(av.size)
av = av.crop(((av.width - side) // 2, (av.height - side) // 2, (av.width + side) // 2, (av.height + side) // 2))
av.resize((320, 320), Image.Resampling.LANCZOS).save("avatar.webp", "WEBP", quality=85, method=6)
