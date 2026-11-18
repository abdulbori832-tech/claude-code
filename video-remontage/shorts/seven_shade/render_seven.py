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


def arc_pts(cx, cy, rx, ry, a0, a1, n=80):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def draw_icon(kind, lt, dur, a):
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
        R.glow_dot(d, c, top + 20 * u, 22 * u, a)
        base = top + arch + 300 * u
        shown = 7 if full else clamp((lt - 0.8) / 2.5) * 7
        for i in range(7):
            q = 1.0 if full else clamp(shown - i)
            x = c + (i - 3) * 82 * u
            yy = base - 60 * u * math.sin(math.pi * (i / 6)) * 0.4
            r = 16 * u
            if q > 0:
                R.glow_dot(d, x, yy, r * (0.6 + 0.4 * ease(q)), a * ease(q))
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
        R.glow_dot(d, c, top - 10 * u, 16 * u, a)
        L = 300 * u
        for side in (-1, 1):
            ex, ey = c + side * L * math.cos(ang), top + 30 * u + side * L * math.sin(ang)
            d.line((c, top + 30 * u, ex, ey), fill=col(LINE, a), width=int(3 * u))
            py = ey + 170 * u
            d.line((ex, ey, ex - 80 * u, py), fill=col(LINE, a * 0.7), width=int(2 * u))
            d.line((ex, ey, ex + 80 * u, py), fill=col(LINE, a * 0.7), width=int(2 * u))
            d.chord((ex - 100 * u, py - 40 * u, ex + 100 * u, py + 40 * u), 0, 180, fill=col(R.CARD, a), outline=col(ACC, a), width=int(3 * u))
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
        R.glow_dot(d, pts[-1][0], pts[-1][1], 14 * u, a)
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
        R.glow_dot(d, c, base - 300 * u, 24 * u * hb, a)
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
        R.glow_dot(d, x1, y, 30 * u, a)
        R.glow_dot(d, x2, y, 30 * u, a)
        close = 1 - clamp(sep / (120 * u))
        if close > 0:
            R.glow_dot(d, c, y, 60 * u * close, a * close * 0.6)
        R.glow_dot(d, c, c - 300 * u, 16 * u, a * 0.9)
        d.line((c, c - 280 * u, x1, y), fill=col(ACC, a * 0.25), width=int(2 * u))
        d.line((c, c - 280 * u, x2, y), fill=col(ACC, a * 0.25), width=int(2 * u))
    elif kind == "turn":
        m = ease((lt - 2.2) / 2.5)
        lx = c - 260 * u
        for k in range(6, 0, -1):
            rr = 70 * u * (1 + k * 0.3)
            d.ellipse((lx - rr, c - rr, lx + rr, c + rr), fill=col(R.PAL["shadow"], a * 0.05))
        d.ellipse((lx - 70 * u, c - 70 * u, lx + 70 * u, c + 70 * u), outline=col(R.PAL["shadow"], a * 0.8), width=lw)
        rx = c + 300 * u
        R.glow_dot(d, rx, c, (26 + 14 * m) * u, a)
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
            d.rounded_rectangle((x - 110 * u, c - 60 * u, x + 110 * u, c + 70 * u), 50 * u, fill=col(R.CARD, a * alpha), outline=col(ACC if side > 0 else LINE, a * alpha), width=lw)
            for f in range(4):
                fx = x - 75 * u + f * 50 * u
                d.rounded_rectangle((fx - 18 * u, c - 130 * u, fx + 18 * u, c - 40 * u), 18 * u, fill=col(R.CARD, a * alpha), outline=col(ACC if side > 0 else LINE, a * alpha), width=int(2 * u))
        f = (lt * 0.55) % 1
        cx_, cy_ = c + 220 * u, c + 80 * u + 170 * u * ease(f)
        R.glow_dot(d, cx_, cy_, 22 * u, a * (1 - clamp((f - 0.8) / 0.2)))
        d.rounded_rectangle((c + 130 * u, c + 270 * u, c + 310 * u, c + 290 * u), 8 * u, outline=col(LINE, a * 0.6), width=int(2 * u))
    elif kind == "eye":
        op = ease(lt / 0.8)
        ex, ey, ew, eh = c, c - 60 * u, 300 * u, 150 * u * op
        d.line(arc_pts(ex, ey + eh * 0.9, ew, eh * 1.6, math.pi * 1.18, math.pi * 1.82), fill=col(LINE, a), width=int(3 * u), joint="curve")
        d.line(arc_pts(ex, ey - eh * 0.9, ew, eh * 1.6, math.pi * 0.18, math.pi * 0.82), fill=col(LINE, a), width=int(3 * u), joint="curve")
        ir = 70 * u * op
        d.ellipse((ex - ir, ey - ir, ex + ir, ey + ir), outline=col(ACC, a), width=int(3 * u))
        R.glow_dot(d, ex, ey, 26 * u * op, a)
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
            d.polygon(pts, fill=col(R.CARD, a * 0.9), outline=col(ACC, a))
            for k in range(6):
                ly = y0 + 60 * u + k * 42 * u
                d.line((c + side * 40 * u, ly + 6 * u, c + side * (40 + 220 * op) * u, ly), fill=col(LINE, a * 0.45), width=int(2 * u))
        d.line((c, y0 + 20 * u, c, y1 + 20 * u), fill=col(ACC, a), width=int(3 * u))
        R.glow_dot(d, c, y0 - 70 * u, 16 * u, a)
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
    frame = R.background(t, 0.6 + 0.4 * a, 0.0, 0.0)
    if kind == "sun":
        arr = np.asarray(frame, dtype=np.float32)[..., :3]
        m = np.clip(SUN_MASK * 0.55 * a * ease(lt / 2.5), 0, 1)
        arr = arr * (1 - m) + np.array((150, 105, 60), np.float32) * m
        frame = Image.fromarray(arr.astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(frame)
    R.particles(d, t, 1.0)
    if 1 <= num <= 7:  # huge faint numeral behind the icon
        nl = Image.new("RGBA", (W, 760), (0, 0, 0, 0))
        R.text_center(ImageDraw.Draw(nl), W / 2, 380, str(num), F_NUM, col(ACC, 0.10 * a))
        frame.alpha_composite(nl, (0, R.CY - 380 - int((1 - ease(lt / 0.6)) * 40)))
    icon = draw_icon(kind, lt, dur, a)
    zoom = 0.9 + 0.1 * ease(lt / 0.6) + 0.03 * clamp(lt / dur)
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
