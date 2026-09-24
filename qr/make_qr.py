"""QR estilizado de medaunbrauni.com: trazos redondeados tipo tinta, esquinas con rombo al centro (el ojo del logo)
y el símbolo de la hormiga al centro. Negro sobre transparente.
Uso: python qr/make_qr.py  -> qr/medaunbrauni_qr.svg (el PNG se renderiza aparte)"""
import base64, io, os
import qrcode
from PIL import Image

URL = "https://medaunbrauni.com"
SRC = r"G:\Mi unidad\Medaunbrauni\MEDAUNBRAUNI SITIO WEB\Landing Page\Logo_Medaunbrauni_ (2).png"
QUIET = 4          # margen en módulos que exige el estándar
DOT = 0.5          # radio de cada punto (módulo = 1); 0.5 = los vecinos se tocan
OUT = os.path.join(os.path.dirname(__file__), "medaunbrauni_qr.svg")

qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, border=0)
qr.add_data(URL)
qr.make(fit=True)
m = qr.get_matrix()
n = len(m)
print("versión", qr.version, f"{n}x{n}")

# Zona central libre para el símbolo (rectángulo vertical, ~9% del código; H tolera ~30%)
c = n // 2
CLEAR_W, CLEAR_H = 3, 5  # semiancho / semialto en módulos
clear = lambda x, y: abs(x - c) <= CLEAR_W and abs(y - c) <= CLEAR_H

finders = [(0, 0), (n - 7, 0), (0, n - 7)]
in_finder = lambda x, y: any(fx <= x < fx + 7 and fy <= y < fy + 7 for fx, fy in finders)
dark = lambda x, y: 0 <= x < n and 0 <= y < n and m[y][x] and not in_finder(x, y) and not clear(x, y)

# Probado con ZXing: puntos unidos con sus vecinos y esquinas sólidas se leen igual que un QR
# normal; puntos sueltos en las esquinas o esquinas en rombo NO se leen en tamaños chicos.
els = []
for y in range(n):
    for x in range(n):
        if not dark(x, y):
            continue
        X, Y = x + QUIET, y + QUIET
        els.append(f'<circle cx="{X + .5}" cy="{Y + .5}" r="{DOT}"/>')
        if dark(x + 1, y):  # puente al vecino derecho
            els.append(f'<rect x="{X + .5}" y="{Y + .5 - DOT}" width="1" height="{2 * DOT}"/>')
        if dark(x, y + 1):  # puente al vecino de abajo
            els.append(f'<rect x="{X + .5 - DOT}" y="{Y + .5}" width="{2 * DOT}" height="1"/>')


def rrect(x, y, w, r):
    return f"M{x + r} {y}H{x + w - r}A{r} {r} 0 0 1 {x + w} {y + r}V{y + w - r}A{r} {r} 0 0 1 {x + w - r} {y + w}H{x + r}A{r} {r} 0 0 1 {x} {y + w - r}V{y + r}A{r} {r} 0 0 1 {x + r} {y}Z"


# Esquinas: marco redondeado + rombo al centro (el ojo del logo)
for fx, fy in finders:
    X, Y = fx + QUIET, fy + QUIET
    cx, cy = X + 3.5, Y + 3.5
    els.append(f'<path fill-rule="evenodd" d="{rrect(X, Y, 7, 2.2)}{rrect(X + 1, Y + 1, 5, 1.5)}"/>')
    els.append(f'<path d="M{cx} {cy - 1.9}L{cx + 1.9} {cy}L{cx} {cy + 1.9}L{cx - 1.9} {cy}Z"/>')

# Símbolo de la hormiga (parte izquierda del logo), en negro
logo = Image.open(SRC).convert("RGBA")
logo = logo.crop(logo.getbbox())
alpha = logo.split()[3]
cols = [alpha.crop((x, 0, x + 1, logo.height)).getbbox() is not None for x in range(logo.width)]
gap = cols.index(False)  # primera columna vacía = fin del símbolo
sym = logo.crop((0, 0, gap, logo.height))
sym = sym.crop(sym.getbbox())
black = Image.new("RGBA", sym.size, (0, 0, 0, 255))
black.putalpha(sym.split()[3])
buf = io.BytesIO()
black.save(buf, "PNG", optimize=True)
b64 = base64.b64encode(buf.getvalue()).decode()

box_h = CLEAR_H * 2 + 1 - 1.2          # deja 0.6 módulo de aire arriba y abajo
box_w = box_h * sym.width / sym.height
sx, sy = c + 0.5 + QUIET - box_w / 2, c + 0.5 + QUIET - box_h / 2

size = n + 2 * QUIET
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {size} {size}" width="{size * 40}" height="{size * 40}">
<g fill="#000">{"".join(els)}</g>
<image x="{sx:.3f}" y="{sy:.3f}" width="{box_w:.3f}" height="{box_h:.3f}" xlink:href="data:image/png;base64,{b64}"/>
</svg>
'''
open(OUT, "w").write(svg)
print("escrito", OUT, f"{len(svg) // 1024} KB")
