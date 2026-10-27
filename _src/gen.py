"""ASC post generator: carousel slides (1080x1350 PNG) and Quick Case Reels (1080x1920 MP4).
Usage: python3 gen.py posts.json outdir
"""
import json, os, sys, subprocess, textwrap
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
F = lambda w, s: ImageFont.truetype(os.path.join(HERE, "fonts", f"Montserrat-{w}.ttf"), s)
CYAN, PURPLE, NAVY = (0, 188, 212), (106, 27, 154), (20, 24, 58)
YELLOW, WHITE, RED = (255, 214, 0), (255, 255, 255), (229, 57, 53)
FOOT = "© 2026 Anesthesia Study Co. LLC · Teaching reference — not a medical directive."


def gradient(w, h):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=tuple(int(CYAN[i] * (1 - t) + PURPLE[i] * t) for i in range(3)))
    return img


def wrap(d, text, font, maxw):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split():
            test = (cur + " " + word).strip()
            if d.textlength(test, font=font) <= maxw:
                cur = test
            else:
                lines.append(cur); cur = word
        lines.append(cur)
    return lines


def text_block(d, xy, text, font, fill, maxw, gap=1.25):
    x, y = xy
    for ln in wrap(d, text, font, maxw):
        d.text((x, y), ln, font=font, fill=fill)
        y += int(font.size * gap)
    return y


def brand_bar(d, w, h, page=None):
    d.text((60, 50), "ANESTHESIA STUDY CO.", font=F("ExtraBold", 30), fill=WHITE)
    if page:
        d.text((w - 60, 50), page, font=F("SemiBold", 28), fill=WHITE, anchor="ra")
    d.text((w // 2, h - 45), FOOT, font=F("Medium", 20), fill=WHITE, anchor="ms")


def card(img, box, header=None):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(box, radius=36, fill=WHITE)
    x0, y0, x1, _ = box
    if header:
        d.rounded_rectangle((x0, y0, x1, y0 + 96), radius=36, fill=CYAN)
        d.rectangle((x0, y0 + 60, x1, y0 + 96), fill=CYAN)
        d.text((x0 + 44, y0 + 48), header.upper(), font=F("ExtraBold", 38), fill=WHITE, anchor="lm")
        return y0 + 130
    return y0 + 50


def slide(s, idx, n):
    W, H = 1080, 1350
    img = gradient(W, H)
    d = ImageDraw.Draw(img)
    brand_bar(d, W, H, f"{idx}/{n}")
    kind = s.get("kind", "body")
    if kind == "cover":
        y = 230
        if s.get("tag"):
            tw = d.textlength(s["tag"].upper(), font=F("ExtraBold", 30))
            d.rounded_rectangle((60, y, 60 + tw + 48, y + 64), radius=32, fill=YELLOW)
            d.text((84, y + 32), s["tag"].upper(), font=F("ExtraBold", 30), fill=NAVY, anchor="lm")
            y += 110
        y = text_block(d, (60, y), s["title"], F("ExtraBold", 84), WHITE, W - 120, 1.15)
        if s.get("sub"):
            y = text_block(d, (60, y + 30), s["sub"], F("SemiBold", 40), WHITE, W - 120)
        d.text((60, H - 150), "SWIPE  →", font=F("ExtraBold", 40), fill=YELLOW)
    elif kind == "cta":
        y = card(img, (60, 330, W - 60, 1060))
        y = text_block(d, (110, y + 30), s["title"], F("ExtraBold", 76), NAVY, W - 220, 1.12)
        y = text_block(d, (110, y + 30), s.get("body", ""), F("Medium", 48), NAVY, W - 220, 1.3)
        d.rounded_rectangle((110, 900, W - 110, 1010), radius=55, fill=PURPLE)
        d.text((W // 2, 955), s.get("button", "SAVE THIS POST"), font=F("ExtraBold", 42), fill=WHITE, anchor="mm")
    else:
        def body(dd, y):
            if s.get("big"):
                y = text_block(dd, (104, y), s["big"], F("ExtraBold", 76), PURPLE, W - 208, 1.12) + 30
            for b in s.get("bullets", []):
                dd.ellipse((104, y + 22, 128, y + 46), fill=CYAN)
                y = text_block(dd, (150, y), b, F("SemiBold", 50), NAVY, W - 254, 1.2) + 30
            if s.get("body"):
                y = text_block(dd, (104, y), s["body"], F("Medium", 50), NAVY, W - 208, 1.3) + 30
            if s.get("pearl"):
                pf = F("Bold", 46)
                n = len(wrap(dd, "PEARL: " + s["pearl"], pf, W - 268))
                dd.rounded_rectangle((104, y, W - 104, y + n * int(46 * 1.25) + 56), radius=24, fill=(255, 248, 204))
                y = text_block(dd, (134, y + 28), "PEARL: " + s["pearl"], pf, NAVY, W - 268) + 40
            return y
        hdr = 130 if s.get("header") else 50
        h = body(ImageDraw.Draw(Image.new("RGB", (W, 4000))), 0) + hdr + 40
        top = max(170, (H - h) // 2)
        y = card(img, (60, top, W - 60, top + h), s.get("header"))
        body(d, y)
    return img


def reel(p, out):
    """Quick Case: 0-1s scene, 1-5s question, 5-8s pause timer, 8-16s answer, 16-20s pearl."""
    W, H = 1080, 1920
    frames = os.path.join(out, "_frames"); os.makedirs(frames, exist_ok=True)

    def base():
        img = gradient(W, H); d = ImageDraw.Draw(img)
        d.text((60, 70), "ANESTHESIA STUDY CO.", font=F("ExtraBold", 34), fill=WHITE)
        d.text((W - 60, 70), "QUICK CASE", font=F("ExtraBold", 34), fill=YELLOW, anchor="ra")
        d.text((W // 2, H - 60), FOOT, font=F("Medium", 22), fill=WHITE, anchor="ms")
        return img, d

    def monitor(img, d, y0):
        rows = len(p["vitals"])
        h = 60 + rows * 160
        d.rounded_rectangle((60, y0, W - 60, y0 + h), radius=30, fill=(8, 10, 24))
        y = y0 + 40
        for v in p["vitals"]:
            col = RED if v.get("alarm") else (0, 230, 118)
            d.text((110, y + 60), v["label"], font=F("Bold", 50), fill=(150, 160, 190), anchor="lm")
            d.text((W - 110, y + 60), v["value"], font=F("ExtraBold", 110), fill=col, anchor="rm")
            y += 160
        return y0 + h + 50

    def answer_card(img, d, header, parts, top_pad=0):
        probe = ImageDraw.Draw(Image.new("RGB", (W, 4000)))
        def draw(dd, y):
            for txt, font, col, gap in parts:
                y = text_block(dd, (110, y), txt, font, col, W - 220, gap) + 30
            return y
        h = draw(probe, 0) + 170
        top = max(240, (1640 - h) // 2 + top_pad)
        y = card(img, (60, top, W - 60, top + h), header)
        return draw(d, y + 10)

    seqs = []
    # scene
    img, d = base(); y = monitor(img, d, 260)
    text_block(d, (70, y + 20), p["scene"], F("ExtraBold", 74), WHITE, W - 140, 1.15)
    seqs.append((img, 1.5))
    # question + options
    img, d = base(); y = monitor(img, d, 260)
    qy = y
    y = text_block(d, (70, y), p["question"], F("ExtraBold", 80), YELLOW, W - 300, 1.1) + 24
    for i, o in enumerate(p["options"]):
        d.rounded_rectangle((70, y, W - 70, y + 120), radius=28, fill=WHITE)
        d.text((112, y + 60), f"{'ABCD'[i]}   {o}", font=F("Bold", 50), fill=NAVY, anchor="lm")
        y += 140
    q = img
    seqs.append((q, 3.5))
    for t in (3, 2, 1):
        img = q.copy(); d = ImageDraw.Draw(img)
        d.ellipse((W - 220, qy - 20, W - 70, qy + 130), fill=YELLOW)
        d.text((W - 145, qy + 55), str(t), font=F("ExtraBold", 96), fill=NAVY, anchor="mm")
        seqs.append((img, 1.0))
    # answer
    img, d = base()
    answer_card(img, d, "Answer", [(p["answer"], F("ExtraBold", 84), PURPLE, 1.1),
                                    (p["why"], F("SemiBold", 56), NAVY, 1.3)])
    seqs.append((img, 8.0))
    # pearl + cta
    img, d = base()
    y = answer_card(img, d, "Clinical pearl", [(p["pearl"], F("ExtraBold", 66), NAVY, 1.22)], -80)
    d.rounded_rectangle((110, y + 70, W - 110, y + 200), radius=65, fill=YELLOW)
    d.text((W // 2, y + 135), p.get("cta", "SAVE FOR YOUR ROTATION"), font=F("ExtraBold", 46), fill=NAVY, anchor="mm")
    seqs.append((img, 4.0))

    lst = os.path.join(frames, "list.txt")
    with open(lst, "w") as f:
        for i, (im, dur) in enumerate(seqs):
            fn = os.path.join(frames, f"{i:02d}.png"); im.save(fn)
            f.write(f"file '{fn}'\nduration {dur}\n")
        f.write(f"file '{fn}'\n")
    seqs[0][0].save(os.path.join(out, "cover.jpg"), quality=92)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest",
                    "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                    "-c:a", "aac", "-movflags", "+faststart", os.path.join(out, "reel.mp4")], check=True)


def main(spec, outdir):
    posts = json.load(open(spec))
    for p in posts:
        out = os.path.abspath(os.path.join(outdir, p["date"])); os.makedirs(out, exist_ok=True)
        if p["format"] == "carousel":
            for i, s in enumerate(p["slides"], 1):
                slide(s, i, len(p["slides"])).convert("RGB").save(os.path.join(out, f"slide{i}.jpg"), quality=92)
        else:
            reel(p, out)
        print("built", p["date"], p["format"])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
