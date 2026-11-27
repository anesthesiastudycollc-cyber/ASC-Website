#!/usr/bin/env python3
"""ASC holiday reel: Santa down the chimney -> ASC gifts under the tree -> the Student Planner (plan + mini lesson).
usage: python3 -I santa.py <fonts_dir> <assets_dir> <out_dir> [handle]"""
import sys, os, math, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONTS, ASSETS, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)
W, H, FPS, DUR = 1080, 1920, 30, 19.5
L, R, TOP, BOT = 64, 936, 230, 1440
NAVY, NAVY2 = (8, 18, 42), (16, 36, 82)
LB, CYAN, YEL, RED, WHITE, INK = (130, 205, 245), (0, 188, 212), (255, 214, 0), (240, 72, 72), (255, 255, 255), (16, 28, 60)
SITE = "www.anesthesiastudyco.com"
_fc = {}
def F(w, s):
    k = (w, s)
    if k not in _fc: _fc[k] = ImageFont.truetype(os.path.join(FONTS, f"Montserrat-{w}.ttf"), s)
    return _fc[k]
def ease(t): t = max(0, min(1, t)); return t * t * (3 - 2 * t)
def back(t):
    t = max(0, min(1, t)); c = 1.70158
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2
def prog(t, a, b): return max(0.0, min(1.0, (t - a) / (b - a)))

def wrap(text, font, maxw):
    d = ImageDraw.Draw(Image.new("RGB", (4, 4))); out, cur = [], ""
    for w in text.split():
        tst = (cur + " " + w).strip()
        if d.textlength(tst, font=font) <= maxw: cur = tst
        else: out.append(cur); cur = w
    out.append(cur); return out
def text_block(d, cx, y, text, weight, size, fill, maxw=R - L, gap=1.15, align="c", alpha=255):
    f = F(weight, size); ls = wrap(text, f, maxw)
    for i, ln in enumerate(ls):
        yy = y + int(i * size * gap)
        if align == "c": d.text((cx, yy), ln, font=f, fill=fill + (alpha,), anchor="ma")
        else: d.text((cx, yy), ln, font=f, fill=fill + (alpha,), anchor="la")
    return y + int(len(ls) * size * gap)

# ---------- assets ----------
cover = Image.open(os.path.join(ASSETS, "cover.png")).convert("RGB")
day = Image.open(os.path.join(ASSETS, "day.png")).convert("RGB")
lesson = Image.open(os.path.join(ASSETS, "lesson.png")).convert("RGB")

# ---------- background ----------
def bg(top=NAVY, bot=NAVY2):
    a = np.linspace(0, 1, H)[:, None, None]
    arr = (np.array(top)[None, None] * (1 - a) + np.array(bot)[None, None] * a).astype(np.uint8)
    arr = np.repeat(arr, W, axis=1)
    return Image.fromarray(arr, "RGB").convert("RGBA")
BG_NIGHT = bg((4, 10, 30), (18, 40, 92))
BG_ROOM = bg((14, 30, 70), (30, 52, 104))
BG_GRID = bg()
gd = ImageDraw.Draw(BG_GRID)
for x in range(0, W, 60): gd.line([(x, 0), (x, H)], fill=(255, 255, 255, 10))
for y in range(0, H, 60): gd.line([(0, y), (W, y)], fill=(255, 255, 255, 10))

rnd = random.Random(7)
STARS = [(rnd.randint(0, W), rnd.randint(0, 900), rnd.random() * 6.28, rnd.choice([2, 3, 3, 4])) for _ in range(90)]
SNOW = [(rnd.random() * W, rnd.random() * H, rnd.uniform(40, 110), rnd.uniform(3, 8), rnd.random() * 6.28) for _ in range(120)]

def draw_snow(d, t, alpha=220):
    for x0, y0, sp, r, ph in SNOW:
        y = (y0 + sp * t) % H
        x = x0 + 18 * math.sin(t * 1.3 + ph)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, alpha))

def footer(d):
    d.text((W // 2, 1392), SITE, font=F("ExtraBold", 40), fill=YEL + (255,), anchor="mm")
    d.text((W // 2, 1432), "© 2026 Anesthesia Study Co. LLC", font=F("Medium", 22), fill=(200, 215, 240, 255), anchor="mm")

def pill(d, cx, cy, text, size, fill, ink, padx=26, pady=12):
    f = F("ExtraBold", size); w = d.textlength(text, font=f)
    d.rounded_rectangle([cx - w / 2 - padx, cy - size / 2 - pady, cx + w / 2 + padx, cy + size / 2 + pady], radius=size, fill=fill)
    d.text((cx, cy), text, font=f, fill=ink, anchor="mm")

# ---------- Santa (back view, no face) ----------
def santa_layer():
    im = Image.new("RGBA", (420, 640), (0, 0, 0, 0)); d = ImageDraw.Draw(im); cx = 230
    # sack over left shoulder
    d.ellipse([20, 150, 200, 360], fill=(150, 98, 52), outline=(110, 70, 36), width=5)
    d.rectangle([70, 120, 120, 175], fill=(0, 188, 212)); d.rectangle([90, 120, 100, 175], fill=YEL)
    d.rectangle([118, 104, 170, 170], fill=YEL); d.rectangle([140, 104, 148, 170], fill=RED)
    d.ellipse([70, 140, 180, 190], fill=(150, 98, 52))
    # legs + boots
    d.rectangle([cx - 85, 470, cx - 10, 570], fill=(200, 30, 40)); d.rectangle([cx + 10, 470, cx + 85, 570], fill=(200, 30, 40))
    d.rounded_rectangle([cx - 100, 560, cx - 5, 625], radius=18, fill=(25, 25, 30))
    d.rounded_rectangle([cx + 5, 560, cx + 100, 625], radius=18, fill=(25, 25, 30))
    d.rectangle([cx - 92, 552, cx - 6, 572], fill=WHITE); d.rectangle([cx + 6, 552, cx + 92, 572], fill=WHITE)
    # coat
    d.rounded_rectangle([cx - 120, 200, cx + 120, 480], radius=60, fill=(214, 36, 46))
    d.rounded_rectangle([cx - 126, 440, cx + 126, 486], radius=20, fill=WHITE)
    d.rectangle([cx - 120, 330, cx + 120, 362], fill=(25, 25, 30))
    # arms
    d.rounded_rectangle([cx + 100, 220, cx + 160, 410], radius=30, fill=(200, 30, 40))
    d.rounded_rectangle([cx + 98, 380, cx + 162, 410], radius=10, fill=WHITE)
    d.ellipse([cx + 104, 400, cx + 158, 452], fill=(25, 25, 30))
    # back of head: white hair, beard edges, hat
    d.ellipse([cx - 78, 110, cx + 78, 250], fill=(245, 245, 245))
    d.ellipse([cx - 92, 170, cx - 40, 240], fill=(235, 235, 235)); d.ellipse([cx + 40, 170, cx + 92, 240], fill=(235, 235, 235))
    d.polygon([(cx - 80, 140), (cx + 80, 140), (cx + 110, 20), (cx + 40, 0)], fill=(214, 36, 46))
    d.rounded_rectangle([cx - 92, 120, cx + 92, 166], radius=22, fill=WHITE)
    d.ellipse([cx + 92, 0, cx + 136, 44], fill=WHITE)
    return im
SANTA = santa_layer()

def chimney(d, top_y=860):
    x0, x1 = 400, 680
    d.rectangle([x0, top_y, x1, 1500], fill=(150, 52, 42))
    for r, y in enumerate(range(top_y, 1500, 34)):
        d.line([(x0, y), (x1, y)], fill=(110, 36, 30), width=3)
        off = 0 if r % 2 == 0 else 35
        for x in range(x0 + off, x1, 70): d.line([(x, y), (x, y + 34)], fill=(110, 36, 30), width=3)
    d.rounded_rectangle([x0 - 30, top_y - 50, x1 + 30, top_y + 10], radius=10, fill=(170, 64, 52), outline=(110, 36, 30), width=4)
    d.rounded_rectangle([x0 - 34, top_y - 66, x1 + 34, top_y - 40], radius=12, fill=(250, 250, 255))  # snow cap

def scene_roof(t):
    im = BG_NIGHT.copy(); d = ImageDraw.Draw(im)
    for x, y, ph, r in STARS:
        a = int(120 + 120 * (0.5 + 0.5 * math.sin(t * 3 + ph)))
        d.ellipse([x - r / 2, y - r / 2, x + r / 2, y + r / 2], fill=(255, 255, 230, a))
    d.ellipse([760, 620, 880, 740], fill=(250, 245, 215)); d.ellipse([792, 605, 905, 720], fill=(10, 24, 62))
    # roof
    d.polygon([(0, 1420), (1080, 1200), (1080, 1920), (0, 1920)], fill=(30, 30, 52))
    d.polygon([(0, 1406), (1080, 1186), (1080, 1220), (0, 1440)], fill=(245, 248, 255))
    # santa slides into chimney: clipped at chimney mouth
    ty = 1090
    p = ease(prog(t, 1.3, 3.5)); sy = int(470 + p * 620 + (8 * math.sin(t * 9) if t < 1.3 else 0))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); layer.alpha_composite(SANTA, (540 - 230 + 6, sy))
    m = Image.new("L", (W, H), 255); ImageDraw.Draw(m).rectangle([0, ty - 40, W, H], fill=0)
    layer.putalpha(Image.fromarray(np.minimum(np.array(layer.getchannel("A")), np.array(m))))
    im.alpha_composite(layer)
    chimney(d, ty)
    # soot puff + sparkles when he's gone
    q = prog(t, 3.4, 4.5)
    if 0 < q < 1:
        for i in range(7):
            ang = -math.pi / 2 + (i - 3) * 0.35; rr = 40 + 160 * q
            x = 540 + math.cos(ang) * rr; y = ty - 60 + math.sin(ang) * rr * 0.8
            s = 30 + 50 * q; a = int(170 * (1 - q))
            d.ellipse([x - s, y - s, x + s, y + s], fill=(120, 120, 140, a))
    draw_snow(d, t)
    # hook
    a = int(255 * ease(prog(t, 0.0, 0.4)))
    pill(d, W // 2, 278, "HO HO HO!", 30, YEL + (a,), INK + (a,))
    text_block(d, W // 2, 326, "What's Santa bringing anesthesia students?", "ExtraBold", 62, WHITE, alpha=a)
    footer(d); return im

# ---------- tree + gifts ----------
def gift_img(w, h, box, rib, label=None, tag=False):
    im = Image.new("RGBA", (w + 40, h + 80), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x0, y0 = 20, 60
    d.rounded_rectangle([x0, y0 + 26, x0 + w, y0 + h], radius=10, fill=box)
    d.rounded_rectangle([x0 - 8, y0, x0 + w + 8, y0 + 34], radius=8, fill=tuple(max(0, c - 25) for c in box))
    rw = max(12, w // 9)
    d.rectangle([x0 + w / 2 - rw / 2, y0, x0 + w / 2 + rw / 2, y0 + h], fill=rib)
    d.ellipse([x0 + w / 2 - 52, y0 - 46, x0 + w / 2 - 2, y0 + 6], outline=rib, width=12)
    d.ellipse([x0 + w / 2 + 2, y0 - 46, x0 + w / 2 + 52, y0 + 6], outline=rib, width=12)
    if label:
        f = F("ExtraBold", 26 if not tag else 40); tw = d.textlength(label, font=f)
        cy = y0 + 26 + (h - 26) * 0.55; ph = 26 if not tag else 40
        d.rounded_rectangle([x0 + w / 2 - tw / 2 - 14, cy - ph / 2 - 10, x0 + w / 2 + tw / 2 + 14, cy + ph / 2 + 10], radius=12, fill=WHITE)
        d.text((x0 + w / 2, cy), label, font=f, fill=INK, anchor="mm")
    return im
GIFTS = [  # (cx, bottom, w, h, box, ribbon, label, t_in)
    (210, 1290, 230, 170, (0, 160, 190), YEL, "Mind maps", 4.9),
    (830, 1290, 230, 190, (214, 36, 46), WHITE, "Study guides", 5.3),
    (300, 1130, 200, 130, (90, 70, 170), YEL, "Quick Charts", 5.7),
    (770, 1130, 190, 120, (20, 130, 90), YEL, "Logbook", 6.1),
]
GIMG = [gift_img(w, h, b, r, l) for (_, _, w, h, b, r, l, _) in GIFTS]
BIG = gift_img(330, 250, YEL, NAVY2, "PLANNER", tag=True)

def paste_scaled(im, src, cx, bottom, s, alpha=1.0):
    if s <= 0.02: return
    w, h = max(1, int(src.width * s)), max(1, int(src.height * s))
    g = src.resize((w, h), Image.LANCZOS)
    if alpha < 1: g.putalpha(g.getchannel("A").point(lambda v: int(v * alpha)))
    im.alpha_composite(g, (int(cx - w / 2), int(bottom - h)))

def tree(d, t):
    cx = 540
    d.rectangle([cx - 40, 1060, cx + 40, 1170], fill=(110, 70, 36))
    tiers = [(640, 1080, 310), (530, 840, 240), (430, 670, 170)]
    for top, bot, half in reversed(tiers):
        d.polygon([(cx, top), (cx - half, bot), (cx + half, bot)], fill=(22, 120, 80))
        d.polygon([(cx, top), (cx - half, bot), (cx - half + 40, bot)], fill=(16, 96, 64))
    for top, bot, half in tiers:
        d.polygon([(cx, top), (cx - half, bot), (cx + half, bot)], outline=(12, 80, 54))
    rr = random.Random(3)
    cols = [CYAN, YEL, RED, LB, WHITE]
    for i in range(34):
        tier = tiers[i % 3]; top, bot, half = tier
        y = rr.uniform(top + 60, bot - 14); ww = half * (y - top) / (bot - top) - 20
        x = cx + rr.uniform(-ww, ww)
        on = (math.sin(t * 5 + i) > -0.2)
        c = cols[i % 5]; r = 9 if i % 3 else 13
        d.ellipse([x - r, y - r, x + r, y + r], fill=c + ((255,) if on else (110,)))
    # star
    s = 52 + 6 * math.sin(t * 6); pts = []
    for k in range(10):
        ang = -math.pi / 2 + k * math.pi / 5; rad = s if k % 2 == 0 else s * 0.45
        pts.append((cx + math.cos(ang) * rad, 430 + math.sin(ang) * rad))
    d.polygon(pts, fill=YEL)

def scene_tree(t):
    im = BG_ROOM.copy(); d = ImageDraw.Draw(im)
    # window w/ snow, floor, fireplace
    d.rounded_rectangle([80, 330, 250, 560], radius=14, fill=(6, 14, 40), outline=(200, 215, 240), width=8)
    d.line([(165, 330), (165, 560)], fill=(200, 215, 240), width=6); d.line([(80, 445), (250, 445)], fill=(200, 215, 240), width=6)
    d.rectangle([0, 1180, W, H], fill=(60, 40, 34))
    d.rectangle([0, 1180, W, 1196], fill=(80, 56, 46))
    # fireplace at right edge
    d.rectangle([820, 700, 1080, 1180], fill=(150, 52, 42)); d.rectangle([800, 680, 1080, 720], fill=(190, 180, 170))
    d.rectangle([870, 860, 1080, 1180], fill=(24, 14, 14))
    fl = 0.5 + 0.5 * math.sin(t * 12)
    d.polygon([(900, 1180), (950, 1040 - 30 * fl), (990, 1180)], fill=(255, 140, 20))
    d.polygon([(960, 1180), (1010, 1000 + 30 * fl), (1060, 1180)], fill=(255, 190, 40))
    # stocking with ASC EKG
    d.polygon([(880, 720), (940, 720), (940, 830), (980, 850), (960, 890), (880, 860)], fill=WHITE)
    d.line([(890, 780), (905, 780), (912, 755), (920, 805), (928, 780), (938, 780)], fill=RED, width=5)
    # soot puff from fireplace (Santa landed)
    q = prog(t, 4.4, 5.4)
    if 0 < q < 1:
        for i in range(6):
            x = 975 - 220 * q * (0.5 + i / 8); y = 1110 - 60 * math.sin(i) * q
            s = 26 + 40 * q
            d.ellipse([x - s, y - s, x + s, y + s], fill=(150, 150, 165, int(180 * (1 - q))))
    tree(d, t)
    for (cx, bot, *_r), gi in zip(GIFTS, GIMG):
        tin = _r[-1]; p = prog(t, tin, tin + 0.45)
        paste_scaled(im, gi, cx, bot + 40, back(p) if p > 0 else 0)
    # big planner gift drops in with glow
    p = prog(t, 6.6, 7.3)
    if p > 0:
        gl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gdd = ImageDraw.Draw(gl)
        pul = 0.75 + 0.25 * math.sin(t * 6)
        gdd.ellipse([340, 1060, 740, 1330], fill=(255, 214, 0, int(120 * pul * ease(p))))
        im.alpha_composite(gl.filter(ImageFilter.GaussianBlur(40)))
        y = 1330 - 700 * (1 - ease(p)) if p < 1 else 1330
        paste_scaled(im, BIG, 540, y + 40, 1.0)
    d = ImageDraw.Draw(im)
    draw_snow(d, t, alpha=0)  # (no indoor snow)
    a = int(255 * ease(prog(t, 4.5, 4.9)))
    text_block(d, W // 2, 250, "Under the tree: ASC study tools", "ExtraBold", 50, WHITE, alpha=a)
    if t > 6.9:
        a2 = int(255 * ease(prog(t, 6.9, 7.3)))
        pill(d, W // 2, 345, "...and one BIG gift", 32, YEL + (a2,), INK + (a2,))
    footer(d); return im

# ---------- reveal ----------
def scene_reveal(t):
    im = BG_GRID.copy(); d = ImageDraw.Draw(im)
    cx, cy = 540, 760
    rays = Image.new("RGBA", (W, H), (0, 0, 0, 0)); rd = ImageDraw.Draw(rays)
    rp = ease(prog(t, 8.6, 9.4))
    for k in range(14):
        ang = k * math.pi / 7 + t * 0.4
        rd.polygon([(cx, cy), (cx + 1400 * math.cos(ang - 0.09), cy + 1400 * math.sin(ang - 0.09)),
                    (cx + 1400 * math.cos(ang + 0.09), cy + 1400 * math.sin(ang + 0.09))], fill=(255, 214, 0, int(40 * rp)))
    im.alpha_composite(rays)
    # box base
    bx0, bx1, by0, by1 = 365, 715, 1080, 1320
    # cover rises out
    p = ease(prog(t, 8.8, 10.2)); s = 0.35 + 0.65 * p
    cw, ch = int(420 * s), int(543 * s)
    cimg = cover.resize((cw, ch), Image.LANCZOS)
    ccy = int(1180 - (1180 - cy) * p)
    sh = Image.new("RGBA", (cw + 40, ch + 40), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([20, 26, cw + 20, ch + 26], radius=14, fill=(0, 0, 0, 110))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)), (cx - cw // 2 - 20, ccy - ch // 2 - 20))
    im.paste(cimg, (cx - cw // 2, ccy - ch // 2))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=12, fill=YEL)
    d.rectangle([cx - 20, by0, cx + 20, by1], fill=NAVY2)
    # lid flies off
    lp = prog(t, 8.5, 9.3)
    ly = by0 - 40 - 900 * ease(lp); lx = cx + 300 * ease(lp)
    if lp < 1:
        lid = Image.new("RGBA", (380, 60), (0, 0, 0, 0)); ld = ImageDraw.Draw(lid)
        ld.rounded_rectangle([0, 0, 380, 60], radius=10, fill=(230, 190, 0)); ld.rectangle([170, 0, 210, 60], fill=NAVY2)
        lid = lid.rotate(-40 * ease(lp), expand=True)
        im.alpha_composite(lid, (int(lx - lid.width / 2), int(ly)))
    # sparkles
    rr = random.Random(11)
    for i in range(22):
        ang = rr.random() * 6.28; dist = 180 + rr.random() * 260
        tw = 0.5 + 0.5 * math.sin(t * 7 + i)
        if t > 9.2:
            x = cx + math.cos(ang) * dist; y = cy + math.sin(ang) * dist * 1.1; s2 = 6 + 8 * tw
            d.polygon([(x, y - s2 * 2), (x + s2 * 0.5, y), (x, y + s2 * 2), (x - s2 * 0.5, y)], fill=(255, 245, 180, int(230 * tw)))
            d.polygon([(x - s2 * 2, y), (x, y + s2 * 0.5), (x + s2 * 2, y), (x, y - s2 * 0.5)], fill=(255, 245, 180, int(230 * tw)))
    a = int(255 * ease(prog(t, 9.6, 10.1)))
    pill(d, W // 2, 278, "SANTA'S TOP PICK", 30, YEL + (a,), INK + (a,))
    text_block(d, W // 2, 322, "The Anesthesia Student Planner", "ExtraBold", 64, WHITE, alpha=a)
    footer(d); return im

# ---------- inside ----------
DW = 420; DH = int(DW * 1320 / 1020)
DAYI = day.resize((DW, DH), Image.LANCZOS); LESI = lesson.resize((DW, DH), Image.LANCZOS)
PX = [(64, 470), (516, 470)]
sc = DW / 1020
REG = {"hour": (80, 218, 356, 935), "pomo": (368, 952, 726, 1053), "concept": (368, 218, 726, 417),
       "med": (368, 443, 726, 935), "qs": (738, 952, 970, 1053)}
POINTS = [(11.3, "PLAN IT", "Hourly schedule, top 3 priorities and a study tracker", ["hour", "pomo"], None),
          (12.7, "LEARN IT", "Concept of the Day, Medication Spotlight, practice questions", ["concept", "med", "qs"], None),
          (14.1, "COLOR IT", "A labeled mini lesson every day: Day 1 is Upper Airway Anatomy", [], "lesson")]
def scene_inside(t):
    im = BG_GRID.copy(); d = ImageDraw.Draw(im)
    a = int(255 * ease(prog(t, 10.6, 11.0)))
    pill(d, W // 2, 272, "INSIDE EVERY DAY", 28, CYAN + (a,), WHITE + (a,))
    text_block(d, W // 2, 312, "A planner page + a mini lesson", "ExtraBold", 56, WHITE, alpha=a)
    for (x, y), pg, k in zip(PX, [DAYI, LESI], [0, 1]):
        p = ease(prog(t, 10.6 + 0.15 * k, 11.1 + 0.15 * k)); yy = int(y + 60 * (1 - p))
        sh = Image.new("RGBA", (DW + 40, DH + 40), (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle([20, 26, DW + 20, DH + 26], fill=(0, 0, 0, int(120 * p)))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)), (x - 20, yy - 20))
        g = pg.convert("RGBA"); g.putalpha(int(255 * p)); im.alpha_composite(g, (x, yy))
    d = ImageDraw.Draw(im)
    active = None
    for i, (t0, _, _, regs, pg) in enumerate(POINTS):
        if t >= t0: active = i
    if active is not None:
        t0, _, _, regs, pg = POINTS[active]
        pul = 0.6 + 0.4 * math.sin((t - t0) * 8)
        for r in regs:
            x0, y0, x1, y1 = REG[r]; ox, oy = PX[0]
            d.rounded_rectangle([ox + x0 * sc - 6, oy + y0 * sc - 6, ox + x1 * sc + 6, oy + y1 * sc + 6], radius=10,
                                outline=YEL + (int(255 * pul),), width=7)
        if pg:
            ox, oy = PX[1]
            d.rounded_rectangle([ox - 8, oy - 8, ox + DW + 8, oy + DH + 8], radius=12, outline=YEL + (int(255 * pul),), width=8)
    # point cards
    y = 1040
    for i, (t0, head, body, _, _) in enumerate(POINTS):
        p = ease(prog(t, t0, t0 + 0.35))
        if p <= 0: continue
        x0 = L + int(40 * (1 - p)); hi = (i == active)
        d.rounded_rectangle([x0, y, R, y + 96], radius=18, fill=(255, 255, 255, int(255 * p)) if hi else (225, 235, 250, int(235 * p)))
        d.ellipse([x0 + 16, y + 22, x0 + 68, y + 74], fill=YEL + (int(255 * p),))
        d.text((x0 + 42, y + 48), str(i + 1), font=F("ExtraBold", 30), fill=INK + (int(255 * p),), anchor="mm")
        d.text((x0 + 86, y + 12), head, font=F("ExtraBold", 26), fill=(0, 140, 170, int(255 * p)))
        f = F("SemiBold", 24); ls = wrap(body, f, R - x0 - 110)
        for j, ln in enumerate(ls[:2]): d.text((x0 + 86, y + 42 + j * 26), ln, font=f, fill=INK + (int(255 * p),))
        y += 108
    footer(d); return im

# ---------- outro ----------
def scene_outro(t):
    im = BG_NIGHT.copy(); d = ImageDraw.Draw(im)
    for x, y, ph, r in STARS:
        a = int(100 + 100 * (0.5 + 0.5 * math.sin(t * 3 + ph)))
        d.ellipse([x - r / 2, y - r / 2, x + r / 2, y + r / 2], fill=(255, 255, 230, a))
    p = back(prog(t, 15.4, 16.0))
    cw, ch = 330, int(330 * 543 / 420)
    c = cover.resize((cw, ch), Image.LANCZOS).convert("RGBA"); cd = ImageDraw.Draw(c)
    cd.rectangle([cw // 2 - 14, 0, cw // 2 + 14, ch], fill=RED + (235,)); cd.rectangle([0, ch // 2 - 14, cw, ch // 2 + 14], fill=RED + (235,))
    big = Image.new("RGBA", (cw + 160, ch + 160), (0, 0, 0, 0)); big.alpha_composite(c, (80, 110))
    bd = ImageDraw.Draw(big)
    bd.ellipse([cw // 2 + 80 - 70, 110 + ch // 2 - 50, cw // 2 + 80 - 4, 110 + ch // 2 + 14], outline=RED, width=14)
    bd.ellipse([cw // 2 + 80 + 4, 110 + ch // 2 - 50, cw // 2 + 80 + 70, 110 + ch // 2 + 14], outline=RED, width=14)
    big = big.rotate(-5, expand=True, resample=Image.BICUBIC)
    paste_scaled(im, big, 540, 860, max(0.01, p))
    d = ImageDraw.Draw(im)
    draw_snow(d, t, alpha=200)
    a = int(255 * ease(prog(t, 15.9, 16.4)))
    yy = text_block(d, W // 2, 880, "Give the gift of a better study day.", "ExtraBold", 62, WHITE, alpha=a)
    a2 = int(255 * ease(prog(t, 16.6, 17.0)))
    text_block(d, W // 2, yy + 20, "30 days of anesthesia mini lessons, starting with airway.", "SemiBold", 34, LB, alpha=a2)
    a3 = int(255 * ease(prog(t, 17.2, 17.6)))
    pill(d, W // 2, 1290, "See it at anesthesiastudyco.com", 38, YEL + (a3,), INK + (a3,))
    footer(d); return im

SCENES = [(0, 4.5, scene_roof), (4.5, 8.4, scene_tree), (8.4, 10.6, scene_reveal), (10.6, 15.3, scene_inside), (15.3, DUR, scene_outro)]
def frame(t):
    for i, (a, b, fn) in enumerate(SCENES):
        if a <= t < b:
            img = fn(t)
            if i > 0 and t < a + 0.3:  # crossfade
                prev = SCENES[i - 1][2](t)
                img = Image.blend(prev, img, (t - a) / 0.3)
            return img.convert("RGB")
    return SCENES[-1][2](t).convert("RGB")

# ---------- audio: Jingle Bells (public domain, 1857) on soft bells + sleigh jingles ----------
SR = 44100
def bell(freq, dur, amp):
    n = int(SR * dur); tt = np.arange(n) / SR
    env = np.exp(-tt * 5.0)
    return amp * env * (np.sin(2 * np.pi * freq * tt) + 0.4 * np.sin(2 * np.pi * freq * 2.76 * tt) + 0.2 * np.sin(2 * np.pi * freq * 5.4 * tt))
def audio(path):
    n = int(SR * DUR); out = np.zeros(n)
    N = {"C": 523.25, "D": 587.33, "E": 659.25, "F": 698.46, "G": 783.99, "c": 261.63, "g": 392.0}
    beat = 0.36
    mel = [("E", 1), ("E", 1), ("E", 2), ("E", 1), ("E", 1), ("E", 2), ("E", 1), ("G", 1), ("C", 1.5), ("D", .5), ("E", 4),
           ("F", 1), ("F", 1), ("F", 1.5), ("F", .5), ("F", 1), ("E", 1), ("E", 1), ("E", .5), ("E", .5),
           ("E", 1), ("D", 1), ("D", 1), ("E", 1), ("D", 2), ("G", 2)]
    t0 = 0.3; reps = 0
    while t0 < DUR - 1.2 and reps < 3:
        for nt, b in mel:
            if t0 >= DUR - 1.2: break
            s = bell(N[nt], 1.2, 0.18); i = int(t0 * SR); e = min(n, i + len(s)); out[i:e] += s[:e - i]
            t0 += b * beat
        reps += 1
    rng = np.random.default_rng(1)
    k = 0.3
    while k < DUR:  # sleigh-bell jingle on each beat
        m = int(SR * 0.12); nz = rng.standard_normal(m) * np.exp(-np.arange(m) / SR * 40)
        nz = np.diff(np.concatenate([[0], nz])) * 0.05; i = int(k * SR); e = min(n, i + m); out[i:e] += nz[:e - i]
        k += beat
    for tt_, f in [(8.5, 1318.5), (9.2, 1568.0)]:
        s = bell(f, 1.0, 0.2); i = int(tt_ * SR); out[i:i + len(s)] += s
    fade = np.ones(n); fl = int(SR * 1.0); fade[-fl:] = np.linspace(1, 0, fl); out *= fade
    out = out / max(1e-6, np.abs(out).max()) * 0.6
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes())

if __name__ == "__main__":
    wav = os.path.join(OUT, "audio.wav"); audio(wav)
    mp4 = os.path.join(OUT, "reel.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-i", wav, "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
                          "-shortest", "-movflags", "+faststart", mp4], stdin=subprocess.PIPE)
    nf = int(DUR * FPS)
    for i in range(nf):
        p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close(); p.wait()
    frame(9.9).save(os.path.join(OUT, "cover.jpg"), quality=92)
    shots = [1.2, 2.8, 4.0, 6.0, 7.8, 9.0, 10.3, 11.8, 13.2, 14.6, 16.2, 18.5]
    th = [frame(s).resize((270, 480)) for s in shots]
    sheet = Image.new("RGB", (270 * 6 + 70, 480 * 2 + 30), (240, 244, 250))
    for i, im in enumerate(th):
        o = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(o)
        im2 = im.convert("RGBA")
        z = Image.new("RGBA", (270, 480), (0, 0, 0, 0)); zd = ImageDraw.Draw(z)
        zd.rectangle([0, 0, 270, 150 / 4], fill=(255, 0, 0, 60)); zd.rectangle([0, 1490 / 4, 270, 480], fill=(255, 0, 0, 60))
        zd.rectangle([940 / 4, 600 / 4, 270, 1490 / 4], fill=(255, 0, 0, 60))
        im2.alpha_composite(z); ImageDraw.Draw(im2).text((6, 6), f"{shots[i]}s", fill=(255, 255, 0), font=F("ExtraBold", 22))
        sheet.paste(im2.convert("RGB"), (10 + (i % 6) * 280, 10 + (i // 6) * 490))
    sheet.save(os.path.join(OUT, "contact.jpg"), quality=88)
    print("done", mp4)
