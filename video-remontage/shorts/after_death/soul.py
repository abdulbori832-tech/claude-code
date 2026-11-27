"""'Path of the soul' — three-part series in the PATH format (one continuous camera).

Part 1  The last minute      desert night, light descends, the soul rises, camera tilts up
Part 2  Through seven skies  camera climbs through seven gates (sand -> emerald -> light), returns
Part 3  Three questions      cross-section of the grave: questions, answers, widening, door to Paradise

Timing: partN.txt paragraphs; timingsN.json from the narration if present, else a reading estimate.
usage: python3 soul.py PART OUT.mp4 [stills t1,t2,...]
"""
import json, math, os, sys, subprocess
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "seven_shade"))
sys.path.insert(0, os.path.join(HERE, "..", "last_man"))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import render_cinema as RC
import characters as C
import formats as F

W, H, FPS = 1080, 1920, 30
rgba, ease, clamp, lerp, eio, mix = RC.rgba, RC.ease, RC.clamp, RC.lerp, RC.eio, F.mix
GOLD, CREAM = RC.GOLD, RC.CREAM
HZ = 1150
LIGHT = (255, 246, 222)
EMER_L = (190, 255, 220)
SRC = "Абу Дауд 4753 · Ахмад 18534"

def comp(frame, im, xy=(0, 0)):
    """Composite an RGBA layer onto the opaque RGB frame."""
    frame.paste(im, xy, im)


def put(frame, im, cx, cy, a):
    if a <= 0:
        return
    if a < 1:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    frame.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), im)


# ---------------------------------------------------------------- tall sky (colour by altitude)
HMAX = 6000
ROWS = HMAX - HZ + H + 10
alt = (HMAX - np.arange(ROWS)).astype(np.float32)  # world height of each row (row 0 = top)
KEYS = [(-900, (90, 60, 40)), (0, (130, 84, 52)), (500, (60, 44, 34)), (1300, (22, 18, 16)), (2200, (8, 22, 24)),
        (3200, (12, 46, 46)), (4200, (36, 96, 80)), (5000, (120, 190, 160)), (5800, (236, 250, 236)), (6100, (255, 255, 245))]
col = np.zeros((ROWS, 3), np.float32)
for (h0, c0), (h1, c1) in zip(KEYS, KEYS[1:]):
    m = (alt >= h0) & (alt < h1)
    k = ((alt[m] - h0) / (h1 - h0))[:, None]
    col[m] = np.array(c0) * (1 - k) + np.array(c1) * k
col[alt >= KEYS[-1][0]] = KEYS[-1][1]
TALL = np.repeat(col[:, None, :], W, axis=1)
xs = np.arange(W, dtype=np.float32)[None, :]
band = np.exp(-(((xs * 0.6 + np.arange(ROWS)[:, None] * 0.25) - 1500) / 300) ** 2) * np.clip((alt[:, None] - 800) / 2000, 0, 1) * np.clip((5200 - alt[:, None]) / 1000, 0, 1)
TALL += band[..., None] * np.array((40, 90, 80), np.float32) * 0.6
TALL = np.clip(TALL, 0, 255).astype(np.uint8)
rng = np.random.default_rng(9)
STARS = np.stack([rng.uniform(0, W, 2600), rng.uniform(300, HMAX, 2600), rng.random(2600)], 1)


def sky(cy, t):
    r0 = int(HMAX - HZ - cy)
    r0 = max(0, min(ROWS - H, r0))
    im = Image.fromarray(TALL[r0:r0 + H])  # opaque RGB: drawing below blends
    d = ImageDraw.Draw(im, "RGBA")
    vis = (STARS[:, 1] > cy + HZ - H - 50) & (STARS[:, 1] < cy + HZ + 50)
    for x, h, b in STARS[vis]:
        y = HZ + cy - h
        fade = clamp((5000 - h) / 1200)
        a = (0.25 + 0.6 * b * (0.6 + 0.4 * math.sin(t * 2 + x))) * fade
        if a > 0.03:
            r = 1.6 if b > 0.93 else 1.0
            d.ellipse((x - r, y - r, x + r, y + r), fill=rgba((255, 250, 235), a))
    return im


def ground(frame, cy, t, rim=True):
    """Dunes + ground below the horizon (screen horizon = HZ + cy)."""
    hy = HZ + cy
    if hy > H + 200:
        return
    S = 2
    lay = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for par, base, amp, f1, f2, ph, c in ((0.15, -70, 90, 2.2, 5.1, 0.3, (58, 42, 34)), (0.45, -10, 30, 3.0, 7.3, 1.1, (40, 30, 24))):
        pts = [(x * S, (hy + F.ridge(x + t * 8 * par, base, amp, f1, f2, ph)) * S) for x in range(0, W + 9, 8)]
        d.polygon(pts + [(W * S, H * S), (0, H * S)], fill=rgba(c, 1))
    g = [(x * S, (hy + F.ridge(x, 30, 10, 1.3, 3.1, 2.0)) * S) for x in range(0, W + 9, 8)]
    d.polygon(g + [(W * S, H * S), (0, H * S)], fill=rgba((20, 15, 12), 1))
    if rim:
        d.line(g, fill=rgba(GOLD, 0.9), width=4, joint="curve")
    comp(frame, lay.resize((W, H), Image.LANCZOS))


def glow_dot(d, x, y, r, a, color=LIGHT, n=7, spread=0.7):
    for k in range(n, 0, -1):
        rr = r * (1 + k * spread)
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=rgba(color, a * 0.045))
    d.ellipse((x - r, y - r, x + r, y + r), fill=rgba(color, a))


def soul_orb(d, x, y, r, a, t):
    glow_dot(d, x, y, r, a, LIGHT, n=9, spread=0.8)
    for k in range(5):  # sparkles
        ang = t * 1.5 + k * 1.26
        sx, sy = x + math.cos(ang) * r * 2.2, y + math.sin(ang) * r * 2.2
        d.ellipse((sx - 3, sy - 3, sx + 3, sy + 3), fill=rgba(LIGHT, a * 0.8))


def light_beams(d, xs_, top, bottom, a, t, width=90, color=LIGHT):
    for i, x in enumerate(xs_):
        for k in range(6, 0, -1):
            w = width * (0.3 + k * 0.25)
            d.polygon([(x - w * 0.4, top), (x + w * 0.4, top), (x + w * 0.7, bottom), (x - w * 0.7, bottom)], fill=rgba(color, a * 0.035))
        d.line((x, top, x, bottom), fill=rgba(color, a * 0.5), width=2)
        for j in range(6):  # descending particles
            f = (t * 0.35 + j / 6 + i * 0.13) % 1
            yy = lerp(top, bottom, f)
            d.ellipse((x - 3 + 18 * math.sin(j + t), yy - 3, x + 3 + 18 * math.sin(j + t), yy + 3), fill=rgba(color, a * (1 - f) * 0.9))


def lying_figure(d, x, y, h, a, color=CREAM):
    """Person lying on a mat, head to the left; (x, y) = centre of the body on the ground."""
    L = h
    d.rounded_rectangle((x - L * 0.6, y - 8, x + L * 0.62, y + 6), 6, fill=rgba((120, 40, 50), a))
    d.ellipse((x - L * 0.55, y - L * 0.2, x - L * 0.37, y - L * 0.02), fill=rgba(color, a))
    d.rounded_rectangle((x - L * 0.38, y - L * 0.17, x + L * 0.55, y - 2), int(L * 0.08), fill=rgba(color, a))


def tent(d, x, y, s, a):
    d.polygon([(x - 260 * s, y), (x, y - 330 * s), (x + 260 * s, y)], fill=rgba((44, 32, 26), a), outline=rgba(GOLD, a * 0.8))
    d.polygon([(x - 50 * s, y), (x, y - 140 * s), (x + 50 * s, y)], fill=rgba((255, 200, 120), a * 0.5))
    d.line((x, y - 330 * s, x, y - 370 * s), fill=rgba(GOLD, a), width=3)


# ---------------------------------------------------------------- text overlay
F_TOP = RC.serif(34, 600)
SHADE = np.zeros((H, W, 4), np.uint8)
SHADE[..., 3] = (np.clip((np.arange(H) - 1250) / 400, 0, 1) ** 1.2 * 215).astype(np.uint8)[:, None]
SHADE = Image.fromarray(SHADE)
TOPSH = np.zeros((H, W, 4), np.uint8)
TOPSH[..., 3] = (np.clip((360 - np.arange(H)) / 360, 0, 1) ** 1.5 * 150).astype(np.uint8)[:, None]
TOPSH = Image.fromarray(TOPSH)


def overlay(frame, part, num, title, sub, src, ar, lt, dur, last):
    comp(frame, SHADE)
    comp(frame, TOPSH)
    out_k = 0 if last else eio((lt - (dur - 0.35)) / 0.35)
    ta = ease((lt - 0.15) / 0.5) * (1 - out_k)
    put(frame, RC.plain_text(f"ПУТЬ ДУШИ  ·  ЧАСТЬ {part} / 3", F_TOP, GOLD + (255,), tracking=3), W / 2, 150, 1.0)
    if num:
        put(frame, RC.plain_text(num, RC.serif(40, 600), GOLD + (255,)), W / 2, 1440, ta)
    nm = RC.gold_text(title, RC.fit_serif(title, W - 120, 96), tracking=4)
    put(frame, nm, W / 2, 1520, ta)
    if sub:
        put(frame, RC.plain_text(sub, RC.F_DESC, (245, 240, 232, 255)), W / 2, 1625, ease((lt - 0.45) / 0.5) * (1 - out_k))
    if src:
        put(frame, RC.plain_text(src, RC.F_SRC, (214, 178, 112, 255)), W / 2, 1735, ease((lt - 0.8) / 0.5) * (1 - out_k))
    if ar:
        put(frame, RC.plain_text(ar, RC.F_AR, (250, 226, 170, 255), direction="rtl"), W / 2, 300, ease((lt - 0.6) / 0.8) * (1 - out_k))


# ---------------------------------------------------------------- PART 1
P1 = [  # title, sub, arabic
    ("ПОСЛЕДНЯЯ МИНУТА", "что будет с тобой в последнюю минуту жизни?", ""),
    ("АНГЕЛЫ", "с лицами, сияющими как солнце", ""),
    ("«О БЛАГАЯ ДУША»", "выходи к прощению Аллаха и Его довольству", "أَيَّتُهَا النَّفْسُ الطَّيِّبَةُ اخْرُجِي إِلَى مَغْفِرَةٍ مِنَ اللَّهِ وَرِضْوَانٍ"),
    ("КАК КАПЛЯ", "душа выходит легко, как капля из бурдюка", ""),
    ("ЭТО ТОЛЬКО НАЧАЛО", "куда её понесут дальше — в части 2  →", ""),
]


def part1(t, si, lt, dur, segs, tl):
    t_soul = tl[3][0]
    t_cliff = tl[4][0]
    cy = 1500 * eio((t - t_cliff) / max(tl[4][1] - t_cliff, 1)) if t >= t_cliff else 0
    frame = sky(cy, t)
    d = ImageDraw.Draw(frame, "RGBA")
    beams = clamp((t - tl[1][0]) / 1.5)
    gy = HZ + cy + 30
    px = W * 0.5
    if beams > 0:
        light_beams(d, [px - 200, px, px + 200], 0, gy - 10, beams * (1 - 0.6 * clamp((t - t_cliff) / 2)), t)
    ground(frame, cy, t)
    d = ImageDraw.Draw(frame, "RGBA")
    tent(d, W * 0.2, gy - 6, 0.8, 1)
    lying_figure(d, px, gy - 4, 300, 1)
    if t >= tl[2][0]:  # light gathers at the head
        k = clamp((t - tl[2][0]) / 1.2) * (1 - clamp((t - t_soul) / 1.0))
        glow_dot(d, px - 140, gy - 40, 10 + 8 * k, k * 0.8)
    if t >= t_soul:
        k = eio((t - t_soul) / max(tl[3][1] - t_soul, 1))
        # the soul gathers like a drop, then rises
        oy = gy - 60 - 420 * k
        if t >= t_cliff:
            oy = min(oy, 760)
        r = 10 + 14 * clamp((t - t_soul) / 0.8)
        soul_orb(d, px + 20 * math.sin(t), oy, r, 1, t)
    return frame


# ---------------------------------------------------------------- PART 2
GATES = [900 + k * 650 for k in range(7)]  # gate heights (world, above horizon)
P2 = [
    ("ПОСЛЕ СМЕРТИ", "куда попадает душа верующего?", ""),
    ("ВОЗНЕСЕНИЕ", "«Чья это благая душа?»", "مَا هَذِهِ الرُّوحُ الطَّيِّبَةُ"),
    ("ИЛЛИЙЙУН", "«Запишите книгу Моего раба в Иллиййун»", "اكْتُبُوا كِتَابَ عَبْدِي فِي عِلِّيِّينَ"),
    ("ВОЗВРАЩЕНИЕ", "главное испытание — в части 3  →", ""),
]


def sky_gate(d, x, y, s, a, open_k, n):
    w, h = 220 * s, 380 * s
    d.rounded_rectangle((x - w / 2 - 22 * s, y - h - 22 * s, x + w / 2 + 22 * s, y), int(w / 2 + 22 * s), outline=rgba(GOLD, a), width=max(3, int(8 * s)))
    dw = w / 2 * (1 - open_k)
    for sd in (-1, 1):
        x0, x1 = (x - w / 2, x - w / 2 + dw) if sd < 0 else (x + w / 2 - dw, x + w / 2)
        if x1 - x0 > 3:
            d.rectangle((x0, y - h + w / 2, x1, y), fill=rgba((150, 110, 50), a * 0.9), outline=rgba(GOLD, a), width=2)
    if open_k > 0:
        d.rounded_rectangle((x - w / 2 + 6, y - h + 6, x + w / 2 - 6, y - 4), int(w / 2), fill=rgba(EMER_L, a * 0.25 * open_k))


def part2(t, si, lt, dur, segs, tl):
    # camera: rises through gates 1-3 in seg 1, 4-7 in seg 2 (first 60%), holds, descends in seg 3
    a1, b1 = tl[1]; a2, b2 = tl[2]; a3, b3 = tl[3]
    top = GATES[6] - 420
    if t < a1:
        cy = 200 + 300 * ease(t / max(a1, 0.1))
    elif t < a2:
        cy = lerp(500, GATES[2] - 420, eio((t - a1) / (a2 - a1)))
    elif t < a3:
        cy = lerp(GATES[2] - 420, top, eio((t - a2) / ((b2 - a2) * 0.6)))
    else:
        cy = lerp(top, 0, eio((t - a3) / max(b3 - a3, 1)))
    frame = sky(cy, t)
    d = ImageDraw.Draw(frame, "RGBA")
    orb_y = 1000 if t < a3 else lerp(1000, HZ + 30 - 60, eio((t - a3) / max(b3 - a3, 1)))
    for n, gh in enumerate(GATES):
        y = HZ + cy - gh
        if -400 < y < H + 450:
            # opens as the soul approaches it from below
            open_k = clamp(((cy + HZ - orb_y) - (gh - 520)) / 250)
            sky_gate(d, W / 2, y, 1.0, 1.0, open_k, n)
            put(frame, RC.plain_text(str(n + 1), RC.serif(46, 700), GOLD + (255,)), W / 2 + 175, y - 330, 0.9)
            d = ImageDraw.Draw(frame, "RGBA")
    for k in range(10):  # clouds at low altitude
        ch = 500 + k * 120
        y = HZ + cy - ch
        if -100 < y < H + 100:
            x = (k * 380 + t * (10 + k * 3)) % (W + 600) - 300
            for j in range(4):
                d.ellipse((x + j * 70 - 90, y - 40 - 15 * (j % 2), x + j * 70 + 90, y + 30), fill=rgba((230, 220, 200), 0.05))
    if t >= a2:  # the seventh heaven: radiance
        k = clamp((t - a2) / 2.0) * (1 - clamp((t - a3) / 1.5))
        glow_dot(d, W / 2, 500, 60 * k + 1, k, (255, 255, 240), n=10, spread=1.1)
    ground(frame, cy, t)
    d = ImageDraw.Draw(frame, "RGBA")
    if HZ + cy < H + 100:
        lying_figure(d, W / 2, HZ + cy + 26, 300, 1)
    soul_orb(d, W / 2 + 18 * math.sin(t), orb_y, 22, 1 - 0.7 * clamp((t - (b3 - 0.6)) / 0.6), t)
    return frame


# ---------------------------------------------------------------- PART 3
P3 = [
    ("ТРИ ВОПРОСА", "их зададут каждому из нас", ""),
    ("ДВА АНГЕЛА", "три вопроса в могиле", "مَنْ رَبُّكَ؟ مَا دِينُكَ؟"),
    ("ОТВЕТ", "твёрдые слова верующего", ""),
    ("«МОЙ РАБ СКАЗАЛ ПРАВДУ»", "могила расширяется, насколько хватает взгляда", "صَدَقَ عَبْدِي"),
    ("БЛАГИЕ ДЕЛА", "«Я — твои благие дела»", ""),
    ("КОРАН 14:27", "твёрдое слово в этой жизни и в Последней", "يُثَبِّتُ اللَّهُ الَّذِينَ آمَنُوا بِالْقَوْلِ الثَّابِتِ"),
    ("ДОСТОВЕРНЫЙ ХАДИС", "передал аль-Бараа ибн Азиб", ""),
    ("ГОТОВЬСЯ СЕГОДНЯ", "эти ответы проживают всю жизнь", ""),
]
SURF = 520     # ground surface line in part 3
CH = (300, 820, 780, 1080)  # grave niche (x0, y0, x1, y1)
_soil = None


def soil():
    global _soil
    if _soil is None:
        yy = np.arange(H, dtype=np.float32)[:, None, None]
        base = np.array((44, 32, 24), np.float32) * (1 - np.clip((yy - SURF) / 1400, 0, 1) * 0.45)
        n = np.asarray(Image.fromarray((rng.random((H // 12, W // 12)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32)[..., None] / 255
        arr = np.broadcast_to(base, (H, W, 3)) * (0.85 + 0.3 * n)
        for k in range(6):  # strata lines
            y0 = SURF + 120 + k * 210
            arr[int(y0):int(y0) + 3] *= 0.7
        im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).rectangle((0, SURF, W, H), fill=255)
        _soil = (im, m)
    return _soil


QA = [("Кто твой Господь?", "Аллах"), ("Какова твоя религия?", "Ислам"), ("Кто этот человек?", "Посланник Аллаха")]


def part3(t, si, lt, dur, segs, tl):
    wide = eio((t - tl[3][0] - 1.5) / 2.5) if t > tl[3][0] else 0
    dawn = eio((t - tl[7][0]) / 2.0) if t > tl[7][0] else 0
    frame = sky(-HZ + SURF + 300 * dawn, t)   # surface sky (sand night)
    soil_im, soil_m = soil()
    frame.paste(soil_im, (0, 0), soil_m)
    d = ImageDraw.Draw(frame, "RGBA")
    d.line((0, SURF, W, SURF), fill=rgba(GOLD, 0.9), width=3)
    d.chord((W / 2 - 160, SURF - 60, W / 2 + 160, SURF + 60), 180, 360, fill=rgba((70, 52, 40), 1), outline=rgba(GOLD, 0.6))  # mound
    # the niche: widens to the edges of the screen; walls fade into emerald light
    x0 = lerp(CH[0], -40, wide); x1 = lerp(CH[2], W + 40, wide)
    y0 = lerp(CH[1], SURF + 40, wide); y1 = lerp(CH[3], 1300, wide)
    inner = mix((18, 13, 10), (24, 70, 58), wide)
    d.rectangle((x0, y0, x1, y1), fill=rgba(inner, 1))
    if wide > 0:  # light of the garden pours in from the door, sparkles drift
        gx_, gy_ = W - 260, y1 - 120
        for k in range(14, 0, -1):
            rr = 60 + k * 70
            d.ellipse((gx_ - rr, gy_ - rr, gx_ + rr, gy_ + rr), fill=rgba((150, 240, 200), wide * 0.035))
        for j in range(26):
            f = (t * 0.12 + j / 26) % 1
            sx = x0 + (j * 97) % max(1, int(x1 - x0))
            sy = y1 - f * (y1 - y0)
            d.ellipse((sx - 3, sy - 3, sx + 3, sy + 3), fill=rgba((220, 255, 235), wide * (1 - f) * 0.8))
    d.rectangle((x0, y0, x1, y1), outline=rgba(GOLD, 0.5 * (1 - wide)), width=3)
    # two beams of light come down through the soil
    beams = clamp((t - tl[1][0]) / 1.2) * (1 - clamp((t - tl[4][0]) / 1.5))
    if beams > 0:
        light_beams(d, [CH[0] + 70, CH[2] - 70], SURF, CH[3] - 10, beams, t, width=70)
    # door to Paradise opens on the right wall
    door = clamp((t - tl[3][0] - 0.8) / 1.5)
    if door > 0:
        dx, dy = x1 - 210 if wide < 0.5 else W - 260, y1
        F.gate(d, dx, dy - 4, door, door, (190, 255, 220), s=0.5)
    # figure: lying, sits up when questioned
    fx, fy = (x0 + x1) / 2 - 40, y1 - 6
    lay = Image.new("RGBA", (W * 2, H * 2), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    if t < tl[1][0] + 1.0:
        lying_figure(ld, fx * 2, fy * 2 - 4, 520, 1)
    else:
        C.figure(ld, fx * 2, fy * 2, 300 * 2, CREAM, 1, facing=1, mode="sit", head_down=0.1)
    if t >= tl[4][0]:  # good deeds: a light figure appears beside him
        k = ease((t - tl[4][0]) / 1.2)
        C.figure(ld, (fx + 230) * 2, fy * 2, 330 * 2, LIGHT, k, facing=-1, front=C.ARMS_DOWN[0], back=C.ARMS_DOWN[1])
    comp(frame, C.glow_layer(lay, 1.3).resize((W, H), Image.LANCZOS))
    # questions and answers, written into the soil above the niche
    d = ImageDraw.Draw(frame, "RGBA")
    qa_a = clamp((t - tl[1][0]) / 0.5) * (1 - clamp((t - tl[3][0]) / 0.6))
    if qa_a > 0:
        a_t = tl[2][0]
        for i, (q, ans) in enumerate(QA):
            qt = tl[1][0] + 0.8 + i * (tl[1][1] - tl[1][0] - 0.8) / 3
            qk = ease((t - qt) / 0.5) * qa_a
            y = 610 + i * 70
            put(frame, RC.plain_text(q, RC.F_DESC, (240, 232, 220, 255)), W / 2 - 120, y, qk)
            at = a_t + 0.3 + i * (tl[2][1] - a_t - 0.3) / 3
            ak = ease((t - at) / 0.5) * qa_a
            put(frame, RC.gold_text(ans, RC.serif(52, 700), tracking=2, glow=0.4), W / 2 + 250, y, ak)
    if dawn > 0:  # final: back to the surface at dawn
        dawn_im = F.path_scene(6 + t, 20, cam=0.35 + 0.1 * dawn, hero_x=0.4, caption=False)
        dawn_im.putalpha(dawn_im.getchannel("A").point(lambda v: int(v * dawn)))
        comp(frame, dawn_im)
    return frame


PARTS = {1: (part1, P1), 2: (part2, P2), 3: (part3, P3)}


def timeline(part):
    tp = os.path.join(HERE, f"timings{part}.json")
    if os.path.exists(tp):
        return json.load(open(tp))["segments"]
    paras = [l.strip() for l in open(os.path.join(HERE, f"part{part}.txt"), encoding="utf-8") if l.strip()]
    t, out = 0.5, []
    for p in paras:
        d = len(p) / 12.5 + 0.3
        out.append([t, t + d]); t += d + 1.0
    return out


def frame_at(part, t):
    fn, meta = PARTS[part]
    tl = TL[part]
    dur_total = tl[-1][1] + 2.5
    si = 0
    for i, (a, b) in enumerate(tl):
        if t >= a - 0.25: si = i
    s0 = 0 if si == 0 else tl[si][0] - 0.25
    s1 = tl[si + 1][0] - 0.25 if si + 1 < len(tl) else dur_total
    frame = fn(t, si, t - s0, s1 - s0, None, tl)
    title, sub, ar = meta[si]
    num = "" if si == 0 else f"{si:02d}"
    src = SRC if si in (2,) or (part == 3 and si in (5, 6)) else ""
    if part == 3 and si == 5:
        src = "Коран 14:27 · аль-Бухари 1369"
    overlay(frame, part, num, title, sub, src, ar, t - s0, s1 - s0, si == len(tl) - 1)
    if si == len(tl) - 1:  # fade out at the very end
        k = eio((t - (dur_total - 0.8)) / 0.8)
        if k > 0:
            comp(frame, Image.new("RGBA", (W, H), (0, 0, 0, int(255 * k))))
    return frame


TL = {p: timeline(p) for p in PARTS}


def chunk(args):
    part, a0, a1, path = args
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for fi in range(a0, a1):
        p.stdin.write(frame_at(part, fi / FPS).convert("RGB").tobytes())
    p.stdin.close(); p.wait()
    return path


if __name__ == "__main__":
    part, out = int(sys.argv[1]), sys.argv[2]
    if len(sys.argv) > 3 and sys.argv[3] == "stills":
        for tt in [float(x) for x in sys.argv[4].split(",")]:
            frame_at(part, tt).convert("RGB").save(f"{out}_{tt:05.2f}.jpg", quality=88)
        sys.exit()
    dur = TL[part][-1][1] + 2.5
    nf = int(dur * FPS)
    step = math.ceil(nf / 4)
    jobs = [(part, i * step, min(nf, (i + 1) * step), f"{out}.part{i}.mp4") for i in range(4)]
    with Pool(4) as pool:
        parts = pool.map(chunk, jobs)
    lst = out + ".list.txt"
    with open(lst, "w") as f:
        for p_ in parts: f.write(f"file '{os.path.abspath(p_)}'\n")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", out], check=True)
    for p_ in parts: os.remove(p_)
    os.remove(lst)
    print("done", out, f"{dur:.1f}s")
