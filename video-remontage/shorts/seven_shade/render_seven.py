"""Short: "7 people in the shade of Allah" (Bukhari 660, Muslim 1031).

Reuses the engine in ../../render.py (palette, background, subtitles, titles).
Timing comes from timings.json if present ({"segments": [[start, end], ...]},
one pair per SEGMENTS entry, seconds), otherwise from a reading-pace estimate.

usage: python3 render_seven.py OUT_DIR [stills t1,t2,...]
"""
import json, math, os, sys, subprocess
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
os.environ.setdefault("PALETTE", "ocean")
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import render as R

W, H, FPS = R.W, R.H, R.FPS
FD = R.FD
WARM = (255, 210, 150)

# id, title, icon, voice text, accent words, numbered index (0 = none)
SEGMENTS = [
    ("hook", "Судный день", "sun",
     "В Судный день солнце приблизится к людям. И не будет никакой тени — кроме тени Аллаха.",
     ["солнце", "тени", "Аллаха."], 0),
    ("q", "Ты среди них?", "canopy",
     "Пророк, мир ему, назвал семерых, кого Аллах укроет в Своей тени в тот день. Ты среди них?",
     ["семерых,", "них?"], 0),
    ("1", "Справедливый правитель", "scales", "Первый — справедливый правитель.", ["справедливый"], 1),
    ("2", "Юноша в поклонении", "sprout", "Второй — юноша, который вырос в поклонении Аллаху.", ["поклонении"], 2),
    ("3", "Сердце в мечети", "mosque", "Третий — человек, чьё сердце привязано к мечетям.", ["сердце", "мечетям."], 3),
    ("4", "Любовь ради Аллаха", "two",
     "Четвёртый — двое, которые полюбили друг друга ради Аллаха: ради Него встретились и ради Него расстались.",
     ["полюбили", "встретились", "расстались."], 4),
    ("5", "«Я боюсь Аллаха»", "turn",
     "Пятый — мужчина, которого позвала к себе знатная и красивая женщина, а он сказал: «Я боюсь Аллаха».",
     ["«Я", "боюсь", "Аллаха»."], 5),
    ("6", "Тайная милостыня", "hands",
     "Шестой — тот, кто подал милостыню так скрытно, что его левая рука не знала, что раздала правая.",
     ["скрытно,", "левая", "правая."], 6),
    ("7", "Слёзы наедине", "eye",
     "Седьмой — тот, кто вспомнил Аллаха в уединении, и его глаза наполнились слезами.",
     ["уединении,", "слезами."], 7),
    ("src", "Достоверный хадис", "book",
     "Этот хадис передал Абу Хурайра, его приводят аль-Бухари и Муслим.", ["аль-Бухари", "Муслим."], 0),
    ("cta", "Стань одним из семерых", "canopy_full",
     "Старайся стать одним из семерых. И отправь это тому, кого любишь ради Аллаха.",
     ["семерых.", "любишь"], 8),
]


def estimate_timings():
    t, out = 0.4, []
    for seg in SEGMENTS:
        d = len(seg[3]) / 13.5 + 0.3
        out.append([t, t + d])
        t += d + 0.55
    return out


TP = os.path.join(HERE, "timings.json")
TIMES = json.load(open(TP))["segments"] if os.path.exists(TP) and not os.environ.get("SEVEN_NO_TIMINGS") else estimate_timings()
DUR = TIMES[-1][1] + 1.6
NF = int(DUR * FPS)
# scene boundaries: each scene runs from its speech start (minus lead) to next speech start
SCENES = []
for i, (seg, (s0, s1)) in enumerate(zip(SEGMENTS, TIMES)):
    a = 0.0 if i == 0 else TIMES[i][0] - 0.25
    b = TIMES[i + 1][0] - 0.25 if i + 1 < len(TIMES) else DUR + 1
    SCENES.append((a, b, seg))


def chunk_subs():
    subs = []
    for seg, (s0, s1) in zip(SEGMENTS, TIMES):
        words = seg[3].split()
        # split long lines into <= ~11-word chunks at punctuation when possible
        chunks, cur = [], []
        for w in words:
            cur.append(w)
            if len(" ".join(cur)) > 58 and w[-1] in ",.:?—»" or len(cur) >= 12:
                chunks.append(cur); cur = []
        if cur:
            if chunks and len(cur) <= 2: chunks[-1] += cur
            else: chunks.append(cur)
        tot = sum(len(" ".join(c)) for c in chunks)
        t = s0
        for c in chunks:
            d = (s1 - s0) * len(" ".join(c)) / tot
            subs.append((t, t + d - 0.04, " ".join(c), seg[4]))
            t += d
    return subs


R.SUBS = chunk_subs()
R.SUB_Y = 1520

F_NUM = ImageFont.truetype(FD + "InterDisplay-Bold.otf", 560)
F_OVER = ImageFont.truetype(FD + "Inter-SemiBold.otf", 30)
SS, IW = R.SS, R.IW
col, ease, clamp, lerp = R.col, R.ease, R.clamp, R.lerp
LINE, ACC = R.LINE, R.GOLD
CARD, SHADOW = R.CARD, R.PAL["shadow"]

# Calm palette per scene: bg top, bg bottom, accent, glow
SCENE_PAL = {
    "hook": ((40, 31, 30), (14, 12, 14), (240, 202, 150), (96, 64, 42)),     # warm dusk
    "q":    ((18, 32, 40), (9, 17, 23), (128, 198, 184), (40, 84, 88)),      # deep teal
    "1":    ((22, 30, 48), (10, 14, 26), (156, 184, 232), (44, 62, 104)),    # slate blue
    "2":    ((22, 34, 28), (10, 16, 13), (172, 212, 160), (50, 86, 60)),     # sage
    "3":    ((18, 30, 44), (8, 13, 23), (140, 204, 212), (38, 78, 96)),      # lagoon
    "4":    ((40, 26, 36), (16, 11, 17), (232, 176, 194), (92, 52, 74)),     # dusty rose
    "5":    ((28, 26, 48), (12, 11, 24), (192, 174, 232), (66, 58, 108)),    # night violet
    "6":    ((36, 32, 24), (14, 13, 10), (226, 202, 152), (86, 72, 46)),     # warm sand
    "7":    ((16, 28, 46), (7, 13, 24), (144, 194, 238), (36, 64, 106)),     # ocean blue
    "src":  ((24, 30, 34), (11, 14, 16), (196, 214, 204), (56, 70, 72)),     # misty grey
    "cta":  ((34, 29, 48), (14, 12, 22), (238, 204, 172), (90, 68, 92)),     # dawn
}


def mix(c0, c1, k):
    return tuple(c0[i] + (c1[i] - c0[i]) * k for i in range(3))


def palette_at(si, lt):
    cur = SCENE_PAL[SEGMENTS[si][0]]
    if si == 0:
        return cur
    prev = SCENE_PAL[SEGMENTS[si - 1][0]]
    k = R.ease_io(lt / 0.9)
    return tuple(mix(a, b, k) for a, b in zip(prev, cur))


def apply_palette(pal):
    global ACC, LINE, CARD, SHADOW
    bg0, bg1, acc, glow = pal
    ACC = tuple(int(v) for v in acc)
    LINE = tuple(int(v) for v in mix(mix(acc, (205, 205, 205), 0.4), (0, 0, 0), 0.18))
    CARD = tuple(int(v) for v in mix(bg0, (255, 255, 255), 0.06))
    SHADOW = tuple(int(v) for v in mix(bg0, (255, 255, 255), 0.28))
    R.GOLD, R.LINE, R.CARD = ACC, LINE, CARD
    R.INK_ON_ACC = tuple(int(v) for v in bg1)
    R.PAL["bg1"] = R.INK_ON_ACC


GRAD = (R.yy[:, :1] / H)[..., None]  # (H,1,1)


def background(t, pal, glow_k):
    bg0, bg1, acc, glow = (np.array(c, np.float32) for c in pal)
    img = bg0 * (1 - GRAD) + bg1 * GRAD                      # (H,1,3) -> broadcast
    img = np.broadcast_to(img, (H, W, 3)).copy()
    m1 = np.clip(R.GLOW * 0.75 * glow_k, 0, 1)
    img = img * (1 - m1) + glow * m1
    m2 = np.clip(R.GLOW2 * 0.3, 0, 1)
    img = img * (1 - m2) + (glow * 0.6 + bg0 * 0.4) * m2
    img = img * R.VIG
    gr = R.GRAIN[int(t * 15) % 6]
    img += np.repeat(np.repeat(gr, 2, 0), 2, 1)[..., None]
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")


BOKEH = np.random.default_rng(11).random((14, 5))


def bokeh(frame, t):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for bx, by, sp, sz, ph in BOKEH:
        x = (bx * W + 40 * math.sin(t * 0.15 + ph * 6)) % W
        y = (by * H - t * (6 + 10 * sp)) % H
        r = 30 + 70 * sz
        tw = 0.5 + 0.5 * math.sin(t * 0.6 + ph * 9)
        for k in range(4, 0, -1):
            rr = r * k / 4
            d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=col(ACC, 0.018 * tw))
    frame.alpha_composite(lay)


def gdot(d, x, y, rad, a):
    R.glow_dot(d, x, y, rad, a, core=ACC)


def arc_pts(cx, cy, rx, ry, a0, a1, n=80):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


import characters as C

USE_CHARS = os.environ.get("CHARS", "1") != "0"
CHAR_KINDS = {"sun", "canopy", "canopy_full", "scales", "sprout", "mosque", "two", "turn", "hands", "eye"}


def crescent(lay, cx, cy, r, color, a):
    m = Image.new("L", (int(2 * r) + 4, int(2 * r) + 4), 0)
    md = ImageDraw.Draw(m)
    md.ellipse((2, 2, 2 * r + 2, 2 * r + 2), fill=int(255 * a))
    md.ellipse((2 - 0.42 * r, 2 - 0.12 * r, 2 * r + 2 - 0.42 * r, 2 * r + 2 - 0.12 * r), fill=0)
    solid = Image.new("RGBA", m.size, tuple(int(v) for v in color) + (255,))
    solid.putalpha(m)
    lay.alpha_composite(solid, (int(cx - r - 2), int(cy - r - 2)))


def draw_chars(kind, lt, dur, a):
    S = IW * SS
    lay = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    fl = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d, fd = ImageDraw.Draw(lay), ImageDraw.Draw(fl)
    c, u = S / 2, SS
    lw = int(2.4 * u)
    ph = clamp(lt / max(dur, 0.1))
    FIG = tuple(int(v) for v in mix(ACC, (255, 250, 240), 0.55))
    DIM = tuple(int(v) for v in mix(LINE, (0, 0, 0), 0.25))
    ground = c + 260 * u

    if kind == "sun":
        y = c - 200 * u + (1 - ease(lt / 3.5)) * -50 * u
        rad = (85 + 25 * ease(lt / 3.5)) * u
        for k in range(8, 0, -1):
            rr = rad * (1 + k * 0.13)
            d.ellipse((c - rr, y - rr, c + rr, y + rr), fill=col(WARM, a * 0.04))
        d.ellipse((c - rad, y - rad, c + rad, y + rad), fill=col(WARM, a))
        for k in range(3):
            f = (lt * 0.5 + k / 3) % 1
            rr = rad * (1.1 + 1.0 * f)
            d.ellipse((c - rr, y - rr, c + rr, y + rr), outline=col(WARM, a * (1 - f) * 0.5), width=lw)
        hz = ground + 40 * u
        d.line((c - 440 * u, hz, c + 440 * u, hz), fill=col(LINE, a * 0.5), width=lw)
        for i in range(9):
            x = c + (i - 4) * 98 * u
            sway = 0.05 * math.sin(lt * 1.2 + i)
            arms = C.ARMS_SHADE if i % 3 == 0 else C.ARMS_DOWN
            C.figure(fd, x, hz, (175 + 12 * ((i * 5) % 3)) * u, DIM, a * 0.9, facing=1 if i % 2 else -1,
                     lean=sway, head_down=0.0 if i % 3 == 0 else 0.35, front=arms[0], back=arms[1])
        lay.alpha_composite(C.glow_layer(fl, 0.5))
        return lay.resize((IW, IW), Image.LANCZOS)

    if kind in ("canopy", "canopy_full"):
        full = kind == "canopy_full"
        top = c - 330 * u
        arcw, arch = 330 * u * ease(lt / 0.9), 230 * u
        for k in range(6, 0, -1):
            pts = arc_pts(c, top + arch, arcw * (1 + k * 0.06), arch * (1 + k * 0.08), math.pi, 2 * math.pi)
            d.polygon(pts + [(c + arcw, ground), (c - arcw, ground)], fill=col(ACC, a * 0.03))
        d.line(arc_pts(c, top + arch, arcw, arch, math.pi, 2 * math.pi), fill=col(ACC, a), width=int(3 * u), joint="curve")
        gdot(d, c, top + 10 * u, 22 * u, a)
        if full:
            for i in range(28):
                ang = math.pi + math.pi * (i + 0.5) / 28
                l0, l1 = arch * 1.08, arch * (1.3 + 0.15 * math.sin(lt * 2 + i))
                d.line((c + l0 * 1.35 * math.cos(ang), top + arch + l0 * math.sin(ang),
                        c + l1 * 1.35 * math.cos(ang), top + arch + l1 * math.sin(ang)), fill=col(ACC, a * 0.4), width=int(2 * u))
        shown = 7 if full else clamp((lt - 0.8) / 2.6) * 7
        for i in range(7):
            q = 1.0 if full else clamp(shown - i)
            if q <= 0:
                continue
            x = c + (i - 3) * 92 * u
            arms = C.ARMS_DUA if full else C.ARMS_DOWN
            C.figure(fd, x, ground - (1 - ease(q)) * 30 * u + (4 * u * math.sin(lt * 2 + i) if full else 0),
                     (170 + 14 * (i % 2)) * u, FIG, a * ease(q), facing=1 if i < 3 else -1,
                     head_down=0.1, front=arms[0], back=arms[1])
        if not full:
            for i in range(10):
                side = -1 if i % 2 else 1
                x = c + side * (300 + 30 * (i // 2)) * u
                yb = ground + (70 + 25 * (i // 2)) * u
                C.figure(d, x, yb, 120 * u, DIM, a * 0.35, facing=-side, head_down=0.4)
        lay.alpha_composite(C.glow_layer(fl, 1.3))
        return lay.resize((IW, IW), Image.LANCZOS)

    if kind == "scales":
        ang = 0.28 * math.exp(-lt * 0.9) * math.cos(lt * 3.2)
        top, L = c - 360 * u, 170 * u
        d.line((c, top - 30 * u, c, top + 30 * u), fill=col(LINE, a), width=lw)
        gdot(d, c, top - 40 * u, 12 * u, a)
        for side in (-1, 1):
            ex, ey = c + side * L * math.cos(ang), top + side * L * math.sin(ang)
            d.line((c, top, ex, ey), fill=col(LINE, a), width=lw)
            py = ey + 95 * u
            d.line((ex, ey, ex - 45 * u, py), fill=col(LINE, a * 0.7), width=int(2 * u))
            d.line((ex, ey, ex + 45 * u, py), fill=col(LINE, a * 0.7), width=int(2 * u))
            d.chord((ex - 60 * u, py - 22 * u, ex + 60 * u, py + 22 * u), 0, 180, fill=col(CARD, a), outline=col(ACC, a), width=lw)
        d.rounded_rectangle((c - 130 * u, ground - 40 * u, c + 130 * u, ground), 10 * u, fill=col(CARD, a), outline=col(LINE, a * 0.7), width=lw)
        C.figure(fd, c, ground - 40 * u, 320 * u, FIG, a, facing=1, front=(1.15, 0.25), back=(-1.15, -0.25))
        for side in (-1, 1):
            C.figure(fd, c + side * 320 * u, ground + 30 * u, 230 * u, FIG, a * 0.85, facing=-side, head_down=0.1)
            f = (lt * 0.45) % 1
            hx0, hy0 = C.hand_pos(c, ground - 40 * u, 320 * u, 1, 0, (1.15, 0.25) if side > 0 else (-1.15, -0.25))
            tx, ty = c + side * 300 * u, ground - 120 * u
            gdot(d, lerp(hx0, tx, ease(f)), lerp(hy0, ty, ease(f)) - math.sin(f * math.pi) * 60 * u, 12 * u, a * (1 - f * 0.6))
        lay.alpha_composite(C.glow_layer(fl, 1.3))
        return lay.resize((IW, IW), Image.LANCZOS)

    if kind == "sprout":
        g = ease(lt / max(dur * 0.7, 1))
        h = (220 + 90 * g) * u
        x = c - 70 * u
        d.rounded_rectangle((c - 260 * u, ground - 6 * u, c + 200 * u, ground + 10 * u), 8 * u, fill=col(CARD, a), outline=col(ACC, a * 0.5), width=int(2 * u))
        arch = arc_pts(c + 280 * u, c - 120 * u, 110 * u, 150 * u, math.pi, 2 * math.pi)
        d.line(arch + [(c + 390 * u, ground), (c + 170 * u, ground), arch[0]], fill=col(LINE, a * 0.5), width=lw)
        C.figure(fd, x, ground, h, FIG, a, facing=1, mode="sit", lean=0.12, head_down=0.35, front=C.ARMS_READ[0], back=C.ARMS_READ[1])
        bx, by = C.hand_pos(x, ground, h, 1, 0.12, C.ARMS_READ[0], mode="sit")
        bw = 0.13 * h
        for side in (-1, 1):
            d.polygon([(bx, by - 0.02 * h), (bx + side * bw, by - 0.06 * h), (bx + side * bw, by + 0.05 * h), (bx, by + 0.07 * h)],
                      fill=col(CARD, a), outline=col(ACC, a))
        for k in range(8):
            f = (lt * 0.35 + k / 8) % 1
            px = bx + 40 * u * math.sin(k * 2.1 + lt) * f
            gdot(d, px, by - 20 * u - 380 * u * f, (7 - 4 * f) * u, a * (1 - f))
        lay.alpha_composite(C.glow_layer(fl, 1.3))
        return lay.resize((IW, IW), Image.LANCZOS)

    if kind == "mosque":
        mx, bw = c - 205 * u, 130 * u
        d.line((mx - bw, ground, mx + bw, ground), fill=col(LINE, a), width=lw)
        for sx in (-1, 1):
            d.line((mx + sx * bw * 0.8, ground, mx + sx * bw * 0.8, c - 20 * u), fill=col(LINE, a), width=lw)
        d.line(arc_pts(mx, c - 20 * u, bw * 0.8, 150 * u, math.pi, 2 * math.pi), fill=col(ACC, a), width=int(3 * u), joint="curve")
        d.line((mx, c - 170 * u, mx, c - 215 * u), fill=col(ACC, a), width=lw)
        d.line((mx - bw - 30 * u, ground, mx - bw - 30 * u, c - 160 * u), fill=col(LINE, a * 0.8), width=lw)
        d.polygon([(mx - bw - 45 * u, c - 160 * u), (mx - bw - 15 * u, c - 160 * u), (mx - bw - 30 * u, c - 215 * u)], outline=col(LINE, a * 0.8))
        d.rounded_rectangle((mx - 45 * u, ground - 120 * u, mx + 45 * u, ground), 45 * u, outline=col(LINE, a * 0.8), width=lw)
        x = c + lerp(110, 270, ph) * u
        info = C.figure(fd, x, ground, 300 * u, FIG, a, facing=1, mode="walk", phase=lt * 3.2, head_down=0.05)
        hx, hy = info["chest"]
        dome = (mx, c - 175 * u)
        pts = []
        for i in range(41):
            s_ = i / 40
            px = lerp(hx, dome[0], s_)
            py = lerp(hy, dome[1], s_) - math.sin(s_ * math.pi) * 170 * u
            pts.append((px, py))
        d.line(pts, fill=col(ACC, a * 0.55), width=int(2 * u), joint="curve")
        for k in range(3):
            s_ = (lt * 0.3 + k / 3) % 1
            gdot(d, *pts[int(s_ * 40)], 8 * u, a * 0.9)
        hb = 1 + 0.18 * abs(math.sin(lt * 3.4))
        gdot(fd, hx, hy, 15 * u * hb, a)
        lay.alpha_composite(C.glow_layer(fl, 1.3))
        return lay.resize((IW, IW), Image.LANCZOS)

    if kind == "two":
        h = 290 * u
        if ph < 0.35:
            k = ease(ph / 0.35); off = lerp(330, 82, k); facing_in = True; walking = True; arm = C.ARMS_DOWN
        elif ph < 0.62:
            off = 82; facing_in = True; walking = False
            r_ = ease((ph - 0.35) / 0.08)
            arm = ((lerp(0.12, 1.2, r_), lerp(0.08, 0.15, r_)), (-0.1, 0.06))
        else:
            k = ease((ph - 0.62) / 0.38); off = lerp(82, 300, k); facing_in = False; walking = True; arm = C.ARMS_DOWN
        chests = []
        for side in (-1, 1):
            fcg = -side if facing_in else side
            info = C.figure(fd, c + side * off * u, ground, h, FIG, a, facing=fcg, mode="walk" if walking else "stand",
                            phase=lt * 3.4 + (0 if side < 0 else math.pi), front=arm[0], back=arm[1])
            chests.append(info["chest"])
        if ph >= 0.35:
            q = ease((ph - 0.35) / 0.1)
            d.line((chests[0][0], chests[0][1], chests[1][0], chests[1][1]), fill=col(ACC, a * 0.6 * q), width=int(2.5 * u))
            for ch in chests:
                gdot(fd, ch[0], ch[1], 11 * u * q, a)
        if 0.38 < ph < 0.62:
            q = math.sin((ph - 0.38) / 0.24 * math.pi)
            hy = C.hand_pos(c - 82 * u, ground, h, 1, 0, arm[0])[1]
            gdot(d, c, hy, 40 * u * q, a * q * 0.7)
        gdot(d, c, c - 330 * u, 16 * u, a)
        for ch in chests:
            d.line((c, c - 315 * u, ch[0], ch[1]), fill=col(ACC, a * 0.18), width=int(2 * u))
        lay.alpha_composite(C.glow_layer(fl, 1.3))
        return lay.resize((IW, IW), Image.LANCZOS)

    if kind == "turn":
        dx = c - 300 * u
        door = (dx - 90 * u, ground - 330 * u, dx + 90 * u, ground)
        for k in range(5, 0, -1):
            g = k * 14 * u
            d.rounded_rectangle((door[0] - g, door[1] - g, door[2] + g, door[3]), 90 * u + g, fill=col(SHADOW, a * 0.05))
        d.rounded_rectangle(door, 90 * u, fill=col(SHADOW, a * 0.25), outline=col(SHADOW, a * 0.8), width=lw)
        stop_t, walk_t = 0.45, 0.68
        calling = 1 - ease((ph - stop_t) / 0.1)
        for k in range(3):
            f = (lt * 0.5 + k / 3) % 1
            rr = (60 + 260 * f) * u
            d.arc((dx - rr, ground - 165 * u - rr, dx + rr, ground - 165 * u + rr), -50, 50, fill=col(SHADOW, a * (1 - f) * 0.7 * calling), width=lw)
        lx = c + 390 * u
        bright = ease((ph - walk_t) / 0.3)
        gdot(d, lx, ground - 170 * u, (18 + 22 * bright) * u, a)
        if ph < stop_t:
            C.figure(fd, c + 60 * u, ground, 320 * u, FIG, a, facing=-1)
        elif ph < walk_t:
            r_ = ease((ph - stop_t) / 0.08)
            arm = (lerp(0.12, C.ARM_STOP[0][0], r_), lerp(0.08, C.ARM_STOP[0][1], r_))
            C.figure(fd, c + 60 * u, ground, 320 * u, FIG, a, facing=-1, front=arm, back=C.ARM_STOP[1])
        else:
            k = ease((ph - walk_t) / (1 - walk_t))
            C.figure(fd, c + lerp(60, 250, k) * u, ground, 320 * u, FIG, a, facing=1, mode="walk", phase=lt * 3.2)
        lay.alpha_composite(C.glow_layer(fl, 1.0 + 0.6 * bright))
        return lay.resize((IW, IW), Image.LANCZOS)

    if kind == "hands":
        gx, rx = c - 140 * u, c + 200 * u
        for yy in range(-330, 260, 26):
            d.line((c - 330 * u, c + yy * u, c - 330 * u, c + (yy + 13) * u), fill=col(LINE, a * 0.35), width=int(2 * u))
        C.figure(fd, gx, ground, 310 * u, FIG, a, facing=1, lean=0.25, head_down=0.15, front=C.ARM_GIVE[0], back=C.ARM_GIVE[1])
        recv = ((1.1, 0.35), (-0.1, 0.06))
        C.figure(fd, rx, ground, 240 * u, FIG, a * 0.85, facing=-1, mode="sit", lean=0.05, front=recv[0], back=recv[1])
        h0 = C.hand_pos(gx, ground, 310 * u, 1, 0.25, C.ARM_GIVE[0])
        h1 = C.hand_pos(rx, ground, 240 * u, -1, 0.05, recv[0], mode="sit")
        f = (lt * 0.45) % 1
        x_ = lerp(h0[0], h1[0], ease(f)); y_ = lerp(h0[1], h1[1], ease(f)) - math.sin(f * math.pi) * 40 * u
        gdot(fd, x_, y_, 12 * u, a)
        lay.alpha_composite(C.glow_layer(fl, 1.3))
        return lay.resize((IW, IW), Image.LANCZOS)

    if kind == "eye":
        crescent(lay, c + 270 * u, c - 300 * u, 60 * u, FIG, a)
        for i in range(14):
            rs = np.random.default_rng(40 + i)
            sx, sy = c + rs.uniform(-420, 420) * u, c + rs.uniform(-430, -120) * u
            tw = 0.4 + 0.6 * abs(math.sin(lt * 1.5 + i))
            d.ellipse((sx - 3 * u, sy - 3 * u, sx + 3 * u, sy + 3 * u), fill=col(FIG, a * tw))
        d.rounded_rectangle((c - 230 * u, ground - 4 * u, c + 170 * u, ground + 12 * u), 6 * u, fill=col(CARD, a), outline=col(ACC, a * 0.6), width=int(2 * u))
        x = c - 40 * u
        info = C.figure(fd, x, ground, 300 * u, FIG, a, facing=1, mode="sit", lean=0.06, head_down=0.3,
                        front=C.ARMS_DUA[0], back=C.ARMS_DUA[1])
        hx, hy = info["head"]
        for k in range(3):
            f = ((lt - 1.0) * 0.5 + k / 3) % 1 if lt > 1.0 else -1
            if f < 0:
                continue
            ty = hy + 25 * u + 230 * u * f ** 1.5
            s_ = 9 * u
            tx = hx + 30 * u
            fd.polygon([(tx, ty - s_ * 1.9), (tx + s_, ty), (tx - s_, ty)], fill=col(ACC, a * (1 - f)))
            fd.ellipse((tx - s_, ty - s_, tx + s_, ty + s_), fill=col(ACC, a * (1 - f)))
        lay.alpha_composite(C.glow_layer(fl, 1.3))
        return lay.resize((IW, IW), Image.LANCZOS)


def draw_icon(kind, lt, dur, a):
    if USE_CHARS and kind in CHAR_KINDS:
        return draw_chars(kind, lt, dur, a)
    S = IW * SS
    lay = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    c, u = S / 2, SS
    p = ease(lt / 0.9)
    lw = int(2.4 * u)
    if kind == "sun":
        y = c - 40 * u + (1 - ease(lt / 3.5)) * -160 * u
        rad = (110 + 40 * ease(lt / 3.5)) * u
        for k in range(8, 0, -1):
            rr = rad * (1 + k * 0.17)
            d.ellipse((c - rr, y - rr, c + rr, y + rr), fill=col(WARM, a * 0.04))
        d.ellipse((c - rad, y - rad, c + rad, y + rad), fill=col(WARM, a))
        for k in range(3):  # heat waves
            f = (lt * 0.5 + k / 3) % 1
            rr = rad * (1.1 + 1.1 * f)
            d.ellipse((c - rr, y - rr, c + rr, y + rr), outline=col(WARM, a * (1 - f) * 0.5), width=lw)
        hz = c + 330 * u
        d.line((c - 420 * u, hz, c + 420 * u, hz), fill=col(LINE, a * 0.6), width=lw)
        for i in range(-8, 9):  # crowd
            x = c + i * 46 * u
            h = (18 + 6 * ((i * 7) % 3)) * u
            d.ellipse((x - 6 * u, hz - h - 14 * u, x + 6 * u, hz - h - 2 * u), fill=col(LINE, a * 0.7))
            d.line((x, hz - h, x, hz), fill=col(LINE, a * 0.7), width=int(3 * u))
    elif kind in ("canopy", "canopy_full"):
        full = kind == "canopy_full"
        top = c - 300 * u
        arcw, arch = 380 * u * p, 260 * u
        for k in range(6, 0, -1):
            pts = arc_pts(c, top + arch, arcw * (1 + k * 0.06), arch * (1 + k * 0.08), math.pi, 2 * math.pi)
            d.polygon(pts + [(c + arcw, top + arch + 420 * u), (c - arcw, top + arch + 420 * u)], fill=col(ACC, a * 0.025))
        d.line(arc_pts(c, top + arch, arcw, arch, math.pi, 2 * math.pi), fill=col(ACC, a), width=int(3 * u), joint="curve")
        gdot(d, c, top + 20 * u, 22 * u, a)
        base = top + arch + 300 * u
        shown = 7 if full else clamp((lt - 0.8) / 2.5) * 7
        for i in range(7):
            q = 1.0 if full else clamp(shown - i)
            x = c + (i - 3) * 82 * u
            yy = base - 60 * u * math.sin(math.pi * (i / 6)) * 0.4
            r = 16 * u
            if q > 0:
                gdot(d, x, yy, r * (0.6 + 0.4 * ease(q)), a * ease(q))
            else:
                d.ellipse((x - r, yy - r, x + r, yy + r), outline=col(LINE, a * 0.35), width=int(2 * u))
        if full:
            for i in range(28):
                ang = math.pi + math.pi * (i + 0.5) / 28
                l0, l1 = arch * 1.08, arch * (1.3 + 0.15 * math.sin(lt * 2 + i))
                d.line((c + l0 * 1.45 * math.cos(ang), top + arch + l0 * math.sin(ang),
                        c + l1 * 1.45 * math.cos(ang), top + arch + l1 * math.sin(ang)), fill=col(ACC, a * 0.45), width=int(2 * u))
        else:
            for i in range(26):  # people outside the shade
                rs = np.random.default_rng(i)
                x = c + rs.uniform(-420, 420) * u
                yy = base + rs.uniform(90, 300) * u
                d.ellipse((x - 6 * u, yy - 6 * u, x + 6 * u, yy + 6 * u), fill=col(LINE, a * 0.25))
    elif kind == "scales":
        ang = 0.28 * math.exp(-lt * 0.9) * math.cos(lt * 3.2)
        top = c - 230 * u
        d.line((c, top, c, c + 260 * u), fill=col(LINE, a), width=int(3 * u))
        d.line((c - 120 * u, c + 260 * u, c + 120 * u, c + 260 * u), fill=col(LINE, a), width=int(3 * u))
        gdot(d, c, top - 10 * u, 16 * u, a)
        L = 300 * u
        for side in (-1, 1):
            ex, ey = c + side * L * math.cos(ang), top + 30 * u + side * L * math.sin(ang)
            d.line((c, top + 30 * u, ex, ey), fill=col(LINE, a), width=int(3 * u))
            py = ey + 170 * u
            d.line((ex, ey, ex - 80 * u, py), fill=col(LINE, a * 0.7), width=int(2 * u))
            d.line((ex, ey, ex + 80 * u, py), fill=col(LINE, a * 0.7), width=int(2 * u))
            d.chord((ex - 100 * u, py - 40 * u, ex + 100 * u, py + 40 * u), 0, 180, fill=col(CARD, a), outline=col(ACC, a), width=int(3 * u))
    elif kind == "sprout":
        g = ease(lt / 2.2)
        base = c + 320 * u
        h = 520 * u * g
        pts = [(c + 22 * u * math.sin(i / 20 * 3 + lt) * (i / 20), base - h * i / 20) for i in range(21)]
        d.line((c - 200 * u, base, c + 200 * u, base), fill=col(LINE, a * 0.6), width=lw)
        d.line(pts, fill=col(ACC, a), width=int(4 * u), joint="curve")
        for k, fr in enumerate((0.35, 0.55, 0.75)):
            q = clamp((g - fr) / 0.2)
            if q <= 0: continue
            x, y = pts[int(fr * 20)]
            side = -1 if k % 2 == 0 else 1
            sz = 90 * u * ease(q)
            leaf = [(x, y), (x + side * sz * 0.6, y - sz * 0.55), (x + side * sz * 1.2, y - sz * 0.2), (x + side * sz * 0.6, y + sz * 0.05)]
            d.polygon(leaf, fill=col(ACC, a * 0.25), outline=col(ACC, a))
        gdot(d, pts[-1][0], pts[-1][1], 14 * u, a)
    elif kind == "mosque":
        dp = clamp(lt / 1.6)
        base = c + 300 * u
        bw = 260 * u
        d.line((c - bw, base, c + bw, base), fill=col(LINE, a), width=lw)
        d.line((c - bw * 0.8, base, c - bw * 0.8, c), fill=col(LINE, a), width=lw)
        d.line((c + bw * 0.8, base, c + bw * 0.8, c), fill=col(LINE, a), width=lw)
        dome = arc_pts(c, c, bw * 0.8, 240 * u, math.pi, math.pi + math.pi * dp)
        if len(dome) > 1: d.line(dome, fill=col(ACC, a), width=int(3 * u), joint="curve")
        d.line((c, c - 240 * u, c, c - 300 * u), fill=col(ACC, a * dp), width=lw)
        d.ellipse((c - 10 * u, c - 320 * u, c + 10 * u, c - 300 * u), outline=col(ACC, a * dp), width=lw)
        for mx in (-1, 1):  # minarets
            x = c + mx * 380 * u
            d.line((x, base, x, c - 180 * u), fill=col(LINE, a * 0.8), width=lw)
            d.polygon([(x - 18 * u, c - 180 * u), (x + 18 * u, c - 180 * u), (x, c - 250 * u)], outline=col(LINE, a * 0.8))
        door = (c - 70 * u, base - 190 * u, c + 70 * u, base)
        d.rounded_rectangle(door, 70 * u, outline=col(LINE, a * 0.8), width=lw)
        hb = 1 + 0.12 * math.sin(lt * 5) * math.sin(lt * 5)
        gdot(d, c, base - 300 * u, 24 * u * hb, a)
        for k in range(3):
            f = (lt * 0.6 + k / 3) % 1
            rr = (30 + 140 * f) * u
            d.ellipse((c - rr, base - 300 * u - rr, c + rr, base - 300 * u + rr), outline=col(ACC, a * (1 - f) * 0.6), width=int(2 * u))
    elif kind == "two":
        ph = clamp(lt / max(dur - 0.6, 1))
        sep = 300 * u * (abs(math.cos(ph * math.pi)) * 0.85 + 0.15)
        y = c + 30 * u * math.sin(lt)
        x1, x2 = c - sep, c + sep
        d.line((x1, y, x2, y), fill=col(ACC, a * 0.6), width=int(2 * u))
        d.arc((c - 420 * u, c - 300 * u, c + 420 * u, c + 300 * u), 200, 340, fill=col(LINE, a * 0.35), width=int(2 * u))
        gdot(d, x1, y, 30 * u, a)
        gdot(d, x2, y, 30 * u, a)
        close = 1 - clamp(sep / (120 * u))
        if close > 0:
            gdot(d, c, y, 60 * u * close, a * close * 0.6)
        gdot(d, c, c - 300 * u, 16 * u, a * 0.9)
        d.line((c, c - 280 * u, x1, y), fill=col(ACC, a * 0.25), width=int(2 * u))
        d.line((c, c - 280 * u, x2, y), fill=col(ACC, a * 0.25), width=int(2 * u))
    elif kind == "turn":
        m = ease((lt - 2.2) / 2.5)
        lx = c - 260 * u
        for k in range(6, 0, -1):
            rr = 70 * u * (1 + k * 0.3)
            d.ellipse((lx - rr, c - rr, lx + rr, c + rr), fill=col(SHADOW, a * 0.05))
        d.ellipse((lx - 70 * u, c - 70 * u, lx + 70 * u, c + 70 * u), outline=col(SHADOW, a * 0.8), width=lw)
        rx = c + 300 * u
        gdot(d, rx, c, (26 + 14 * m) * u, a)
        x = lerp(c - 120 * u, c + 180 * u, m)
        for k in range(12):
            tx = lerp(c - 120 * u, x, k / 11)
            d.ellipse((tx - 3 * u, c - 3 * u, tx + 3 * u, c + 3 * u), fill=col(ACC, a * 0.4 * (k / 11)))
        d.ellipse((x - 18 * u, c - 18 * u, x + 18 * u, c + 18 * u), fill=col(R.CREAM, a))
        sh = 1 - m
        d.line((x - 60 * u, c - 90 * u * sh - 30 * u, x - 60 * u, c + 90 * u * sh + 30 * u), fill=col(ACC, a * (0.3 + 0.7 * m)), width=int(4 * u))
    elif kind == "hands":
        d.line((c, c - 300 * u, c, c + 300 * u), fill=col(LINE, a * 0.5), width=int(2 * u))
        for yy in range(-300, 300, 30):
            d.line((c - 6 * u, c + yy * u, c + 6 * u, c + yy * u), fill=col(LINE, a * 0.25), width=int(1 * u))
        for side, alpha in ((-1, 0.3), (1, 1.0)):
            x = c + side * 220 * u
            d.rounded_rectangle((x - 110 * u, c - 60 * u, x + 110 * u, c + 70 * u), 50 * u, fill=col(CARD, a * alpha), outline=col(ACC if side > 0 else LINE, a * alpha), width=lw)
            for f in range(4):
                fx = x - 75 * u + f * 50 * u
                d.rounded_rectangle((fx - 18 * u, c - 130 * u, fx + 18 * u, c - 40 * u), 18 * u, fill=col(CARD, a * alpha), outline=col(ACC if side > 0 else LINE, a * alpha), width=int(2 * u))
        f = (lt * 0.55) % 1
        cx_, cy_ = c + 220 * u, c + 80 * u + 170 * u * ease(f)
        gdot(d, cx_, cy_, 22 * u, a * (1 - clamp((f - 0.8) / 0.2)))
        d.rounded_rectangle((c + 130 * u, c + 270 * u, c + 310 * u, c + 290 * u), 8 * u, outline=col(LINE, a * 0.6), width=int(2 * u))
    elif kind == "eye":
        op = ease(lt / 0.8)
        ex, ey, ew, eh = c, c - 60 * u, 300 * u, 150 * u * op
        d.line(arc_pts(ex, ey + eh * 0.9, ew, eh * 1.6, math.pi * 1.18, math.pi * 1.82), fill=col(LINE, a), width=int(3 * u), joint="curve")
        d.line(arc_pts(ex, ey - eh * 0.9, ew, eh * 1.6, math.pi * 0.18, math.pi * 0.82), fill=col(LINE, a), width=int(3 * u), joint="curve")
        ir = 70 * u * op
        d.ellipse((ex - ir, ey - ir, ex + ir, ey + ir), outline=col(ACC, a), width=int(3 * u))
        gdot(d, ex, ey, 26 * u * op, a)
        for k in range(2):
            f = ((lt - 1.0) * 0.45 + k * 0.5) % 1 if lt > 1.0 else -1
            if f < 0: continue
            tx, ty = ex + 210 * u, ey + 60 * u + 330 * u * f ** 1.6
            s = 22 * u
            d.polygon([(tx, ty - s * 1.8), (tx + s, ty), (tx - s, ty)], fill=col(ACC, a * (1 - f)))
            d.ellipse((tx - s, ty - s, tx + s, ty + s), fill=col(ACC, a * (1 - f)))
    elif kind == "book":
        op = ease(lt / 0.8)
        y0, y1 = c - 170 * u, c + 170 * u
        for side in (-1, 1):
            xo = c + side * 320 * u * op
            pts = [(c, y0 + 20 * u), (xo, y0), (xo, y1), (c, y1 + 20 * u)]
            d.polygon(pts, fill=col(CARD, a * 0.9), outline=col(ACC, a))
            for k in range(6):
                ly = y0 + 60 * u + k * 42 * u
                d.line((c + side * 40 * u, ly + 6 * u, c + side * (40 + 220 * op) * u, ly), fill=col(LINE, a * 0.45), width=int(2 * u))
        d.line((c, y0 + 20 * u, c, y1 + 20 * u), fill=col(ACC, a), width=int(3 * u))
        gdot(d, c, y0 - 70 * u, 16 * u, a)
        f = R.sfont(FD + "Inter-SemiBold.otf", int(40 * u))
        R.text_center(d, c, y1 + 110 * u, "аль-Бухари № 660 · Муслим № 1031", f, col(R.CREAM, a * 0.9))
    return lay.resize((IW, IW), Image.LANCZOS)


SUN_MASK = np.exp(-(np.sqrt((R.xx - R.CX) ** 2 + ((R.yy - R.CY + 100) * 0.8) ** 2) / 520) ** 2)[..., None]


def render(fi):
    t = fi / FPS
    si = max(i for i, s in enumerate(SCENES) if s[0] <= t) if t >= SCENES[0][0] else 0
    s0, s1, seg = SCENES[si]
    sid, title, kind, _, _, num = seg
    lt, dur = t - s0, s1 - s0
    last = si == len(SCENES) - 1
    a_out = 1 - R.ease_io((t - (DUR - 0.7)) / 0.7) if last else 1 - R.ease_io((lt - (dur - 0.28)) / 0.28)
    a = ease(lt / 0.4) * a_out
    pal = palette_at(si, lt)
    apply_palette(pal)
    frame = background(t, pal, 0.6 + 0.4 * a)
    bokeh(frame, t)
    if kind == "sun":
        arr = np.asarray(frame, dtype=np.float32)[..., :3]
        m = np.clip(SUN_MASK * 0.55 * a * ease(lt / 2.5), 0, 1)
        arr = arr * (1 - m) + np.array((150, 105, 60), np.float32) * m
        frame = Image.fromarray(arr.astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(frame)
    R.particles(d, t, 1.0)
    if 1 <= num <= 7:  # huge faint numeral behind the icon
        nl = Image.new("RGBA", (W, 760), (0, 0, 0, 0))
        R.text_center(ImageDraw.Draw(nl), W / 2, 380, str(num), F_NUM, col(ACC, 0.055 * a))
        frame.alpha_composite(nl, (0, R.CY - 380 - int((1 - ease(lt / 0.6)) * 40)))
    icon = draw_icon(kind, lt, dur, a)
    zoom = (0.9 + 0.1 * ease(lt / 0.6) + 0.03 * clamp(lt / dur)) * (1.18 if USE_CHARS and kind in CHAR_KINDS else 1.0)
    sz = int(IW * zoom)
    frame.alpha_composite(icon.resize((sz, sz), Image.BICUBIC), (int(R.CX - sz / 2), int(R.CY - sz / 2 + 8 * math.sin(t * 1.3))))
    ti = R.title_img(title)
    ta = ease((lt - 0.12) / 0.45) * a_out
    if ta > 0:
        sc = 1.06 - 0.06 * ease((lt - 0.12) / 0.6)
        tim = ti.resize((int(ti.width * sc), int(ti.height * sc)), Image.BICUBIC)
        al = np.array(tim.getchannel("A"), np.float32) * ta
        tim.putalpha(Image.fromarray(al.astype(np.uint8)))
        frame.alpha_composite(tim, (int(W / 2 - tim.width / 2), int(R.TITLE_Y - tim.height / 2 + (1 - ease((lt - 0.12) / 0.5)) * 40)))
    d = ImageDraw.Draw(frame)
    if num >= 1:  # 7-dot counter under the title
        y = R.TITLE_Y + (ti.height / 2) + 30
        for k in range(7):
            x = W / 2 + (k - 3) * 44
            on = k < num - 1 or num == 8
            cur = k == num - 1
            r = 9 if cur else 7
            if cur:
                pu = 0.6 + 0.4 * math.sin(t * 5)
                d.ellipse((x - r * 2.2, y - r * 2.2, x + r * 2.2, y + r * 2.2), fill=col(ACC, 0.18 * pu * a_out))
            d.ellipse((x - r, y - r, x + r, y + r), fill=col(ACC, (0.95 if (on or cur) else 0.0) * a_out),
                      outline=col(R.LINE, 0.5 * a_out), width=2)
    R.draw_sub(frame, t)
    d = ImageDraw.Draw(frame)
    R.text_center(d, W / 2, 140, "ХАДИС · АЛЬ-БУХАРИ И МУСЛИМ", F_OVER, col(R.LINE, 0.75))
    n = len(SCENES); gap = 6; x0 = 60; tot = W - 120
    segw = (tot - gap * (n - 1)) / n
    for k in range(n):
        xa = x0 + k * (segw + gap)
        d.rounded_rectangle((xa, 92, xa + segw, 98), 3, fill=(255, 255, 255, 30))
        f = 1 if k < si else (clamp(lt / dur) if k == si else 0)
        if f > 0: d.rounded_rectangle((xa, 92, xa + max(6, segw * f), 98), 3, fill=col(ACC, 0.9))
    return frame.convert("RGB").tobytes()


def chunk(args):
    a0, a1, path = args
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for fi in range(a0, a1):
        p.stdin.write(render(fi))
    p.stdin.close(); p.wait()
    return path


if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    if len(sys.argv) > 2 and sys.argv[2] == "stills":
        for tt in [float(x) for x in sys.argv[3].split(",")]:
            Image.frombytes("RGB", (W, H), render(int(tt * FPS))).save(f"{out}/still_{tt:06.2f}.jpg", quality=88)
        sys.exit()
    print(f"duration {DUR:.1f}s, {NF} frames")
    step = math.ceil(NF / 4)
    jobs = [(i * step, min(NF, (i + 1) * step), f"{out}/part{i}.mp4") for i in range(4)]
    with Pool(4) as pool:
        parts = pool.map(chunk, jobs)
    with open(f"{out}/list.txt", "w") as f:
        for p_ in parts: f.write(f"file '{os.path.abspath(p_)}'\n")
    print("done")
