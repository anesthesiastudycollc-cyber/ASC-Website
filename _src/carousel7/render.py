"""ASC 7-format carousel renderer: 1080x1350, navy / light blue / white, LLC logo on every slide."""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1350
NAVY = (5, 31, 52)
NAVY2 = (10, 48, 82)
BLUE = (77, 163, 255)
BLUE_D = (43, 92, 210)
LIGHT = (222, 238, 255)
WHITE = (255, 255, 255)
GOLD = (246, 205, 22)
INK = (12, 30, 52)
RED = (214, 64, 69)
GREEN = (24, 160, 106)
FOOT = "© 2026 Anesthesia Study Co. LLC · Teaching reference — not a medical directive."
HERE = os.path.dirname(os.path.abspath(__file__))


def F(w, s):
    return ImageFont.truetype(os.path.join(HERE, "fonts", f"Montserrat-{w}.ttf"), s)


def keyed_logo():
    im = Image.open(os.path.join(HERE, "logo_llc.png")).convert("RGB")
    px = im.load(); out = Image.new("RGBA", im.size)
    op = out.load()
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            r, g, b = px[x, y]
            d = abs(r - 5) + abs(g - 31) + abs(b - 52)
            a = max(0, min(255, (d - 18) * 6))
            op[x, y] = (r, g, b, a)
    return out


LOGO = keyed_logo()
MARK = LOGO.crop((150, 80, 405, 320))           # the "A" with EKG wave
FULL = LOGO.crop((140, 80, 410, 425))           # mark + wordmark


def paste_h(img, src, x, y, h):
    w = int(src.width * h / src.height)
    s = src.resize((w, h), Image.LANCZOS)
    img.alpha_composite(s, (x, y))
    return w


def wrap(d, text, font, maxw):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split():
            t = (cur + " " + word).strip()
            if d.textlength(t, font=font) <= maxw:
                cur = t
            else:
                if cur: lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


def tb(d, xy, text, font, fill, maxw, gap=1.25, draw=True, center=False):
    x, y = xy
    for ln in wrap(d, text, font, maxw):
        if draw:
            if center:
                d.text((x + maxw / 2, y), ln, font=font, fill=fill, anchor="ma")
            else:
                d.text((x, y), ln, font=font, fill=fill)
        y += int(font.size * gap)
    return y


def base(idx, n, label):
    img = Image.new("RGBA", (W, H), NAVY + (255,))
    # soft light-blue glow top-right
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((560, -380, 1460, 520), fill=BLUE_D + (90,))
    gd.ellipse((-420, 980, 380, 1700), fill=BLUE_D + (60,))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(140)))
    d = ImageDraw.Draw(img)
    paste_h(img, MARK, 54, 38, 74)
    d.text((140, 56), "ANESTHESIA STUDY CO.", font=F("ExtraBold", 30), fill=WHITE)
    d.text((140, 92), label.upper(), font=F("Bold", 22), fill=BLUE)
    d.text((W - 60, 62), f"{idx}/{n}", font=F("Bold", 28), fill=LIGHT, anchor="ra")
    d.text((W // 2, H - 38), FOOT, font=F("Medium", 20), fill=(160, 185, 210), anchor="ms")
    return img, d


def card(img, box, header=None, hcol=BLUE_D):
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, radius=34, fill=WHITE)
    if header:
        d.rounded_rectangle((x0, y0, x1, y0 + 92), radius=34, fill=hcol)
        d.rectangle((x0, y0 + 50, x1, y0 + 92), fill=hcol)
        d.text((x0 + 46, y0 + 46), header.upper(), font=F("ExtraBold", 36), fill=WHITE, anchor="lm")
        return y0 + 130
    return y0 + 50


def centered_card(img, render, header=None, hcol=BLUE_D, top_min=170):
    probe = ImageDraw.Draw(Image.new("RGB", (W, 5000)))
    h = render(probe, 0, False) + (130 if header else 50) + 44
    top = max(top_min, (H - h) // 2 + 20)
    y = card(img, (60, top, W - 60, top + h), header, hcol)
    render(ImageDraw.Draw(img), y, True)
    return top + h


def pearl(d, y, text, draw):
    pf = F("Bold", 40)
    lines = wrap(d, text, pf, W - 268)
    hh = len(lines) * int(40 * 1.25) + 52
    if draw:
        d.rounded_rectangle((104, y, W - 104, y + hh), radius=22, fill=(255, 245, 196))
        tb(d, (134, y + 26), text, pf, INK, W - 268)
    return y + hh + 26


# ---------- slide kinds ----------
def s_cover(s, img, d):
    y = 250
    tag = s.get("tag", "").upper()
    if tag:
        tw = d.textlength(tag, font=F("ExtraBold", 30))
        d.rounded_rectangle((60, y, 60 + tw + 52, y + 66), radius=33, fill=BLUE)
        d.text((86, y + 33), tag, font=F("ExtraBold", 30), fill=NAVY, anchor="lm")
        y += 120
    y = tb(d, (60, y), s["title"], F("ExtraBold", 86), WHITE, W - 120, 1.12)
    if s.get("sub"):
        y = tb(d, (60, y + 34), s["sub"], F("SemiBold", 42), LIGHT, W - 120, 1.28)
    d.rounded_rectangle((60, H - 210, 60 + 70, H - 204), radius=3, fill=GOLD)
    d.text((60, H - 180), "SWIPE  →", font=F("ExtraBold", 40), fill=GOLD)


def s_myth(s, img, d):
    def r(dd, y, draw):
        if draw:
            dd.rounded_rectangle((104, y, 104 + 190, y + 60), radius=30, fill=RED)
            dd.text((199, y + 30), "MYTH", font=F("ExtraBold", 32), fill=WHITE, anchor="mm")
        y = tb(dd, (104, y + 84), s["myth"], F("SemiBold", 46), (110, 120, 135), W - 208, 1.25, draw) + 26
        if draw:
            dd.line((104, y, W - 104, y), fill=(220, 228, 238), width=3)
        y += 34
        if draw:
            dd.rounded_rectangle((104, y, 104 + 190, y + 60), radius=30, fill=GREEN)
            dd.text((199, y + 30), "FACT", font=F("ExtraBold", 32), fill=WHITE, anchor="mm")
        y = tb(dd, (104, y + 84), s["fact"], F("Bold", 50), INK, W - 208, 1.25, draw) + 26
        if s.get("pearl"):
            y = pearl(dd, y, s["pearl"], draw)
        return y
    centered_card(img, r, s.get("header"))


def s_mistake(s, img, d):
    def r(dd, y, draw):
        if draw:
            dd.ellipse((104, y, 200, y + 96), fill=RED)
            dd.text((152, y + 48), str(s["n"]), font=F("ExtraBold", 50), fill=WHITE, anchor="mm")
        y2 = tb(dd, (228, y + 8), s["mistake"], F("ExtraBold", 50), INK, W - 332, 1.18, draw)
        y = max(y + 110, y2) + 24
        if s.get("why"):
            y = tb(dd, (104, y), s["why"], F("Medium", 42), (70, 85, 105), W - 208, 1.3, draw) + 26
        fx = F("Bold", 44)
        lines = wrap(dd, "FIX: " + s["fix"], fx, W - 276)
        hh = len(lines) * int(44 * 1.28) + 56
        if draw:
            dd.rounded_rectangle((104, y, W - 104, y + hh), radius=22, fill=LIGHT)
            dd.rectangle((104, y, 116, y + hh), fill=GREEN)
            tb(dd, (144, y + 28), "FIX: " + s["fix"], fx, INK, W - 276, 1.28)
        return y + hh + 20
    centered_card(img, r)


def s_compare(s, img, d):
    a, b = s["cols"]
    colw = (W - 120 - 56) // 2
    def r(dd, y, draw):
        if draw:
            dd.rounded_rectangle((88, y, 88 + colw - 8, y + 86), radius=22, fill=BLUE_D)
            dd.rounded_rectangle((88 + colw + 8, y, 88 + 2 * colw, y + 86), radius=22, fill=NAVY2)
            dd.text((88 + (colw - 8) / 2, y + 43), a, font=F("ExtraBold", 38), fill=WHITE, anchor="mm")
            dd.text((88 + colw + 8 + (colw - 8) / 2, y + 43), b, font=F("ExtraBold", 38), fill=WHITE, anchor="mm")
        y += 110
        for lab, va, vb in s["rows"]:
            if draw:
                dd.text((W // 2, y), lab.upper(), font=F("ExtraBold", 28), fill=BLUE_D, anchor="ma")
            y += 44
            f = F("SemiBold", 38)
            ya = tb(dd, (104, y), va, f, INK, colw - 40, 1.22, draw, center=True)
            yb = tb(dd, (88 + colw + 24, y), vb, f, INK, colw - 40, 1.22, draw, center=True)
            if draw:
                dd.line((W // 2, y - 4, W // 2, max(ya, yb) - 6), fill=(210, 220, 232), width=3)
            y = max(ya, yb) + 22
            if draw:
                dd.line((104, y - 10, W - 104, y - 10), fill=(230, 236, 244), width=2)
            y += 14
        if s.get("pearl"):
            y = pearl(dd, y, s["pearl"], draw)
        return y
    centered_card(img, r, s.get("header"), top_min=150)


def s_checklist(s, img, d):
    def r(dd, y, draw):
        for it in s["items"]:
            if draw:
                dd.rounded_rectangle((104, y + 4, 156, y + 56), radius=10, outline=BLUE_D, width=5)
                dd.line((116, y + 30, 128, y + 44), fill=GREEN, width=7)
                dd.line((128, y + 44, 148, y + 14), fill=GREEN, width=7)
            if isinstance(it, list):
                y2 = tb(dd, (184, y), it[0], F("ExtraBold", 46), INK, W - 290, 1.15, draw)
                y = tb(dd, (184, y2 + 2), it[1], F("Medium", 38), (70, 85, 105), W - 290, 1.25, draw) + 28
            else:
                y = tb(dd, (184, y + 2), it, F("SemiBold", 46), INK, W - 290, 1.2, draw) + 28
        if s.get("pearl"):
            y = pearl(dd, y, s["pearl"], draw)
        return y
    centered_card(img, r, s.get("header"))


def s_step(s, img, d):
    def r(dd, y, draw):
        if draw:
            dd.ellipse((104, y, 214, y + 110), fill=BLUE_D)
            dd.text((159, y + 55), str(s["n"]), font=F("ExtraBold", 60), fill=WHITE, anchor="mm")
        y2 = tb(dd, (240, y + 22), s["title"], F("ExtraBold", 58), INK, W - 344, 1.12, draw)
        y = max(y + 130, y2) + 20
        for b in s.get("bullets", []):
            if draw:
                dd.ellipse((108, y + 20, 130, y + 42), fill=BLUE)
            y = tb(dd, (152, y), b, F("SemiBold", 44), INK, W - 256, 1.25, draw) + 24
        if s.get("pearl"):
            y = pearl(dd, y, s["pearl"], draw)
        return y
    centered_card(img, r)


def s_quote(s, img, d):
    y = 300
    d.text((60, y - 40), "“", font=F("ExtraBold", 220), fill=BLUE)
    y = tb(d, (60, y + 150), s["quote"], F("ExtraBold", 72), WHITE, W - 120, 1.16)
    if s.get("sub"):
        tb(d, (60, y + 40), s["sub"], F("SemiBold", 42), LIGHT, W - 120, 1.3)


def s_story(s, img, d):
    probe = ImageDraw.Draw(Image.new("RGB", (W, 5000)))
    h = (70 if s.get("kicker") else 0) + len(wrap(probe, s["text"], F("SemiBold", 54), W - 120)) * int(54 * 1.34)
    if s.get("pearl"):
        h += 30 + len(wrap(probe, s["pearl"], F("Bold", 42), W - 200)) * int(42 * 1.28) + 56
    y = max(200, (H - h) // 2)
    if s.get("kicker"):
        d.text((60, y), s["kicker"].upper(), font=F("ExtraBold", 32), fill=GOLD)
        y += 70
    y = tb(d, (60, y), s["text"], F("SemiBold", 54), WHITE, W - 120, 1.34)
    if s.get("pearl"):
        y += 30
        pf = F("Bold", 42)
        lines = wrap(d, s["pearl"], pf, W - 200)
        hh = len(lines) * int(42 * 1.28) + 56
        d.rounded_rectangle((60, y, W - 60, y + hh), radius=24, fill=WHITE)
        d.rectangle((60, y, 72, y + hh), fill=GOLD)
        tb(d, (100, y + 28), s["pearl"], pf, INK, W - 200, 1.28)


def s_body(s, img, d):
    def r(dd, y, draw):
        if s.get("big"):
            y = tb(dd, (104, y), s["big"], F("ExtraBold", 66), BLUE_D, W - 208, 1.12, draw) + 26
        for b in s.get("bullets", []):
            if draw:
                dd.ellipse((108, y + 20, 130, y + 42), fill=BLUE)
            y = tb(dd, (152, y), b, F("SemiBold", 46), INK, W - 256, 1.22, draw) + 26
        if s.get("body"):
            y = tb(dd, (104, y), s["body"], F("Medium", 46), INK, W - 208, 1.32, draw) + 26
        if s.get("pearl"):
            y = pearl(dd, y, s["pearl"], draw)
        return y
    centered_card(img, r, s.get("header"))


def s_cta(s, img, d):
    w = int(FULL.width * 330 / FULL.height)
    paste_h(img, FULL, (W - w) // 2, 170, 330)
    y = tb(d, (90, 560), s["title"], F("ExtraBold", 64), WHITE, W - 180, 1.14, center=True)
    y = tb(d, (90, y + 24), s.get("body", ""), F("SemiBold", 40), LIGHT, W - 180, 1.32, center=True)
    by = max(y + 40, 1020)
    d.rounded_rectangle((130, by, W - 130, by + 108), radius=54, fill=GOLD)
    d.text((W // 2, by + 54), s.get("button", "SAVE THIS POST"), font=F("ExtraBold", 40), fill=NAVY, anchor="mm")
    d.text((W // 2, by + 150), "anesthesiastudyco.com  ·  @anesthesiastudyco", font=F("Bold", 32), fill=BLUE, anchor="ma")


KINDS = dict(cover=s_cover, myth=s_myth, mistake=s_mistake, compare=s_compare, checklist=s_checklist,
             step=s_step, quote=s_quote, story=s_story, body=s_body, cta=s_cta)


def main(spec, outdir):
    for p in json.load(open(spec)):
        out = os.path.join(outdir, p["slug"]); os.makedirs(out, exist_ok=True)
        n = len(p["slides"])
        for i, s in enumerate(p["slides"], 1):
            img, d = base(i, n, p["label"])
            KINDS[s.get("kind", "body")](s, img, d)
            img.convert("RGB").save(os.path.join(out, f"slide{i}.jpg"), quality=92)
        with open(os.path.join(out, "caption.txt"), "w") as f:
            f.write(p["caption"])
        print("built", p["slug"], n)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
