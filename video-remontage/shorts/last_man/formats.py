"""Three format tests on the 'last man to enter Paradise' story (no audio):

  path       continuous parallax panorama, sand night -> emerald Paradise
  arch       brand frame: golden mihrab arch with geometric pattern, scene inside
  manuscript illuminated-manuscript page, ink drawing reveals, page turn

usage: python3 formats.py FORMAT OUT.mp4 [stills t1,t2]
"""
import math, os, sys, subprocess
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "seven_shade"))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import render_cinema as RC
import characters as C

W, H, FPS = 1080, 1920, 30
rgba, ease, clamp, lerp, eio = RC.rgba, RC.ease, RC.clamp, RC.lerp, RC.eio
GOLD, CREAM = RC.GOLD, RC.CREAM
rng = np.random.default_rng(21)


def mix(a, b, k):
    return tuple(a[i] + (b[i] - a[i]) * k for i in range(len(a)))


# ======================================================================= PATH
HZ = 1150
SAND = dict(top=(22, 18, 16), mid=(54, 40, 32), low=(120, 78, 50), band=(90, 70, 50), mtn=(58, 42, 34), dune=(40, 30, 24), ground=(20, 15, 12))
EMER = dict(top=(5, 16, 18), mid=(12, 44, 46), low=(40, 96, 80), band=(40, 96, 86), mtn=(14, 44, 42), dune=(10, 30, 30), ground=(5, 15, 16))
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)


def make_sky(p):
    g = np.clip(yy / HZ, 0, 1)[..., None]
    top, mid, low = (np.array(p[k], np.float32) for k in ("top", "mid", "low"))
    sky = np.where(g < 0.65, top + (mid - top) * (g / 0.65), mid + (low - mid) * ((g - 0.65) / 0.35))
    band = np.exp(-(((xx * 0.6 + yy * 0.8) - 1000) / 280) ** 2)[..., None]
    sky += band * np.array(p["band"], np.float32) * 0.45
    return np.clip(sky, 0, 255)


SKY_S, SKY_E = make_sky(SAND), make_sky(EMER)
STARS = rng.random((700, 3))
FIRE_GLOW = np.exp(-(((xx - 250) / 700) ** 2 + ((yy - HZ) / 260) ** 2))[..., None] * np.array((170, 60, 20), np.float32)
WORLD = 2.75 * W   # camera travel


def ridge(x, base, amp, f1, f2, ph):
    return base - amp * (0.6 * math.sin(x / W * f1 * math.pi + ph) + 0.4 * math.sin(x / W * f2 * math.pi + ph * 1.7))


def gold_tree(d, x, y, s, a, glow_col=GOLD, leaf=(236, 200, 132)):
    d.polygon([(x - 18 * s, y), (x + 18 * s, y), (x + 8 * s, y - 260 * s), (x - 8 * s, y - 260 * s)], fill=rgba((150, 105, 50), a))
    for dx, dy, r in ((0, -330, 120), (-95, -270, 90), (95, -265, 92), (-50, -410, 80), (60, -415, 78), (0, -230, 70)):
        d.ellipse((x + (dx - r) * s, y + (dy - r) * s, x + (dx + r) * s, y + (dy + r) * s), fill=rgba(leaf, a))
    for i in range(6):  # fruits / sparkles
        ang = i * 1.05
        d.ellipse((x + math.cos(ang) * 80 * s - 7 * s, y - 330 * s + math.sin(ang) * 70 * s - 7 * s,
                   x + math.cos(ang) * 80 * s + 7 * s, y - 330 * s + math.sin(ang) * 70 * s + 7 * s), fill=rgba((255, 245, 210), a))


def gate(d, x, y, a, open_k, light, s=1.0):
    """Golden arched gate; doors swing open revealing light. (x, y) = bottom centre."""
    w, h, fr = 300 * s, 560 * s, 34 * s
    for k in range(8, 0, -1):
        g = k * 22 * s
        d.rounded_rectangle((x - w / 2 - fr - g, y - h - fr - g, x + w / 2 + fr + g, y), radius=int(w / 2 + fr + g), fill=rgba(light, a * 0.014 * (0.3 + open_k)))
    d.rounded_rectangle((x - w / 2 - fr, y - h - fr, x + w / 2 + fr, y), radius=int(w / 2 + fr), fill=rgba(GOLD, a))
    d.rounded_rectangle((x - w / 2, y - h, x + w / 2, y), radius=int(w / 2), fill=rgba(mix(light, (255, 255, 255), 0.55), a))
    dw = (w / 2) * (1 - 0.85 * open_k)
    for sd in (-1, 1):
        x0, x1 = sorted((x + sd * (w / 2 - dw), x + sd * w / 2 if sd > 0 else x - w / 2))
        x0, x1 = (x - w / 2, x - w / 2 + dw) if sd < 0 else (x + w / 2 - dw, x + w / 2)
        top = y - h + w / 2
        d.rectangle((x0, top, x1, y), fill=rgba((150, 105, 50), a))
        if x1 - x0 > 16 * s:
            d.rectangle((x0 + 8 * s, top + 8 * s, x1 - 8 * s, y - 8 * s), outline=rgba(GOLD, a), width=max(2, int(3 * s)))


def path_scene(t, dur, cam=None, hero_x=0.40, caption=True):
    p = eio(t / dur) if cam is None else cam
    camx = p * WORLD
    pal_k = eio((p - 0.55) / 0.35)  # sand -> emerald when reaching the gate
    sky = SKY_S * (1 - pal_k) + SKY_E * pal_k
    fire_k = clamp(1 - p / 0.22)
    sky = sky + FIRE_GLOW * fire_k * (0.8 + 0.2 * math.sin(t * 7))
    frame = Image.fromarray(np.clip(sky, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(frame)
    for sx, sy, sb in STARS:
        x = (sx * W * 1.3 - camx * 0.05) % (W * 1.3)
        y = sy * (HZ - 120)
        b = 0.25 + 0.6 * sb * (0.6 + 0.4 * math.sin(t * 2 + sx * 40))
        d.point((x, y), fill=rgba((255, 248, 230), b))
    pal = {k: mix(SAND[k], EMER[k], pal_k) for k in SAND}
    # supersampled world strip
    Y0, Y1, S = 380, 1360, 2
    lay = Image.new("RGBA", (W * S, (Y1 - Y0) * S), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    fl = Image.new("RGBA", lay.size, (0, 0, 0, 0))
    fd = ImageDraw.Draw(fl)
    def L(x, y): return ((x) * S, (y - Y0) * S)
    for par, base, amp, f1, f2, ph, colk in ((0.15, HZ - 70, 90, 2.2, 5.1, 0.3, "mtn"), (0.45, HZ - 10, 30, 3.0, 7.3, 1.1, "dune")):
        pts = [L(x, ridge(x + camx * par, base, amp, f1, f2, ph)) for x in range(0, W + 9, 8)]
        ld.polygon(pts + [L(W, Y1), L(0, Y1)], fill=rgba(pal[colk], 1))
    gpts = [L(x, ridge(x + camx, HZ + 30, 10, 1.3, 3.1, 2.0)) for x in range(0, W + 9, 8)]
    # world objects (parallax 1.0); world x positions relative to camera
    def sx(wx): return wx - camx
    # fire zone
    if fire_k > 0:
        for i in range(26):
            wx = -200 + i * 32
            x = sx(wx)
            if -60 < x < W + 60:
                h = (70 + 50 * abs(math.sin(t * 6 + i * 1.7))) * (0.6 + 0.4 * ((i * 7) % 3) / 2)
                gy = ridge(wx, HZ + 30, 10, 1.3, 3.1, 2.0)
                ld.polygon([L(x - 22, gy), L(x + 22, gy), L(x + 6 * math.sin(t * 9 + i), gy - h)], fill=rgba((255, 120, 40), 0.85))
                ld.polygon([L(x - 10, gy), L(x + 10, gy), L(x + 3 * math.sin(t * 11 + i), gy - h * 0.55)], fill=rgba((255, 210, 120), 0.9))
    def ground_y(x): return ridge(x + camx, HZ + 30, 10, 1.3, 3.1, 2.0)
    for wx, s, gl in ((1.15 * W, 0.8, GOLD), (1.95 * W, 1.0, (255, 225, 160))):
        x = sx(wx)
        if -400 < x < W + 400:
            gold_tree(ld, x * S, (ground_y(x) - Y0) * S, s * S, 1.0, gl)
    gx = sx(WORLD + 0.66 * W)
    if -400 < gx < W + 400:
        gold_tree(ld, (gx + 250) * S, (ground_y(gx + 250) - Y0) * S, 1.15 * S, 1.0, (200, 255, 220), leaf=(214, 232, 170))
        open_k = eio((p - 0.86) / 0.12)
        gate(ld, gx * S, (ground_y(gx) - Y0) * S, 1.0, open_k, (190, 255, 220), s=S)
        # garden behind / to the right
        for k, ox in enumerate((430, 560, 680)):
            gold_tree(ld, (gx + ox) * S, (ground_y(gx + ox) - Y0) * S, (0.7 - 0.1 * k) * S, 0.9, (150, 240, 200), leaf=(120, 200, 160))
    ld.polygon(gpts + [L(W, Y1), L(0, Y1)], fill=rgba(pal["ground"], 1))
    ld.line(gpts, fill=rgba(GOLD, 0.9), width=4, joint="curve")
    # hero
    hx = W * (hero_x + (0.07 * eio((p - 0.85) / 0.15) if cam is None else 0))
    hy = ground_y(hx)
    if p < 0.1:
        C.figure(fd, hx * S, (hy - Y0) * S, 260 * S, CREAM, 1.0, facing=1, mode="sit", lean=0.75 + 0.1 * math.sin(t * 3),
                 head_down=0.3, front=(1.0, 0.4), back=(0.6, 0.6))
    else:
        C.figure(fd, hx * S, (hy - Y0) * S, 300 * S, CREAM, 1.0, facing=1, mode="walk", phase=t * 3.3, head_down=0.05)
    lay.alpha_composite(C.glow_layer(fl, 1.3))
    frame.alpha_composite(lay.resize((W, Y1 - Y0), Image.LANCZOS), (0, Y0))
    d = ImageDraw.Draw(frame)
    d.rectangle((0, Y1, W, H), fill=rgba(pal["ground"], 1))
    if caption:
        chapters = [(0.0, "ИЗ ОГНЯ", "то идёт, то падает, и огонь обжигает его"), (0.24, "ПЕРВОЕ ДЕРЕВО", "«приблизь меня к нему»"),
                    (0.5, "ВТОРОЕ ДЕРЕВО", "лучше первого — и он снова просит"), (0.78, "У ВОРОТ РАЯ", "«Господи, введи меня туда!»")]
        for i, (p0, title, sub) in enumerate(chapters):
            p1 = chapters[i + 1][0] if i + 1 < len(chapters) else 1.01
            if p0 <= p < p1:
                k = clamp((p - p0) / 0.04) * (1 - clamp((p - (p1 - 0.03)) / 0.03))
                put = RC.put
                put(frame, RC.plain_text(f"{i + 1:02d}", RC.serif(40, 600), GOLD + (255,)), W / 2, 1450, k)
                put(frame, RC.gold_text(title, RC.serif(92, 700), tracking=4), W / 2, 1530, k)
                put(frame, RC.plain_text(sub, RC.F_DESC, (245, 240, 232, 255)), W / 2, 1625, k)
    return frame


# ======================================================================= ARCH
AX0, AX1, AY0, AY1 = 110, 970, 210, 1180   # arch window
ARCH_TOP = AY0 + 250


def arch_shape(x0, x1, y0, ytop, y1, n=60):
    cx = (x0 + x1) / 2
    w = x1 - x0
    pts = [(x0, y1), (x0, ytop)]
    for s in np.linspace(0, 1, n):  # left half: from (x0,ytop) curving to apex (cx,y0)
        a = s * math.pi / 2
        pts.append((x0 + (cx - x0) * (1 - math.cos(a)) ** 0.8, ytop - (ytop - y0) * math.sin(a) ** 1.3))
    for s in np.linspace(1, 0, n):
        a = s * math.pi / 2
        pts.append((x1 - (x1 - cx) * (1 - math.cos(a)) ** 0.8, ytop - (ytop - y0) * math.sin(a) ** 1.3))
    pts += [(x1, ytop), (x1, y1)]
    return pts


def star8(d, x, y, r, fill=None, outline=None, width=1):
    pts = []
    for i in range(16):
        rr = r if i % 2 == 0 else r * 0.62
        a = i * math.pi / 8
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    d.polygon(pts, fill=fill, outline=outline, width=width)


def make_pattern(bg, line):
    im = Image.new("RGBA", (W, H), bg + (255,))
    d = ImageDraw.Draw(im)
    step = 120
    for j in range(-1, H // step + 2):
        for i in range(-1, W // step + 2):
            x, y = i * step + (step / 2 if j % 2 else 0), j * step
            star8(d, x, y, 34, outline=rgba(line, 0.16), width=2)
            d.line((x + 34, y, x + step - 34, y), fill=rgba(line, 0.08), width=2)
    vig = np.clip(1 - 0.6 * (((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2) * 2.2, 0.35, 1)
    arr = np.asarray(im, np.float32)
    arr[..., :3] *= vig[..., None]
    return Image.fromarray(arr.astype(np.uint8))


PATTERN = make_pattern((30, 22, 16), GOLD)
ARCH = arch_shape(AX0, AX1, AY0, ARCH_TOP, AY1)
ARCH_MASK = Image.new("L", (W, H), 0)
ImageDraw.Draw(ARCH_MASK).polygon(ARCH, fill=255)
ARCH_MASK = ARCH_MASK.filter(ImageFilter.GaussianBlur(1))


def arch_frame(t, dur):
    frame = PATTERN.copy()
    # scene inside: the walk towards the gate, camera slowly moving, offset into the arch window
    inner = path_scene(t, dur, cam=lerp(0.86, 0.97, ease(t / dur)), hero_x=0.30 + 0.12 * ease(t / dur), caption=False)
    inner_shift = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    inner_shift.alpha_composite(inner.crop((0, 230, W, H)), (0, 0))
    frame.paste(inner_shift, (0, 0), ARCH_MASK)
    d = ImageDraw.Draw(frame)
    # gold border drawn in progressively
    k = ease(t / 1.6)
    n = max(2, int(len(ARCH) * k))
    for wdt, off, al in ((10, 0, 1.0), (3, 22, 0.8)):
        pts = arch_shape(AX0 - off, AX1 + off, AY0 - off, ARCH_TOP - off * 0.3, AY1 + off)
        d.line(pts[:n], fill=rgba(GOLD, al), width=wdt, joint="curve")
    for x in (AX0 - 11, AX1 + 11):
        for yv in np.arange(ARCH_TOP + 40, AY1, 90):
            star8(d, x, yv, 9 * k, fill=rgba(GOLD, k))
    star8(d, W / 2, AY0 - 40, 20 * k, fill=rgba(GOLD, k))
    RC.put(frame, RC.plain_text("s u n n a", RC.serif(44, 600), GOLD + (255,)), W / 2, 120, ease((t - 0.5) / 0.8))
    ta = ease((t - 1.0) / 0.6)
    RC.put(frame, RC.plain_text("ЧЕТВЁРТАЯ СЦЕНА", RC.F_KICK, GOLD + (255,)), W / 2, 1300, ta)
    RC.put(frame, RC.gold_text("У ВОРОТ РАЯ", RC.serif(104, 700), tracking=4), W / 2, 1390, ta)
    RC.put(frame, RC.plain_text("رَبِّ أَدْخِلْنِيهَا", RC.F_AR, (240, 212, 150, 255), direction="rtl"), W / 2, 1500, ease((t - 1.4) / 0.6))
    RC.put(frame, RC.plain_text("«Господи, введи меня туда!»", RC.F_DESC, (245, 240, 232, 255)), W / 2, 1585, ease((t - 1.7) / 0.6))
    RC.put(frame, RC.plain_text("Муслим 187", RC.F_SRC, (214, 178, 112, 255)), W / 2, 1650, ease((t - 2.0) / 0.6))
    return frame


# ================================================================= MANUSCRIPT
INK = (70, 44, 24)
RED = (160, 52, 30)


def make_parchment():
    base = np.ones((H, W, 3), np.float32) * np.array((232, 214, 176), np.float32)
    n1 = np.asarray(Image.fromarray((rng.random((H // 16, W // 16)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(30)), np.float32) / 255
    n2 = rng.normal(0, 5, (H, W, 1)).astype(np.float32)
    base *= (0.9 + 0.12 * n1)[..., None]
    base += n2
    edge = np.clip((((xx - W / 2) / (W / 2)) ** 4 + ((yy - H / 2) / (H / 2)) ** 4), 0, 1)[..., None]
    base = base * (1 - 0.35 * edge) + np.array((120, 80, 40), np.float32) * 0.35 * edge
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(im)
    for off, wdt, col in ((44, 6, (176, 132, 60)), (60, 2, INK), (72, 2, (176, 132, 60))):
        d.rectangle((off, off, W - off, H - off), outline=rgba(col, 1), width=wdt)
    for x, y in ((58, 58), (W - 58, 58), (58, H - 58), (W - 58, H - 58)):
        star8(d, x, y, 34, fill=rgba((196, 150, 70), 1), outline=rgba(INK, 1), width=2)
        star8(d, x, y, 14, fill=rgba((240, 220, 170), 1))
    for x in np.arange(150, W - 100, 80):
        star8(d, x, 58, 8, fill=rgba((176, 132, 60), 1)); star8(d, x, H - 58, 8, fill=rgba((176, 132, 60), 1))
    return im


PARCH = make_parchment()
PANEL = (140, 330, 940, 1110)


def flame(d, x, gy, w, h, sway, fill, outline):
    pts = []
    for k in range(21):  # teardrop: wide rounded base, curling tip
        u = k / 20
        half = w * math.sin(math.pi * min(1, u * 1.35) ** 0.7) * (1 - u) ** 0.6
        pts.append((x - half + sway * w * 0.6 * u ** 2, gy - h * u))
    for k in range(20, -1, -1):
        u = k / 20
        half = w * math.sin(math.pi * min(1, u * 1.35) ** 0.7) * (1 - u) ** 0.6
        pts.append((x + half + sway * w * 0.6 * u ** 2, gy - h * u))
    d.polygon(pts, fill=rgba(fill, 0.95), outline=rgba(outline, 1) if outline else None, width=3)


def ink_page(t, page):
    im = PARCH.copy()
    S = 2
    pw, ph = PANEL[2] - PANEL[0], PANEL[3] - PANEL[1]
    lay = Image.new("RGBA", (pw * S, ph * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    gy = ph * 0.82 * S
    d.line((0, gy, pw * S, gy), fill=rgba(INK, 0.9), width=4)
    for i in range(12):  # ink hatching on the ground
        x = (i * 70 + 20) * S
        d.line((x, gy + 14 * S, x + 30 * S, gy + 14 * S), fill=rgba(INK, 0.5), width=3)
    if page == 0:
        for i in range(9):
            x = (50 + i * 58) * S
            h = (120 + 110 * math.sin(i / 8 * math.pi) + 30 * math.sin(t * 5 + i * 1.3)) * S
            flame(d, x, gy, 46 * S, h, math.sin(t * 6 + i * 2.1), (214, 96, 40), INK)
            flame(d, x, gy, 24 * S, h * 0.55, math.sin(t * 7 + i), (240, 180, 80), None)
        C.figure(d, 620 * S, gy, 280 * S, INK, 1.0, facing=1, mode="sit", lean=0.8, head_down=0.3, front=(1.0, 0.4), back=(0.6, 0.6))
    else:
        for k, (x, s) in enumerate(((160, 0.55), (390, 0.7), (640, 0.9))):
            q = ease((t - 0.3 - k * 0.6) / 0.8)
            if q <= 0: continue
            tx, sc = x * S, s * S * q
            d.polygon([(tx - 14 * sc, gy), (tx + 14 * sc, gy), (tx + 6 * sc, gy - 220 * sc), (tx - 6 * sc, gy - 220 * sc)], fill=rgba(INK, 1))
            for dx, dy, r in ((0, -280, 110), (-85, -225, 80), (85, -220, 82), (0, -380, 80)):
                d.ellipse((tx + (dx - r) * sc, gy + (dy - r) * sc, tx + (dx + r) * sc, gy + (dy + r) * sc), fill=rgba((196, 150, 70), 1), outline=rgba(INK, 1), width=4)
        C.figure(d, 70 * S, gy, 260 * S, INK, 1.0, facing=1, mode="walk", phase=t * 3)
    lay = lay.resize((pw, ph), Image.LANCZOS)
    # reveal: ink "draws in" from left to right with a soft edge
    rv = ease(t / 1.8)
    m = np.clip((np.arange(pw)[None, :] - (rv * (pw + 200) - 200)) / -200, 0, 1) * np.ones((ph, 1))
    al = np.asarray(lay.getchannel("A"), np.float32) * m
    lay.putalpha(Image.fromarray(al.astype(np.uint8)))
    d2 = ImageDraw.Draw(im)
    d2.rectangle(PANEL, outline=rgba(INK, 1), width=3)
    d2.rectangle((PANEL[0] - 12, PANEL[1] - 12, PANEL[2] + 12, PANEL[3] + 12), outline=rgba((176, 132, 60), 1), width=2)
    im.alpha_composite(lay, (PANEL[0], PANEL[1]))
    title, ar, line = (("ИЗ ОГНЯ", "تَبَارَكَ الَّذِي نَجَّانِي مِنْكِ", "«Благословен Тот, Кто спас меня от тебя!»") if page == 0 else
                       ("ТРИ ДЕРЕВА", "أَيْ رَبِّ أَدْنِنِي مِنْ هَذِهِ الشَّجَرَةِ", "каждое лучше прежнего — и он снова просит"))
    def write(img, cy, k):  # writing reveal left->right
        if k <= 0: return
        img = img.copy()
        a = np.asarray(img.getchannel("A"), np.float32)
        wv = int(img.width * k)
        a[:, wv:] = 0
        img.putalpha(Image.fromarray(a.astype(np.uint8)))
        im.alpha_composite(img, (int(W / 2 - img.width / 2), int(cy - img.height / 2)))
    write(RC.plain_text(f"{page + 1:02d}", RC.serif(48, 600), (176, 132, 60, 255)), 230, ease((t - 0.2) / 0.5))
    write(RC.plain_text(title, RC.serif(110, 700), INK + (255,)), 1240, ease((t - 0.8) / 0.9))
    write(RC.plain_text(ar, ImageFont.truetype(os.path.join(RC.FONTS, "AmiriQuran-Regular.ttf"), 54), RED + (255,), direction="rtl"), 1390, ease((t - 1.5) / 0.9))
    write(RC.plain_text(line, ImageFont.truetype(os.path.join(RC.FONTS, "CormorantGaramond[wght].ttf"), 52), INK + (255,)), 1490, ease((t - 2.1) / 1.0))
    write(RC.plain_text("Сахих Муслим 187", RC.serif(38, 600), (150, 110, 50, 255)), 1580, ease((t - 2.8) / 0.6))
    return im


def manuscript_frame(t, dur):
    turn_t, turn_d = 6.0, 1.1
    if t < turn_t:
        return ink_page(t, 0)
    k = eio((t - turn_t) / turn_d)
    old = ink_page(turn_t, 0)
    new = ink_page(max(0, t - turn_t - turn_d * 0.6), 1)
    if k >= 1:
        return new
    # page turn: new page slides in from the right with a fold shadow and highlight
    x = int(W * (1 - k))
    frame = old.copy()
    sh = np.zeros((H, 160, 4), np.uint8)
    sh[..., 3] = (np.linspace(0, 150, 160)[None, :] * (1 - k)).astype(np.uint8)
    frame.alpha_composite(Image.fromarray(sh), (max(0, x - 160), 0))
    frame.paste(new.crop((0, 0, W - x, H)), (x, 0))
    hl = np.zeros((H, 60, 4), np.uint8)
    hl[..., :3] = 255
    hl[..., 3] = (np.linspace(120, 0, 60)[None, :] * (1 - k)).astype(np.uint8)
    frame.alpha_composite(Image.fromarray(hl), (min(W - 60, x), 0))
    return frame


# ================================================================== RENDER
FORMATS = {"path": (path_scene, 16.0), "arch": (arch_frame, 10.0), "manuscript": (manuscript_frame, 12.0)}


def chunk(args):
    fmt, a0, a1, path = args
    fn, dur = FORMATS[fmt]
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for fi in range(a0, a1):
        p.stdin.write(fn(fi / FPS, dur).convert("RGB").tobytes())
    p.stdin.close(); p.wait()
    return path


if __name__ == "__main__":
    fmt, out = sys.argv[1], sys.argv[2]
    fn, dur = FORMATS[fmt]
    if len(sys.argv) > 3 and sys.argv[3] == "stills":
        for tt in [float(x) for x in sys.argv[4].split(",")]:
            fn(tt, dur).convert("RGB").save(f"{out}_{tt:05.2f}.jpg", quality=88)
        sys.exit()
    nf = int(dur * FPS)
    step = math.ceil(nf / 4)
    jobs = [(fmt, i * step, min(nf, (i + 1) * step), f"{out}.part{i}.mp4") for i in range(4)]
    with Pool(4) as pool:
        parts = pool.map(chunk, jobs)
    lst = out + ".list.txt"
    with open(lst, "w") as f:
        for p_ in parts: f.write(f"file '{os.path.abspath(p_)}'\n")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", out], check=True)
    for p_ in parts: os.remove(p_)
    os.remove(lst)
    print("done", out)
