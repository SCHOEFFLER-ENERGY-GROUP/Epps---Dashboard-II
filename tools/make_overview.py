"""EPPS weekly Overview PDF.
Usage: python3 make_overview.py overview.png out.pdf <acreage prev> <acreage curr> <acreage total> <infra prev> <infra curr> <infra total> [title]
Page 1224 x 963.75 pt: dashboard Overview capture (3264x2170) on top, 150 pt Bonus Payments panel below.
Current Week $0.00 is grey, non-zero white; the Total column is blue."""
import sys
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont('Sans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('SansB', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Mono', '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'))
pdfmetrics.registerFont(TTFont('MonoB', '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'))

img, out = sys.argv[1], sys.argv[2]
ap, ac, at, ip, ic, it = map(float, sys.argv[3:9])
title = sys.argv[9] if len(sys.argv) > 9 else 'EPPS Dashboard - Overview'

W, H = 1224, 963.75
PANEL = 150
IMG_H = W * 2170 / 3264          # 813.75
BG = HexColor('#0f1523'); CARD = HexColor('#141c2c'); LINE = HexColor('#25304a')
TXT = HexColor('#e6ebf5'); MUTED = HexColor('#7c879e'); GREY = HexColor('#5b6579'); BLUE = HexColor('#5b9bff')

c = canvas.Canvas(out, pagesize=(W, H)); c.setTitle(title)
c.setFillColor(BG); c.rect(0, 0, W, H, fill=1, stroke=0)
c.drawImage(img, 0, PANEL, width=W, height=IMG_H)

# panel card
x0, y0, cw, ch = 39, 14, W - 78, PANEL - 22
c.setFillColor(CARD); c.setStrokeColor(LINE); c.setLineWidth(0.8)
c.roundRect(x0, y0, cw, ch, 10, fill=1, stroke=1)
c.setFillColor(TXT); c.setFont('SansB', 13); c.drawString(x0 + 16, y0 + ch - 24, 'Bonus Payments')
c.setFillColor(MUTED); c.setFont('Sans', 8.5); c.drawString(x0 + 16, y0 + ch - 38, 'From the Mapper Export Weekly Summary · EPPS - Bonus Payments')

cols = [x0 + 16, x0 + cw * 0.45, x0 + cw * 0.67, x0 + cw - 16]   # name, prev(right), curr(right), total(right)
hy = y0 + ch - 58
c.setFont('Sans', 8.5); c.setFillColor(MUTED)
c.drawString(cols[0], hy, 'PROJECT')
for x, t in zip(cols[1:], ['PREVIOUS WEEK', 'CURRENT WEEK', 'TOTAL BONUS']): c.drawRightString(x, hy, t)
c.setStrokeColor(LINE); c.line(cols[0], hy - 6, cols[3], hy - 6)

def money(v): return '${:,.2f}'.format(v)
rows = [('ETP - Epps Acreage', ap, ac, at), ('ETP - Epps Infrastructure', ip, ic, it), ('Total', ap + ip, ac + ic, at + it)]
y = hy - 22
for i, (n, p, cu, t) in enumerate(rows):
    tot = (n == 'Total')
    if tot: c.setStrokeColor(LINE); c.line(cols[0], y + 13, cols[3], y + 13)
    c.setFont('SansB' if tot else 'Sans', 10.5); c.setFillColor(TXT); c.drawString(cols[0], y, n)
    f = 'MonoB' if tot else 'Mono'
    c.setFont(f, 10.5); c.setFillColor(TXT); c.drawRightString(cols[1], y, money(p))
    c.setFillColor(GREY if round(cu, 2) == 0 else TXT); c.drawRightString(cols[2], y, money(cu))
    c.setFillColor(BLUE); c.drawRightString(cols[3], y, money(t))
    y -= 19
c.showPage(); c.save()
print('wrote', out)
