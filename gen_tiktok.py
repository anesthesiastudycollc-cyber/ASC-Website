"""ASC TikTok generator: faceless 1080x1920 reels, programmatic graphics only (no AI imagery, no people).

Formats
  "brand" (12:30 PM company spotlight, 16 s): hook + product mockup -> kicker -> 3 points -> where to get it -> outro.
  "case"  (8:30 PM Quick Case, 22 s): monitor + scene -> question + 4 options -> 3-2-1 -> reveal -> why -> pearl + CTA.

Usage: python3 -I _src/gen_tiktok.py <spec.json> <outdir>
  spec path may be relative to _src. Writes <outdir>/<date>/reel.mp4 + cover.jpg for every post,
  and <outdir>/contact.jpg (key frames of every reel with TikTok UI zones shaded) for review.
Spec fields, layout rules and the topic log live in TIKTOK.md. Example: tiktok-sample.json.
"""
import json, math, os, re, struct, subprocess, sys, wave
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1920
FPS_ANIM = 15
# TikTok safe zone: top tabs ~0-150, right action rail x>940 (y 600-1500), bottom caption/sound bar y>1490.
L, R, TOP, BOT = 64, 936, 230, 1440
CW = R - L

NAVY_D, NAVY, NAVY_L = (8, 18, 42), (16, 36, 82), (28, 58, 120)
LBLUE, CYAN, WHITE = (130, 205, 245), (0, 188, 212), (255, 255, 255)
YELLOW, RED, GREEN, GREY = (255, 214, 0), (240, 72, 72), (0, 230, 118), (150, 165, 195)
INK = (16, 28, 60)

BANNED = [r"\bAndrea\b", r"\bRegan\b", r"\bNSU\b", r"Nova Southeastern", r"(?i)\buniversity\b",
          r"(?i)\bprofessor\b", r"\bNCCAA\b", r"\bNBCRNA\b", r"\bNCE\b", r"\bCDQ\b"]

_fonts = {}


def F(w, s):
    k = (w, s)
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(os.path.join(HERE, "fonts", f"Montserrat-{w}.ttf"), s)
    return _fonts[k]


PROBE = ImageDraw.Draw(Image.new("RGB", (10, 10)))


def wrap(text, font, maxw):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split():
            t = (cur + " " + word).strip()
            if PROBE.textlength(t, font=font) <= maxw or not cur:
                cur = t
            else:
                lines.append(cur); cur = word
        lines.append(cur)
    return lines


def fit(text, weight, maxs, mins, maxw, maxh, gap=1.15):
    """Largest font size where the wrapped text fits the box. Raises instead of clipping."""
    for s in range(maxs, mins - 1, -2):
        f = F(weight, s)
        ls = wrap(text, f, maxw)
        h = len(ls) * int(s * gap)
        if h <= maxh and all(PROBE.textlength(x, font=f) <= maxw for x in ls):
            return f, ls, h
    raise ValueError(f"Text does not fit ({maxw}x{maxh}, min {mins}px): {text[:60]!r}. Shorten it.")


def lines_at(d, x, y, ls, f, fill, gap=1.15, align="l"):
    for ln in ls:
        if align == "c":
            d.text((x, y), ln, font=f, fill=fill, anchor="ma")
        else:
            d.text((x, y), ln, font=f, fill=fill)
        y += int(f.size * gap)
    return y


def layer():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def ease(p):
    p = max(0.0, min(1.0, p))
    return 1 - (1 - p) ** 3


# ---------- background, header, footer ----------

def background(label, year, footer_note=True):
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(NAVY_D[i] * (1 - t) + NAVY[i] * t) for i in range(3)))
    # faint grid + EKG motif
    for x in range(0, W, 90):
        d.line([(x, 0), (x, H)], fill=(22, 40, 84))
    for y in range(0, H, 90):
        d.line([(0, y), (W, y)], fill=(22, 40, 84))
    ekg(d, 0, 1560, W, 70, (34, 70, 130), 3, beats=3)
    img = img.convert("RGBA")
    d = ImageDraw.Draw(img)
    logo = os.path.join(HERE, "brand", "logo.png")
    x = L
    if os.path.exists(logo):
        lg = Image.open(logo).convert("RGBA")
        lg.thumbnail((64, 64))
        img.alpha_composite(lg, (L, 152 + (64 - lg.height) // 2))
        x = L + lg.width + 16
    d.text((x, 184), "ANESTHESIA STUDY CO.", font=F("ExtraBold", 32), fill=WHITE, anchor="lm")
    d.text((R, 184), label, font=F("ExtraBold", 28), fill=LBLUE, anchor="rm")
    d.line([(L, 222), (R, 222)], fill=(60, 90, 150), width=2)
    note = f"© {year} Anesthesia Study Co. LLC" + (" · Teaching reference, not a medical directive." if footer_note else "")
    f, ls, _ = fit(note, "Medium", 22, 16, CW, 60)
    lines_at(d, (L + R) // 2, 1452, ls, f, (170, 190, 225), 1.2, "c")
    return img


def ekg(d, x0, y0, w, h, col, width=4, beats=4, head=None, gap=40):
    """Synthetic ECG trace. If head is set, leave a gap ahead of the sweep (monitor look)."""
    pts = []
    for i in range(w):
        ph = (i / w * beats) % 1.0
        v = 0
        if 0.10 < ph < 0.16: v = 0.12 * math.sin((ph - 0.10) / 0.06 * math.pi)
        elif 0.20 < ph < 0.22: v = -0.15
        elif 0.22 < ph < 0.25: v = 1.0
        elif 0.25 < ph < 0.28: v = -0.3
        elif 0.40 < ph < 0.52: v = 0.22 * math.sin((ph - 0.40) / 0.12 * math.pi)
        pts.append((x0 + i, y0 + h * 0.6 - v * h * 0.8))
    if head is None:
        d.line(pts, fill=col, width=width)
    else:
        a = [p for p in pts if p[0] < head]
        b = [p for p in pts if p[0] > head + gap]
        if len(a) > 1: d.line(a, fill=col, width=width)
        if len(b) > 1: d.line(b, fill=col, width=width)


def pill(d, cx, cy, text, font, bg, fg, padx=40, h=None):
    h = h or int(font.size * 2.0)
    tw = d.textlength(text, font=font)
    d.rounded_rectangle((cx - tw / 2 - padx, cy - h / 2, cx + tw / 2 + padx, cy + h / 2), radius=h // 2, fill=bg)
    d.text((cx, cy), text, font=font, fill=fg, anchor="mm")


def chip(d, x, y, text, bg=YELLOW, fg=INK, size=30):
    f = F("ExtraBold", size)
    tw = d.textlength(text, font=f)
    d.rounded_rectangle((x, y, x + tw + 44, y + size + 30), radius=(size + 30) // 2, fill=bg)
    d.text((x + 22, y + (size + 30) / 2), text, font=f, fill=fg, anchor="lm")
    return y + size + 30


# ---------- product mockups (drawn, not generated) ----------

def mockup(img, box, m):
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    t = m.get("type", "meet")
    labels = m.get("labels", [])
    title = m.get("title", "")
    shadow = (0, 0, 0, 90)

    def book(bx, by, bw, bh, cover, txt, accent=LBLUE):
        d.rounded_rectangle((bx + 12, by + 14, bx + bw + 12, by + bh + 14), radius=14, fill=shadow)
        d.rounded_rectangle((bx, by, bx + bw, by + bh), radius=14, fill=cover)
        d.rectangle((bx, by, bx + 18, by + bh), fill=tuple(max(0, c - 30) for c in cover))
        d.rectangle((bx + 18, by + 40, bx + bw, by + 52), fill=accent)
        f, ls, th = fit(txt, "ExtraBold", 40, 18, bw - 60, bh * 0.55, 1.12)
        lines_at(d, bx + 38, by + 80, ls, f, WHITE, 1.12)
        ekg(d, bx + 30, by + bh - 110, bw - 60, 50, accent, 4, beats=2)
        d.text((bx + 38, by + bh - 40), "ANESTHESIA STUDY CO.", font=F("Bold", max(12, int(bw / 22))), fill=accent, anchor="lm")

    if t == "logbook":
        book(x0 + 20, y0 + 20, int(w * 0.48), h - 40, NAVY_L, title or "CLINICAL LOGBOOK")
        px, py, pw, ph = x0 + int(w * 0.44), y0 + 60, int(w * 0.54), h - 100
        d.rounded_rectangle((px + 10, py + 12, px + pw + 10, py + ph + 12), radius=12, fill=shadow)
        d.rounded_rectangle((px, py, px + pw, py + ph), radius=12, fill=WHITE)
        d.rectangle((px, py, px + pw, py + 56), fill=CYAN)
        d.text((px + 20, py + 28), "CASE LOG", font=F("ExtraBold", 26), fill=WHITE, anchor="lm")
        cols = labels or ["Date", "Case", "Airway", "Lines"]
        cw = (pw - 30) / len(cols)
        for i, c in enumerate(cols):
            d.text((px + 18 + i * cw, py + 80), c, font=F("Bold", 18), fill=INK)
        ry = py + 116
        while ry < py + ph - 30:
            d.line([(px + 14, ry), (px + pw - 14, ry)], fill=(200, 210, 225), width=2)
            for i in range(len(cols)):
                if (ry // 38 + i) % 3:
                    d.line([(px + 20 + i * cw, ry - 12), (px + 20 + i * cw + cw * 0.55, ry - 12)], fill=(150, 170, 200), width=3)
            ry += 38
    elif t == "mindmap":
        cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
        labs = (labels or ["Airway", "Drugs", "Monitors", "Physiology", "Machine", "Emergencies"])[:6]
        rx, ry = w * 0.36, h * 0.36
        nodes = []
        for i, lb in enumerate(labs):
            a = -math.pi / 2 + i * 2 * math.pi / len(labs)
            nodes.append((cx + rx * math.cos(a), cy + ry * math.sin(a), lb))
        cols = [CYAN, YELLOW, LBLUE, (255, 140, 120), (150, 230, 170), (200, 170, 255)]
        for (nx, ny, _), c in zip(nodes, cols):
            d.line([(cx, cy), (nx, ny)], fill=c, width=6)
        for (nx, ny, lb), c in zip(nodes, cols):
            f, ls, th = fit(lb, "Bold", 26, 16, 170, 70, 1.1)
            bw = max(PROBE.textlength(x, font=f) for x in ls) + 36
            d.rounded_rectangle((nx - bw / 2, ny - th / 2 - 14, nx + bw / 2, ny + th / 2 + 14), radius=20, fill=c)
            lines_at(d, nx, ny - th / 2, ls, f, INK, 1.1, "c")
        f, ls, th = fit(title or "MIND MAP", "ExtraBold", 34, 18, 230, 120, 1.1)
        d.ellipse((cx - 140, cy - 95, cx + 140, cy + 95), fill=WHITE, outline=CYAN, width=6)
        lines_at(d, cx, cy - th / 2, ls, f, INK, 1.1, "c")
    elif t == "guide":
        for k in (2, 1, 0):
            gx, gy = x0 + 60 + k * 30, y0 + 10 + k * 22
            gw, gh = int(w * 0.72), h - 60
            d.rounded_rectangle((gx + 10, gy + 12, gx + gw + 10, gy + gh + 12), radius=14, fill=shadow)
            d.rounded_rectangle((gx, gy, gx + gw, gy + gh), radius=14, fill=WHITE)
        gx, gy, gw, gh = x0 + 60, y0 + 10, int(w * 0.72), h - 60
        d.rounded_rectangle((gx, gy, gx + gw, gy + 80), radius=14, fill=CYAN)
        d.rectangle((gx, gy + 50, gx + gw, gy + 80), fill=CYAN)
        f, ls, _ = fit(title or "STUDY GUIDE", "ExtraBold", 32, 18, gw - 40, 60, 1.1)
        d.text((gx + 22, gy + 40), ls[0], font=f, fill=WHITE, anchor="lm")
        yy = gy + 110
        for i, lb in enumerate((labels or ["Key concepts", "Drug table", "Practice Qs"])[:4]):
            d.rounded_rectangle((gx + 24, yy, gx + gw - 24, yy + 44), radius=10, fill=(230, 244, 252))
            d.text((gx + 40, yy + 22), lb, font=F("Bold", 24), fill=INK, anchor="lm")
            yy += 60
            for j in range(2):
                d.line([(gx + 40, yy + 10), (gx + gw - 60 - j * 90, yy + 10)], fill=(170, 185, 210), width=4)
                yy += 24
            yy += 14
            if yy > gy + gh - 70:
                break
    elif t == "cards":
        labs = (labels or ["Propofol", "Rocuronium", "Phenylephrine"])[:3]
        cw_, ch_ = int(w * 0.42), int(h * 0.82)
        for i, lb in enumerate(labs):
            card = Image.new("RGBA", (cw_, ch_), (0, 0, 0, 0))
            cd = ImageDraw.Draw(card)
            cd.rounded_rectangle((0, 0, cw_ - 1, ch_ - 1), radius=24, fill=WHITE)
            cd.rounded_rectangle((0, 0, cw_ - 1, 90), radius=24, fill=[CYAN, NAVY_L, (106, 27, 154)][i])
            cd.rectangle((0, 60, cw_ - 1, 90), fill=[CYAN, NAVY_L, (106, 27, 154)][i])
            f, ls, _ = fit(lb, "ExtraBold", 34, 16, cw_ - 40, 60, 1.1)
            cd.text((cw_ // 2, 45), ls[0], font=f, fill=WHITE, anchor="mm")
            yy = 120
            for k, hd in enumerate(["Class", "Onset", "Watch for"]):
                cd.text((24, yy), hd, font=F("Bold", 22), fill=CYAN)
                cd.line([(24, yy + 40), (cw_ - 30 - k * 40, yy + 40)], fill=(170, 185, 210), width=4)
                cd.line([(24, yy + 64), (cw_ - 80, yy + 64)], fill=(170, 185, 210), width=4)
                yy += 110
            rot = card.rotate([12, 0, -12][i], expand=True, resample=Image.BICUBIC)
            px = int(x0 + w / 2 - rot.width / 2 + (i - 1) * w * 0.26)
            py = int(y0 + (h - rot.height) / 2 + [24, 0, 24][i])
            img.alpha_composite(rot, (px, py))
    elif t == "books":
        labs = (labels or ["Anesthesia & Critical Care: Quick Charts", "Trauma Anesthesia Pocket Guide",
                           "Visual Anesthesia Medication Study Cards"])[:3]
        bw = int((w - 80) / 3)
        covers = [NAVY_L, (0, 110, 140), (70, 40, 120)]
        for i, lb in enumerate(labs):
            book(x0 + 10 + i * (bw + 25), y0 + 30 + (i % 2) * 30, bw, h - 90, covers[i], lb)
        d.rounded_rectangle((x0 + w // 2 - 150, y1 - 44, x0 + w // 2 + 150, y1 + 4), radius=24, fill=YELLOW)
        d.text((x0 + w // 2, y1 - 20), title or "ON AMAZON", font=F("ExtraBold", 26), fill=INK, anchor="mm")
    elif t in ("bls", "web"):
        bx0, by0, bx1, by1 = x0 + 20, y0 + 20, x1 - 20, y1 - 20
        d.rounded_rectangle((bx0 + 12, by0 + 14, bx1 + 12, by1 + 14), radius=22, fill=shadow)
        d.rounded_rectangle((bx0, by0, bx1, by1), radius=22, fill=WHITE)
        d.rounded_rectangle((bx0, by0, bx1, by0 + 64), radius=22, fill=(225, 232, 244))
        d.rectangle((bx0, by0 + 40, bx1, by0 + 64), fill=(225, 232, 244))
        for k, c in enumerate([RED, YELLOW, GREEN]):
            d.ellipse((bx0 + 22 + k * 30, by0 + 22, bx0 + 42 + k * 30, by0 + 42), fill=c)
        d.rounded_rectangle((bx0 + 130, by0 + 14, bx1 - 24, by0 + 50), radius=18, fill=WHITE)
        d.text((bx0 + 150, by0 + 32), "anesthesiastudyco.com", font=F("SemiBold", 22), fill=INK, anchor="lm")
        d.rectangle((bx0, by0 + 64, bx1, by0 + 190), fill=NAVY_L)
        f, ls, _ = fit(title or ("BLS + ACLS" if t == "bls" else "ANESTHESIA STUDY CO."), "ExtraBold", 48, 22, bx1 - bx0 - 60, 100, 1.1)
        lines_at(d, (bx0 + bx1) // 2, by0 + 90, ls[:2], f, WHITE, 1.1, "c")
        ekg(d, bx0 + 40, by0 + 200, bx1 - bx0 - 80, 90, RED if t == "bls" else CYAN, 5, beats=3)
        labs = (labels or (["BLS", "ACLS", "Megacode practice", "Algorithms"] if t == "bls"
                           else ["Mind maps", "Study guides", "Blog", "Books"]))[:4]
        tw = (bx1 - bx0 - 70) / 2
        for k, lb in enumerate(labs):
            tx = bx0 + 24 + (k % 2) * (tw + 22)
            ty = by0 + 320 + (k // 2) * 110
            if ty + 90 > by1 - 10:
                break
            d.rounded_rectangle((tx, ty, tx + tw, ty + 90), radius=18, fill=(230, 244, 252))
            f, ls, th = fit(lb, "Bold", 28, 16, tw - 30, 70, 1.1)
            lines_at(d, tx + tw / 2, ty + 45 - th / 2, ls, f, INK, 1.1, "c")
    else:  # meet
        labs = (labels or ["Clinical logbooks", "Study guides", "Mind maps", "Medication cards"])[:4]
        icons = [CYAN, YELLOW, LBLUE, (255, 140, 120)]
        gap = max(16, int(w * 0.05))
        tw, th_ = (w - gap) / 2, (h - gap) / 2
        r = int(min(50, th_ * 0.2))
        for k, lb in enumerate(labs):
            tx, ty = x0 + (k % 2) * (tw + gap), y0 + (k // 2) * (th_ + gap)
            d.rounded_rectangle((tx + 8, ty + 10, tx + tw + 8, ty + th_ + 10), radius=22, fill=shadow)
            d.rounded_rectangle((tx, ty, tx + tw, ty + th_), radius=22, fill=WHITE)
            cy = ty + th_ * 0.08 + r
            d.ellipse((tx + tw / 2 - r, cy - r, tx + tw / 2 + r, cy + r), fill=icons[k])
            ekg(d, int(tx + tw / 2 - r * 0.7), int(cy - r * 0.5), int(r * 1.4), int(r), INK, max(2, r // 12), beats=1)
            ty2 = cy + r + th_ * 0.06
            f, ls, hh = fit(lb, "ExtraBold", 34, 14, tw - 30, ty + th_ - 10 - ty2, 1.1)
            lines_at(d, tx + tw / 2, ty2 + (ty + th_ - 10 - ty2 - hh) / 2, ls, f, INK, 1.1, "c")


# ---------- frame engine ----------

class El:
    def __init__(self, img, delay=0.0, dy=60):
        bb = img.getbbox() or (0, 0, 1, 1)
        self.piece, self.x, self.y = img.crop(bb), bb[0], bb[1]
        self.delay, self.dy = delay, dy


def el(fn, delay=0.0, dy=60):
    ly = layer()
    fn(ly, ImageDraw.Draw(ly))
    return El(ly, delay, dy)


def render(bg, els, t, dyn=None):
    img = bg.copy()
    for e in els:
        p = ease((t - e.delay) / 0.4)
        if p <= 0:
            continue
        pc = e.piece
        if p < 1:
            pc = pc.copy()
            pc.putalpha(pc.getchannel("A").point(lambda v: int(v * p)))
        img.alpha_composite(pc, (e.x, e.y + int((1 - p) * e.dy)))
    if dyn:
        dyn(img, ImageDraw.Draw(img), t)
    return img.convert("RGB")


def segment(bg, els, dur, dyn=None, full=False):
    """Return [(image, seconds)] for one segment: animated entry, then a hold frame."""
    out = []
    end = dur if full else min(dur, max([e.delay for e in els] + [0]) + 0.45)
    n = max(1, int(end * FPS_ANIM))
    for i in range(n):
        out.append((render(bg, els, i / FPS_ANIM, dyn), 1 / FPS_ANIM))
    rest = dur - n / FPS_ANIM
    if rest > 0.01:
        out.append((render(bg, els, dur, dyn), rest))
    return out


# ---------- audio (soft synthesized cues; trending sounds must be added in the TikTok app) ----------

def write_audio(path, total, cues):
    sr = 44100
    n = int(total * sr)
    buf = [0.0] * n
    for t0, freq, dur, vol in cues:
        s0 = int(t0 * sr)
        for i in range(int(dur * sr)):
            if s0 + i >= n:
                break
            env = min(1.0, i / (0.005 * sr)) * math.exp(-i / (dur * sr) * 4)
            buf[s0 + i] += vol * env * math.sin(2 * math.pi * freq * i / sr)
    with wave.open(path, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v)) * 32000)) for v in buf))


def encode(seqs, out, total, cues):
    frames = os.path.join(out, "_frames")
    os.makedirs(frames, exist_ok=True)
    lst = os.path.join(frames, "list.txt")
    with open(lst, "w") as f:
        for i, (im, dur) in enumerate(seqs):
            fn = os.path.join(frames, f"{i:04d}.png"); im.save(fn, compress_level=1)
            f.write(f"file '{fn}'\nduration {dur:.4f}\n")
        f.write(f"file '{fn}'\n")
    wav = os.path.join(frames, "audio.wav")
    write_audio(wav, total, cues)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", wav,
                    "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                    "-c:a", "aac", "-b:a", "128k", "-ac", "2", "-t", f"{total:.2f}", "-movflags", "+faststart",
                    os.path.join(out, "reel.mp4")], check=True)
    for fn in os.listdir(frames):
        os.remove(os.path.join(frames, fn))
    os.rmdir(frames)


# ---------- brand spotlight ----------

BRAND_T = [("hook", 2.2), ("kicker", 1.8), ("points", 7.6), ("where", 1.8), ("outro", 2.6)]
BRAND_KEYS = [1.5, 2.9, 7.8, 10.5, 12.2, 14.5]


def brand(p, out):
    year = p["date"][:4]
    bg = background(p.get("label", "SPOTLIGHT"), year, footer_note=False)
    seqs = []
    m = p.get("mockup", {"type": "meet"})

    # 1 hook + mockup
    def hook(ly, d):
        y = chip(d, L, TOP + 20, p.get("chip", "ANESTHESIA STUDY CO.").upper())
        f, ls, h = fit(p["hook"], "ExtraBold", 92, 52, CW, 420, 1.1)
        lines_at(d, L, y + 34, ls, f, WHITE, 1.1)
    mk = layer(); mockup(mk, (L + 20, 800, R - 20, 1400), m)
    seqs += segment(bg, [el(hook), El(mk, 0.25, 90)], 2.2)
    cover = render(bg, [el(hook), El(mk)], 9)

    # 2 kicker
    def kick(ly, d):
        f, ls, h = fit(p["kicker"], "ExtraBold", 84, 48, CW - 80, 640, 1.15)
        top = (TOP + BOT) // 2 - h // 2 - 60
        d.rounded_rectangle((L, top - 60, R, top + h + 60), radius=40, fill=WHITE)
        d.rectangle((L, top - 60, L + 18, top + h + 60), fill=CYAN)
        lines_at(d, L + 50, top, ls, f, INK, 1.15)
    seqs += segment(bg, [el(kick)], 1.8)

    # 3 points, cumulative
    pts = p["points"]
    assert len(pts) == 3, "brand posts need exactly 3 points"
    small = layer(); mockup(small, (L + 160, 1080, R - 160, 1420), m)

    def ptitle(ly, d):
        chip(d, L, TOP + 20, p.get("points_title", "WHAT'S INSIDE").upper(), CYAN, WHITE)
    pt_els = [el(ptitle)]
    y = TOP + 130
    slot = (1060 - y - 2 * 28) // 3
    size = min(fit(t, "Bold", 54, 30, CW - 150, slot - 50, 1.18)[0].size for t in pts)
    for i, txt in enumerate(pts):
        f, ls, h = fit(txt, "Bold", size, size, CW - 150, slot - 50, 1.18)
        bh = max(h + 50, 130)

        def draw_pt(ly, d, y=y, ls=ls, f=f, bh=bh, h=h, i=i):
            d.rounded_rectangle((L, y, R, y + bh), radius=30, fill=(255, 255, 255, 235))
            d.ellipse((L + 26, y + bh / 2 - 36, L + 98, y + bh / 2 + 36), fill=YELLOW)
            d.text((L + 62, y + bh / 2), str(i + 1), font=F("ExtraBold", 44), fill=INK, anchor="mm")
            lines_at(d, L + 126, y + (bh - h) / 2, ls, f, INK, 1.18)
        pt_els.append(el(draw_pt, delay=[0.0, 2.6, 5.2][i]))
        y += bh + 28
    if y > 1060:
        raise ValueError("points too long: they overlap the mockup. Shorten them.")
    pt_els.append(El(small, 0.3, 40))
    seqs += segment(bg, pt_els[:2] + [pt_els[-1]], 2.6)
    # points 2 and 3 slide in on top of the existing ones
    shown = pt_els[:2] + [pt_els[-1]]
    for k in (2, 3):
        new = pt_els[k]
        new.delay = 0.0
        base = render(bg, shown, 9).convert("RGBA")
        seqs += segment(base, [new], 2.6 if k == 2 else 2.4)
        shown = shown + [new]

    # 4 where to get it
    def where(ly, d):
        f, ls, h = fit(p["where"], "ExtraBold", 60, 34, CW - 80, 260, 1.15)
        top = 1060
        d.rounded_rectangle((L, top, R, top + h + 80), radius=40, fill=YELLOW)
        lines_at(d, (L + R) // 2, top + 40, ls, f, INK, 1.15, "c")
    big = layer(); mockup(big, (L + 40, TOP + 60, R - 40, 1010), m)
    seqs += segment(bg, [El(big, 0, 40), el(where, 0.2)], 1.8)

    # 5 outro
    def outro(ly, d):
        logo = os.path.join(HERE, "brand", "logo.png")
        y = TOP + 120
        if os.path.exists(logo):
            lg = Image.open(logo).convert("RGBA"); lg.thumbnail((260, 260))
            ly.alpha_composite(lg, ((W - lg.width) // 2, y)); y += lg.height + 40
        else:
            d.ellipse((W // 2 - 130, y, W // 2 + 130, y + 260), fill=WHITE)
            ekg(d, W // 2 - 95, y + 95, 190, 80, CYAN, 8, beats=1)
            y += 300
        f, ls, h = fit(p.get("outro", "Organized. Confident. OR-ready."), "ExtraBold", 76, 44, CW, 330, 1.12)
        y = lines_at(d, (L + R) // 2, y, ls, f, WHITE, 1.12, "c") + 50
        pill(d, (L + R) // 2, y + 50, p.get("follow", "FOLLOW @ANESTHESIASTUDYCO"), F("ExtraBold", 40), YELLOW, INK)
        f2, ls2, _ = fit(p.get("tagline", "Daily Quick Cases · anesthesiastudyco.com"), "SemiBold", 36, 24, CW, 100)
        lines_at(d, (L + R) // 2, y + 150, ls2, f2, LBLUE, 1.2, "c")
    seqs += segment(bg, [el(outro)], 2.6)

    total = sum(dur for _, dur in seqs)
    cues = [(0.0, 660, 0.25, 0.10), (2.2, 880, 0.2, 0.08), (4.0, 990, 0.2, 0.08), (6.6, 990, 0.2, 0.08),
            (9.2, 990, 0.2, 0.08), (11.6, 1320, 0.3, 0.08), (13.4, 660, 0.5, 0.10), (13.55, 990, 0.6, 0.08)]
    cover.convert("RGB").save(os.path.join(out, "cover.jpg"), quality=92)
    encode(seqs, out, total, cues)
    return total


# ---------- quick case ----------

CASE_KEYS = [2.0, 4.5, 8.0, 10.5, 14.0, 20.0]


def correct_index(p):
    c = p["correct"]
    return "ABCD".index(c.upper()[0]) if isinstance(c, str) else int(c)


def case(p, out):
    year = p["date"][:4]
    bg = background("QUICK CASE", year)
    vit = p["vitals"][:4]
    ci = correct_index(p)
    hr = next((int(re.sub(r"\D", "", v["value"]) or 70) for v in vit if v["label"].upper() == "HR"
               and re.sub(r"\D", "", v["value"])), 75)
    seqs = []

    # 1 scene: big monitor with live ECG sweep
    mon_top = TOP + (90 if p.get("series") else 30)
    row = 150
    mon_h = 40 + len(vit) * row + 150

    def series(ly, d):
        if p.get("series"):
            chip(d, L, TOP + 16, p["series"].upper())

    def monitor(ly, d):
        d.rounded_rectangle((L, mon_top, R, mon_top + mon_h), radius=30, fill=(4, 8, 20))
        y = mon_top + 30
        for v in vit:
            d.text((L + 44, y + row / 2), v["label"], font=F("Bold", 48), fill=GREY, anchor="lm")
            y += row

    def scene(ly, d):
        f, ls, h = fit(p["scene"], "ExtraBold", 66, 40, CW, BOT - (mon_top + mon_h + 40), 1.15)
        lines_at(d, L, mon_top + mon_h + 40, ls, f, WHITE, 1.15)

    def live(img, d, t):
        y = mon_top + 30
        blink = int(t * 2.5) % 2 == 0
        for v in vit:
            col = (RED if blink else (140, 40, 40)) if v.get("alarm") else GREEN
            f, _, _ = fit(v["value"], "ExtraBold", 104, 50, 420, 140)
            d.text((R - 44, y + row / 2), v["value"], font=f, fill=col, anchor="rm")
            y += row
        head = L + 40 + ((t * 260) % (CW - 80))
        ekg(d, L + 40, mon_top + mon_h - 140, CW - 80, 120, GREEN, 5, beats=max(2, round(hr / 30)), head=head)
    seqs += segment(bg, [el(series), el(monitor), el(scene, 0.35)], 3.2, live, full=True)
    cover = render(bg, [el(series), el(monitor), el(scene)], 9, live)

    # 2 question + options, compact vitals strip
    def strip(ly, d):
        d.rounded_rectangle((L, TOP + 20, R, TOP + 150), radius=24, fill=(4, 8, 20))
        n = len(vit); cw = CW / n
        for i, v in enumerate(vit):
            cx = L + cw * i + cw / 2
            d.text((cx, TOP + 52), v["label"], font=F("Bold", 26), fill=GREY, anchor="mm")
            f, _, _ = fit(v["value"], "ExtraBold", 56, 28, cw - 20, 70)
            d.text((cx, TOP + 108), v["value"], font=f, fill=RED if v.get("alarm") else GREEN, anchor="mm")
    qf, qls, qh = fit(p["question"], "ExtraBold", 76, 46, CW, 260, 1.1)
    qy = TOP + 190

    def question(ly, d):
        lines_at(d, L, qy, qls, qf, YELLOW, 1.1)
    opt_top = qy + qh + 40
    boxes = []
    y = opt_top
    for i, o in enumerate(p["options"]):
        f, ls, h = fit(o, "Bold", 46, 30, CW - 150, 120, 1.12)
        bh = max(110, h + 44)
        boxes.append((y, bh, f, ls, h))
        y += bh + 22
    if y > 1250:
        raise ValueError("options too long: they run into the countdown. Shorten them.")

    def opts(state):
        def fn(ly, d):
            for i, (yy, bh, f, ls, h) in enumerate(boxes):
                bgc, fg, badge = WHITE, INK, CYAN
                if state == "reveal":
                    if i == ci:
                        bgc, fg, badge = GREEN, INK, INK
                    else:
                        bgc, fg, badge = (60, 75, 110), (150, 165, 195), (90, 105, 140)
                d.rounded_rectangle((L, yy, R, yy + bh), radius=26, fill=bgc)
                d.ellipse((L + 22, yy + bh / 2 - 34, L + 90, yy + bh / 2 + 34), fill=badge)
                d.text((L + 56, yy + bh / 2), "ABCD"[i], font=F("ExtraBold", 38), fill=WHITE, anchor="mm")
                lines_at(d, L + 118, yy + (bh - h) / 2, ls, f, fg, 1.12)
        return fn
    o_layer = el(opts("q"), 0.35)
    seqs += segment(bg, [el(strip), el(question, 0.1), o_layer], 3.0)

    # 3 countdown 3-2-1
    qbase = render(bg, [el(strip), el(question), el(opts("q"))], 9).convert("RGBA")

    def count(img, d, t):
        n = 3 - int(t)
        cx, cy, r = (L + R) // 2, 1330, 82
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=NAVY_D, outline=(60, 90, 150), width=10)
        frac = 1 - (t % 1.0)
        d.arc((cx - r, cy - r, cx + r, cy + r), -90, -90 + 360 * frac, fill=YELLOW, width=12)
        d.text((cx, cy), str(max(1, n)), font=F("ExtraBold", 92), fill=WHITE, anchor="mm")
        d.text((L, cy), "COMMENT", font=F("ExtraBold", 34), fill=LBLUE, anchor="lm")
        d.text((L, cy + 42), "YOUR PICK", font=F("ExtraBold", 34), fill=LBLUE, anchor="lm")
    seqs += segment(qbase, [], 3.0, count, full=True)

    # 4 reveal
    def ans_chip(ly, d):
        pill(d, (L + R) // 2, 1330, "ANSWER: " + "ABCD"[ci], F("ExtraBold", 50), GREEN, INK, 50, 110)
    seqs += segment(bg, [el(strip), el(question), el(opts("reveal"), 0, 0), el(ans_chip, 0.1, 30)], 3.0)

    # 5 why
    def why(ly, d):
        head = "ABCD"[ci] + ". " + p["options"][ci]
        hf, hls, hh = fit(head, "ExtraBold", 62, 38, CW - 100, 230, 1.1)
        wf, wls, wh = fit(p["why"], "SemiBold", 50, 34, CW - 100, 760, 1.3)
        h = 96 + 40 + hh + 30 + wh + 60
        top = max(TOP + 20, (TOP + BOT) // 2 - h // 2)
        d.rounded_rectangle((L, top, R, top + h), radius=36, fill=WHITE)
        d.rounded_rectangle((L, top, R, top + 96), radius=36, fill=CYAN)
        d.rectangle((L, top + 60, R, top + 96), fill=CYAN)
        d.text((L + 44, top + 48), "WHY", font=F("ExtraBold", 40), fill=WHITE, anchor="lm")
        y = lines_at(d, L + 50, top + 136, hls, hf, NAVY_L, 1.1) + 30
        lines_at(d, L + 50, y, wls, wf, INK, 1.3)
    seqs += segment(bg, [el(why)], 5.0)

    # 6 pearl + cta
    def pearl(ly, d):
        pf, pls, ph = fit(p["pearl"], "ExtraBold", 66, 40, CW - 100, 520, 1.2)
        h = 96 + 40 + ph + 50
        top = TOP + 120
        d.rounded_rectangle((L, top, R, top + h), radius=36, fill=(255, 248, 204))
        d.rounded_rectangle((L, top, R, top + 96), radius=36, fill=YELLOW)
        d.rectangle((L, top + 60, R, top + 96), fill=YELLOW)
        d.text((L + 44, top + 48), "CLINICAL PEARL", font=F("ExtraBold", 40), fill=INK, anchor="lm")
        y = lines_at(d, L + 50, top + 136, pls, pf, INK, 1.2) + 90
        pill(d, (L + R) // 2, y + 50, p.get("cta", "SAVE FOR YOUR ROTATION").upper(), F("ExtraBold", 44), CYAN, WHITE, 50, 110)
        f2, ls2, _ = fit("Follow @anesthesiastudyco for a new case every night", "SemiBold", 36, 24, CW, 100, 1.2)
        lines_at(d, (L + R) // 2, y + 150, ls2, f2, LBLUE, 1.2, "c")
    seqs += segment(bg, [el(pearl)], 5.0)

    total = sum(dur for _, dur in seqs)
    beat = 60 / max(40, min(150, hr))
    cues = [(k * beat, 880, 0.12, 0.10) for k in range(int(3.2 / beat) + 1)]
    cues += [(6.2, 740, 0.15, 0.09), (7.2, 740, 0.15, 0.09), (8.2, 740, 0.15, 0.09),
             (9.2, 1046, 0.4, 0.10), (9.35, 1318, 0.5, 0.08), (17.2, 880, 0.3, 0.07)]
    cover.convert("RGB").save(os.path.join(out, "cover.jpg"), quality=92)
    encode(seqs, out, total, cues)
    return total


# ---------- checks + contact sheet ----------

def check(p):
    errs = []
    blob = json.dumps(p, ensure_ascii=False)
    for pat in BANNED:
        if re.search(pat, blob):
            errs.append(f"banned name/term {pat}")
    cap = p.get("caption", "")
    if not cap:
        errs.append("missing caption")
    elif len(cap.split("\n")[0]) >= 100:
        errs.append("caption hook line must be under 100 characters")
    if "📚 More: Anesthesia Study Co. on Amazon + anesthesiastudyco.com (link in bio)" not in cap:
        errs.append("caption missing the 📚 More line")
    tags = re.findall(r"#\w+", cap)
    if not 4 <= len(tags) <= 6:
        errs.append(f"caption needs 4-6 hashtags (has {len(tags)})")
    if p["format"] == "case":
        if len(p["options"]) != 4:
            errs.append("case needs 4 options")
        if len(p["why"].split()) > 40:
            errs.append("why is over 40 words")
        if len(p["pearl"].split()) > 14:
            errs.append("pearl is over 14 words")
    if errs:
        raise ValueError(f"{p['date']} {p['format']}: " + "; ".join(errs))


def contact_sheet(built, outdir):
    tw, th = 216, 384
    rows = []
    for date, fmt, out in built:
        keys = BRAND_KEYS if fmt == "brand" else CASE_KEYS
        thumbs = []
        for t in keys:
            fn = os.path.join(out, f"_k{t}.png")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(t), "-i", os.path.join(out, "reel.mp4"),
                            "-frames:v", "1", fn], check=True)
            im = Image.open(fn).convert("RGBA"); os.remove(fn)
            ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
            od.rectangle((0, 0, W, 140), fill=(255, 0, 0, 60))
            od.rectangle((945, 600, W, 1490), fill=(255, 0, 0, 60))
            od.rectangle((0, 1490, W, H), fill=(255, 0, 0, 60))
            im = Image.alpha_composite(im, ov).convert("RGB").resize((tw, th))
            thumbs.append((t, im))
        rows.append((f"{date}  {fmt}", thumbs))
    sheet = Image.new("RGB", (40 + 6 * (tw + 12), 20 + len(rows) * (th + 60)), (245, 246, 250))
    d = ImageDraw.Draw(sheet)
    y = 20
    for label, thumbs in rows:
        d.text((20, y), label, font=F("Bold", 26), fill=INK)
        x = 20
        for t, im in thumbs:
            sheet.paste(im, (x, y + 34)); d.text((x + 4, y + 36), f"{t}s", font=F("Bold", 18), fill=YELLOW)
            x += tw + 12
        y += th + 60
    path = os.path.join(outdir, "contact.jpg")
    sheet.save(path, quality=88)
    return path


def main(spec, outdir):
    if not os.path.exists(spec):
        spec = os.path.join(HERE, spec)
    posts = json.load(open(spec))
    for p in posts:
        check(p)
    built = []
    dates = [p["date"] for p in posts]
    for p in posts:
        name = p["date"] if dates.count(p["date"]) == 1 else f"{p['date']}-{p['format']}"
        out = os.path.abspath(os.path.join(outdir, name)); os.makedirs(out, exist_ok=True)
        total = brand(p, out) if p["format"] == "brand" else case(p, out)
        built.append((p["date"], p["format"], out))
        print(f"built {p['date']} {p['format']} {total:.1f}s")
    print("contact sheet:", contact_sheet(built, outdir))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
