"""Re-edit: same voiceover, new motion-graphics visuals. 1080x1920 @30fps."""
import math, sys, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from multiprocessing import Pool

W, H, FPS = 1080, 1920, 30
DUR = 116.48
NF = int(DUR * FPS)
FD = "/usr/share/fonts/opentype/inter/"
F_TITLE = ImageFont.truetype(FD + "InterDisplay-Bold.otf", 104)
F_BIG = ImageFont.truetype(FD + "InterDisplay-Bold.otf", 300)
F_SUB = ImageFont.truetype(FD + "Inter-SemiBold.otf", 50)
F_CARD = ImageFont.truetype(FD + "Inter-Bold.otf", 46)
F_TAG = ImageFont.truetype(FD + "InterDisplay-Bold.otf", 120)
F_SMALL = ImageFont.truetype(FD + "Inter-Medium.otf", 30)

GOLD = (243, 196, 109)
CREAM = (250, 244, 232)
LINE = (236, 214, 170)
CX, CY = W // 2, 700          # icon centre
TITLE_Y = 1150
SUB_Y = 1530

# ---------------------------------------------------------------- data
SCENES = [  # start, end, title, icon, extra
    (0.00, 7.47, "Пойти на прогулку", "path", {}),
    (7.47, 12.93, "Что занимает мысли?", "orbits", {}),
    (12.93, 16.20, "Что я собой представляю?", "pulse", {}),
    (16.20, 21.57, "Кто я?", "cards2", {"a": "Кто я?", "b": "Что я?", "tb": 19.6}),
    (21.57, 27.53, "Плоть и кости", "person", {}),
    (27.53, 31.87, "Имя", "tag", {}),
    (31.87, 42.63, "Жизненный опыт", "stack", {}),
    (42.63, 51.70, "Пережитое", "scatter", {}),
    (51.70, 55.87, "Воспоминания", "fan", {}),
    (55.87, 59.77, "Нечто большее", "rings", {}),
    (59.77, 69.33, "7 небес", "seven", {}),
    (69.33, 75.37, "Тёмные стороны", "dark", {}),
    (75.37, 80.93, "Животное и духовное", "cards2", {"a": "Животное", "b": "Духовное", "tb": 79.1}),
    (80.93, 88.33, "Всё одновременно", "atom", {}),
    (88.33, 96.20, "Коран и PlayStation", "cards2", {"a": "Коран", "b": "PlayStation", "tb": 92.1}),
    (96.20, 100.07, "Как это уживается во мне?", "atom", {}),
    (100.07, 105.60, "Кто создал меня?", "rays", {}),
    (105.60, 111.87, "Задумайтесь", "path", {}),
    (111.87, DUR + 1, "Осознанность", "sunrise", {}),
]

SUBS = [  # start, end, text, accent words
    (0.05, 3.80, "На самом деле одно из самых сложных, но в то же время глубоко", ["сложных,"]),
    (3.87, 7.35, "духовных занятий — это просто пойти на прогулку и подумать о себе.", ["прогулку"]),
    (7.47, 11.65, "Я имею в виду не мысли о ваших чувствах или о том, что кто-то с вами сделал.", ["чувствах"]),
    (11.73, 12.58, "Я говорю не об этом.", []),
    (12.63, 14.62, "Нужно глубоко задуматься о себе.", ["задуматься"]),
    (14.67, 16.15, "Что я собой представляю?", ["представляю?"]),
    (16.20, 21.50, "Можно легко ответить на вопрос «кто я» — Нуман. Но что я такое?", ["такое?"]),
    (21.57, 24.00, "Неужели я — это просто набор плоти и костей?", ["костей?"]),
    (25.57, 27.48, "Это всё, что я из себя представляю?", []),
    (27.53, 30.45, "Или я — это просто имя, которое дали мне родители, и всё.", ["имя,"]),
    (31.87, 35.35, "Или я лишь набор жизненного опыта, как сказал бы мне психотерапевт.", ["опыта,"]),
    (39.55, 40.15, "И на этом всё.", []),
    (42.63, 45.28, "Или я — это всего лишь череда травмирующих событий, которые", ["травмирующих"]),
    (45.33, 49.28, "сделали меня тем сломленным человеком, которым я сейчас являюсь.", ["сломленным"]),
    (49.33, 51.65, "Всего лишь куча пережитого опыта.", ["пережитого"]),
    (51.70, 55.80, "Я — это просто совокупность моих воспоминаний, и это всё, что во мне есть.", ["воспоминаний,"]),
    (55.87, 59.70, "Есть ли во мне нечто большее, чем мои эмоции и физическая оболочка?", ["большее,"]),
    (59.77, 63.78, "Есть ли внутри меня что-то небесное, что-то, что исходит из-за пределов", ["небесное,"]),
    (63.83, 67.60, "даже семи небес, что было вложено в меня и тянется к чему-то великому?", ["семи", "небес,"]),
    (67.67, 69.28, "Это тоже входит в мою сущность.", ["сущность."]),
    (69.33, 71.92, "Внутри меня есть тёмные и низменные стороны.", ["тёмные"]),
    (71.97, 74.15, "Часть меня полна уныния и бессмысленности.", ["уныния"]),
    (75.37, 79.02, "Во мне есть что-то животное, но в то же время во мне есть", ["животное,"]),
    (79.07, 80.62, "и что-то духовно возвышенное.", ["духовно"]),
    (80.67, 85.38, "Всё это тоже находится внутри меня, и я представляю собой всё это одновременно.", ["одновременно."]),
    (85.43, 88.28, "Я устроен довольно сложно, действительно сложно.", ["сложно,", "сложно."]),
    (88.33, 92.02, "Я тот, кто хочет размышлять над Кораном, и в то же время хочу", ["Кораном,"]),
    (92.07, 93.92, "поиграть в новую игру на PlayStation.", ["PlayStation."]),
    (95.93, 96.98, "Всё это одновременно.", ["одновременно."]),
    (97.87, 98.95, "Как это уживается во мне?", ["уживается"]),
    (99.80, 101.42, "Кто создал меня таким сложным?", ["сложным?"]),
    (102.30, 103.38, "Кто создал меня?", ["создал"]),
    (103.43, 104.72, "Это очень глубокий вопрос.", ["глубокий"]),
    (105.60, 106.72, "Просто задумайтесь об этом.", ["задумайтесь"]),
    (111.87, 114.20, "И тогда мы с вами станем гораздо более осознанными.", ["осознанными."]),
]

# ---------------------------------------------------------------- helpers
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_io(x): x = clamp(x); return x * x * (3 - 2 * x)
def lerp(a, b, t): return a + (b - a) * t
def col(c, a): return (c[0], c[1], c[2], int(clamp(a) * 255))

def scene_at(t):
    for i, s in enumerate(SCENES):
        if s[0] <= t < s[1]: return i, s
    return len(SCENES) - 1, SCENES[-1]

# ---------------------------------------------------------------- static layers
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
BASE = np.zeros((H, W, 3), np.float32)
g = yy / H
for k, (c0, c1) in enumerate(zip((10, 13, 24), (6, 8, 14))):
    BASE[..., k] = lerp(c0, c1, g)
r = np.sqrt((xx - CX) ** 2 + ((yy - CY) * 0.85) ** 2)
GLOW = np.exp(-(r / 430) ** 2)[..., None] * np.array(GOLD, np.float32)[None, None] / 255
GLOW2 = np.exp(-(r / 900) ** 2)[..., None] * np.array((120, 110, 160), np.float32)[None, None] / 255
vig = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2)
VIG = np.clip(1 - 0.55 * vig ** 2, 0.25, 1)[..., None]
rng = np.random.default_rng(7)
GRAIN = [rng.normal(0, 4.0, (H // 2, W // 2)).astype(np.float32) for _ in range(6)]
PART = rng.random((70, 4))  # x, y, speed, size

def background(t, glow_k, dark_k, bright_k):
    img = BASE * (1 - 0.45 * dark_k) + GLOW * (38 * glow_k + 140 * bright_k) + GLOW2 * (30 * (1 - dark_k) + 60 * bright_k)
    img = img * VIG
    gr = GRAIN[int(t * 15) % 6]
    img += np.repeat(np.repeat(gr, 2, 0), 2, 1)[..., None]
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")

def particles(d, t, a):
    for px, py, sp, sz in PART:
        y = (py * H - t * (12 + 30 * sp)) % H
        x = px * W + 18 * math.sin(t * 0.4 + py * 20)
        tw = 0.5 + 0.5 * math.sin(t * (1 + sp * 2) + px * 30)
        rr = 1.2 + 2.2 * sz
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=col(LINE, a * (0.08 + 0.25 * tw)))

# ---------------------------------------------------------------- icon drawing (on 2x supersampled layer)
SS = 2
IW = 900  # icon canvas (logical)

def glow_dot(d, x, y, rad, a, core=GOLD):
    for k in range(6, 0, -1):
        rr = rad * (1 + k * 0.55)
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=col(core, a * 0.05))
    d.ellipse((x - rad, y - rad, x + rad, y + rad), fill=col(core, a))

def ell(d, x, y, rx, ry, a, w=2.4, c=LINE):
    d.ellipse((x - rx, y - ry, x + rx, y + ry), outline=col(c, a), width=int(w * SS))

def rot_ellipse(d, x, y, rx, ry, ang, a, w=2.2, n=120):
    ca, sa = math.cos(ang), math.sin(ang)
    pts = []
    for i in range(n + 1):
        th = 2 * math.pi * i / n
        ex, ey = rx * math.cos(th), ry * math.sin(th)
        pts.append((x + ex * ca - ey * sa, y + ex * sa + ey * ca))
    d.line(pts, fill=col(LINE, a), width=int(w * SS), joint="curve")

def rrect(d, box, rad, a, fill=None, w=2.4, c=LINE):
    d.rounded_rectangle(box, rad, fill=fill, outline=col(c, a), width=int(w * SS))

def rot_poly(cx, cy, w, h, ang):
    ca, sa = math.cos(ang), math.sin(ang)
    out = []
    for px, py in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
        out.append((cx + px * ca - py * sa, cy + px * sa + py * ca))
    return out

def card_poly(d, cx, cy, w, h, ang, a, fill_a=0.55):
    pts = rot_poly(cx, cy, w, h, ang)
    d.polygon(pts, fill=(22, 24, 34, int(255 * a * fill_a)))
    d.line(pts + [pts[0]], fill=col(LINE, a * 0.9), width=int(2.2 * SS), joint="curve")

def text_center(d, x, y, s, font, fill):
    bb = d.textbbox((0, 0), s, font=font)
    pos = (x - (bb[2] + bb[0]) / 2, y - (bb[3] + bb[1]) / 2)
    d.text(pos, s, font=font, fill=fill)
    return pos

FONT_CACHE = {}
def sfont(path, size):
    k = (path, size)
    if k not in FONT_CACHE: FONT_CACHE[k] = ImageFont.truetype(path, size)
    return FONT_CACHE[k]

def draw_icon(kind, lt, dur, a, t, extra):
    S = IW * SS
    lay = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    c = S / 2
    u = SS  # unit
    p = ease(lt / 0.9)
    if kind == "path":
        hz = c - 120 * u
        for k in range(-3, 4):
            x0 = c + k * 230 * u
            d.line((c + k * 6 * u, hz, x0, S), fill=col(LINE, a * (0.25 if k else 0.0)), width=int(1.6 * u))
        for i in range(14):
            f = ((i / 14) + lt * 0.12) % 1
            yv = hz + (S - hz) * f ** 2
            alpha = a * f * 0.8
            hw = 40 * u * f ** 2 + 2 * u
            d.line((c - hw, yv, c + hw, yv), fill=col(LINE, alpha * 0.5), width=int(1.6 * u))
        for i in range(6):  # footsteps
            f = ((i / 6) + lt * 0.22) % 1
            yv = S - (S - hz) * (1 - (1 - f) ** 2)
            sc = (1 - f) * 22 * u + 3 * u
            side = -1 if i % 2 else 1
            xv = c + side * sc * 1.1
            d.ellipse((xv - sc * 0.55, yv - sc, xv + sc * 0.55, yv + sc), fill=col(GOLD, a * (1 - f) * 0.7))
        glow_dot(d, c, hz - 20 * u, (26 + 4 * math.sin(lt * 2)) * u, a)
    elif kind == "orbits":
        glow_dot(d, c, c, 40 * u, a)
        for k in range(4):
            rad = (90 + k * 60) * u * p
            ang = lt * (0.5 + 0.25 * k) * (1 if k % 2 else -1) + k
            rot_ellipse(d, c + 12 * u * math.sin(lt + k), c, rad, rad * (0.8 + 0.06 * k), ang, a * (0.9 - k * 0.15))
            th = lt * (1.2 - 0.2 * k) + k * 2
            ox, oy = c + rad * math.cos(th), c + rad * 0.85 * math.sin(th)
            d.ellipse((ox - 7 * u, oy - 7 * u, ox + 7 * u, oy + 7 * u), fill=col(GOLD, a))
    elif kind == "pulse":
        glow_dot(d, c, c, (44 + 6 * math.sin(lt * 4)) * u, a)
        for k in range(4):
            f = ((lt * 0.7) + k / 4) % 1
            ell(d, c, c, (50 + 330 * f) * u, (50 + 330 * f) * u, a * (1 - f) * 0.8)
    elif kind == "cards2":
        tb = extra["tb"] - (lt + 0)  # time until second highlight (relative)
        q = ease((lt - (extra["tb"] - extra["t0"])) / 0.5) if "t0" in extra else 0
        cw, ch = 300 * u, 300 * u
        sep = lerp(0, 190, ease(lt / 0.8)) * u
        for idx, lab in enumerate((extra["a"], extra["b"])):
            x = c + (-1 if idx == 0 else 1) * sep
            hi = q if idx == 1 else 0
            sc = 1 + 0.08 * hi
            box = (x - cw / 2 * sc, c - ch / 2 * sc, x + cw / 2 * sc, c + ch / 2 * sc)
            if idx == 1 and sep < 5 * u: continue
            fill = (int(lerp(22, GOLD[0], hi)), int(lerp(24, GOLD[1], hi)), int(lerp(34, GOLD[2], hi)), int(255 * a * lerp(0.6, 0.95, hi)))
            rrect(d, box, 36 * u, a * (0.9 if idx == 0 or hi else 0.45), fill=fill)
            # diamond glyph
            gx, gy, gr = x, c - 40 * u, 38 * u * sc
            d.polygon([(gx, gy - gr), (gx + gr, gy), (gx, gy + gr), (gx - gr, gy)], outline=col((20, 20, 28) if hi > 0.5 else LINE, a), width=int(2.4 * u))
            fsz = 46 if len(lab) < 9 else 40
            text_center(d, x, c + 75 * u, lab, sfont(FD + "Inter-Bold.otf", int(fsz * u * sc)),
                        col((20, 20, 28) if hi > 0.5 else CREAM, a))
    elif kind == "person":
        hy = c - 140 * u
        n = 22
        for i in range(n):
            f = i / n
            rev = clamp((lt * 1.6 - f) * 3)
            y = hy - 120 * u + i * 26 * u
            # half-width of silhouette at height y
            if y < hy + 120 * u:
                dy = (y - hy) / (120 * u)
                hw = 100 * u * math.sqrt(max(0, 1 - dy * dy))
            else:
                k = (y - (hy + 150 * u)) / (260 * u)
                hw = (110 + 230 * math.sqrt(clamp(k))) * u if y > hy + 150 * u else 50 * u
            wob = 6 * u * math.sin(lt * 2 + i * 0.6)
            d.line((c - hw * rev + wob, y, c + hw * rev + wob, y), fill=col(LINE, a * 0.75), width=int(2 * u))
        glow_dot(d, c, hy, 10 * u, a * 0.9)
    elif kind == "tag":
        sw = math.sin(lt * 2.2) * 0.12 * math.exp(-lt * 0.35) - 0.08
        tw, th = 560 * u, 240 * u
        tagl = Image.new("RGBA", (int(tw + 40 * u), int(th + 40 * u)), (0, 0, 0, 0))
        td = ImageDraw.Draw(tagl)
        box = (20 * u, 20 * u, 20 * u + tw, 20 * u + th)
        td.rounded_rectangle(box, 40 * u, fill=(24, 26, 36, int(240 * a)), outline=col(LINE, a), width=int(2.6 * u))
        td.ellipse((50 * u, 50 * u, 74 * u, 74 * u), outline=col(LINE, a), width=int(2.4 * u))
        text_center(td, 20 * u + tw / 2, 20 * u + th / 2, "Нуман", sfont(FD + "InterDisplay-Bold.otf", 120 * u), col(GOLD, a))
        tagl = tagl.rotate(math.degrees(sw), resample=Image.BICUBIC, expand=True)
        drop = int((1 - ease(lt / 0.7)) * -200 * u)
        d.line((c - 200 * u, 0, c - 230 * u, c - th / 2 + drop), fill=col(LINE, a * 0.5), width=int(2 * u))
        lay.alpha_composite(tagl, (int(c - tagl.width / 2), int(c - tagl.height / 2 + drop)))
    elif kind in ("stack", "scatter", "fan"):
        n = 7
        for i in range(n):
            appear = ease((lt - i * 0.35) / 0.5) if kind == "stack" else ease((lt - i * 0.12) / 0.5)
            if appear <= 0: continue
            if kind == "stack":
                x, y, ang = c + (i - 3) * 14 * u, c + 140 * u - i * 46 * u * appear, -0.18 + 0.01 * math.sin(lt + i)
                cw, chh = 380 * u, 220 * u
            elif kind == "scatter":
                rs = np.random.default_rng(i)
                tx, ty = rs.uniform(-230, 230) * u, rs.uniform(-200, 200) * u
                shake = 3 * u * math.sin(lt * 23 + i * 7) * (1 if 2.5 < lt < 7 else 0.3)
                x, y = c + tx * appear + shake, c + ty * appear
                ang = rs.uniform(-0.6, 0.6) * appear + 0.05 * math.sin(lt * 0.8 + i)
                cw, chh = 230 * u, 300 * u
            else:
                ang = (i - 3) * 0.2 * appear + 0.04 * math.sin(lt + i)
                x, y = c + math.sin(ang) * 260 * u, c + 140 * u - math.cos(ang) * 260 * u + 120 * u
                cw, chh = 230 * u, 320 * u
            card_poly(d, x, y, cw, chh, ang, a * appear)
            if kind == "fan":
                pts = rot_poly(x, y - 40 * u, 150 * u, 110 * u, ang)
                d.polygon(pts, outline=col(GOLD, a * appear * 0.7), width=int(2 * u))
        if kind == "scatter":
            # crack line
            cp = clamp((lt - 2.7) / 0.6)
            if cp > 0:
                pts = [(c - 300 * u, c - 260 * u), (c - 120 * u, c - 90 * u), (c - 160 * u, c + 20 * u), (c + 40 * u, c + 120 * u), (c + 10 * u, c + 220 * u), (c + 260 * u, c + 330 * u)]
                m = max(2, int(len(pts) * cp))
                d.line(pts[:m], fill=col(GOLD, a * 0.85), width=int(3 * u), joint="curve")
    elif kind == "rings":
        glow_dot(d, c, c, 36 * u, a)
        for k in range(5):
            br = 1 + 0.05 * math.sin(lt * 2 - k * 0.7)
            rad = (80 + 70 * k) * u * br * ease((lt - k * 0.15) / 0.7)
            ell(d, c, c, rad, rad, a * (0.85 - k * 0.13))
    elif kind == "seven":
        glow_dot(d, c, c, 34 * u, a)
        shown = clamp((lt - 0.2) / 4.0) * 7
        for k in range(7):
            q = clamp(shown - k)
            if q <= 0: continue
            rad = (70 + 45 * k) * u * (0.85 + 0.15 * ease(q)) * (1 + 0.015 * math.sin(lt * 2 + k))
            ell(d, c, c, rad, rad, a * ease(q) * (0.95 - k * 0.08), w=2.2 + (1.2 if k == int(shown) - 1 else 0))
    elif kind == "dark":
        fl = 0.55 + 0.25 * math.sin(lt * 9) * math.sin(lt * 3.1)
        glow_dot(d, c, c, 26 * u, a * fl, core=(150, 140, 170))
        for k in range(4):
            rad = (100 + 70 * k) * u
            rot_ellipse(d, c, c, rad, rad * 0.97, lt * 0.1 * (k + 1), a * 0.25 * (1 - k * 0.15))
        for i in range(40):  # creeping dark smoke dots
            rs = np.random.default_rng(100 + i)
            ang = rs.uniform(0, 6.28) + lt * 0.05
            rr = (420 - (lt * 40 + rs.uniform(0, 200)) % 300) * u
            x, y = c + rr * math.cos(ang), c + rr * math.sin(ang)
            d.ellipse((x - 4 * u, y - 4 * u, x + 4 * u, y + 4 * u), fill=col((150, 140, 170), a * 0.35))
    elif kind == "atom":
        glow_dot(d, c, c, 34 * u, a)
        for k in range(3):
            ang = k * math.pi / 3 + lt * 0.25
            rx, ry = 290 * u * ease(lt / 0.8), 105 * u
            rot_ellipse(d, c, c, rx, ry, ang, a * 0.85)
            th = lt * (1.6 + 0.3 * k) + k * 2.1
            ex, ey = rx * math.cos(th), ry * math.sin(th)
            ca, sa = math.cos(ang), math.sin(ang)
            ox, oy = c + ex * ca - ey * sa, c + ex * sa + ey * ca
            d.ellipse((ox - 9 * u, oy - 9 * u, ox + 9 * u, oy + 9 * u), fill=col(GOLD, a))
    elif kind == "rays":
        glow_dot(d, c, c, 42 * u, a)
        n = 24
        for i in range(n):
            ang = 2 * math.pi * i / n + lt * 0.15
            l0 = 90 * u
            l1 = l0 + (120 + 140 * (0.5 + 0.5 * math.sin(lt * 1.8 + i * 1.7))) * u * ease(lt / 1.0)
            d.line((c + l0 * math.cos(ang), c + l0 * math.sin(ang), c + l1 * math.cos(ang), c + l1 * math.sin(ang)),
                   fill=col(LINE, a * 0.6), width=int(2 * u))
        ell(d, c, c, 380 * u, 380 * u, a * 0.25)
    elif kind == "sunrise":
        g = ease(lt / 3.0)
        glow_dot(d, c, c, (40 + 50 * g) * u, a)
        for k in range(5):
            f = ((lt * 0.35) + k / 5) % 1
            ell(d, c, c, (90 + 340 * f) * u, (90 + 340 * f) * u, a * (1 - f) * 0.6)
    return lay.resize((IW, IW), Image.LANCZOS)

# ---------------------------------------------------------------- text
TXT_CACHE = {}
def title_img(s):
    if s in TXT_CACHE: return TXT_CACHE[s]
    words = s.split()
    lines, cur = [], ""
    for w_ in words:
        tst = (cur + " " + w_).strip()
        if F_TITLE.getlength(tst) > W - 140 and cur:
            lines.append(cur); cur = w_
        else: cur = tst
    lines.append(cur)
    lh = 118
    im = Image.new("RGBA", (W, lh * len(lines) + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, ln in enumerate(lines):
        # "7" accent
        pos = text_center(d, W / 2, 20 + lh * i + lh / 2, ln, F_TITLE, CREAM)
        if i == 0 and s.startswith("7 "):
            d.text(pos, "7", font=F_TITLE, fill=GOLD)
    TXT_CACHE[s] = im
    return im

def layout_sub(text):
    words = text.split()
    lines, cur = [], []
    for w_ in words:
        tst = " ".join(cur + [w_])
        if F_SUB.getlength(tst) > W - 200 and cur:
            lines.append(cur); cur = [w_]
        else: cur.append(w_)
    lines.append(cur)
    return lines

def word_times(s0, s1, words):
    L = [len(w_) + 2 for w_ in words]
    tot = sum(L); acc = 0; out = []
    span = (s1 - s0) * 0.92
    for l in L:
        out.append(s0 + span * acc / tot); acc += l
    return out

def draw_sub(frame, t):
    for s0, s1, text, acc in SUBS:
        if s0 - 0.05 <= t <= s1 + 0.12:
            break
    else:
        return
    a = ease((t - s0 + 0.05) / 0.18) * (1 - ease((t - s1) / 0.12))
    lines = layout_sub(text)
    words = [w_ for ln in lines for w_ in ln]
    wt = word_times(s0, s1, words)
    lh = 66
    bh = lh * len(lines) + 56
    bw = max(F_SUB.getlength(" ".join(ln)) for ln in lines) + 90
    rise = (1 - ease((t - s0 + 0.05) / 0.25)) * 24
    y0 = SUB_Y + rise
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((W / 2 - bw / 2, y0, W / 2 + bw / 2, y0 + bh), 34, fill=(8, 9, 14, int(185 * a)),
                        outline=(255, 255, 255, int(18 * a)), width=2)
    idx = 0
    space = F_SUB.getlength(" ")
    for li, ln in enumerate(lines):
        lw = F_SUB.getlength(" ".join(ln))
        x = W / 2 - lw / 2
        y = y0 + 28 + lh * li
        for w_ in ln:
            on = ease((t - wt[idx]) / 0.15)
            is_acc = w_ in acc
            base = GOLD if is_acc else CREAM
            alpha = a * (0.38 + 0.62 * on)
            dy = (1 - on) * 6
            d.text((x, y + dy), w_, font=F_SUB, fill=col(base, alpha))
            if is_acc and on > 0:
                ulw = F_SUB.getlength(w_.rstrip(",.?!»")) * on
                d.line((x, y + 60, x + ulw, y + 60), fill=col(GOLD, a * 0.8), width=3)
            x += F_SUB.getlength(w_) + space
            idx += 1
    frame.alpha_composite(lay)

# ---------------------------------------------------------------- frame
def render(fi):
    t = fi / FPS
    si, (s0, s1, title, kind, extra) = scene_at(t)
    lt = t - s0
    dur = s1 - s0
    a_in = ease(lt / 0.45)
    a_out = 1 - ease_io((lt - (dur - 0.30)) / 0.30) if si < len(SCENES) - 1 else 1
    if si == len(SCENES) - 1:
        a_out = 1 - ease_io((t - (DUR - 0.8)) / 0.8)
    a = a_in * a_out
    dark_k = 0.0
    if kind == "dark": dark_k = ease(lt / 0.8) * (1 - ease((lt - dur + 0.6) / 0.6))
    bright_k = ease(lt / 2.5) * 0.9 if kind == "sunrise" else 0.0
    glow_k = (0.6 + 0.4 * a) * (1 - 0.7 * dark_k)
    frame = background(t, glow_k, dark_k, bright_k * a_out)
    d = ImageDraw.Draw(frame)
    particles(d, t, 1 - 0.6 * dark_k)

    ex = dict(extra)
    if kind == "cards2": ex["t0"] = s0
    icon = draw_icon(kind, lt, dur, a, t, ex)
    zoom = 0.9 + 0.1 * ease(lt / 0.6) + 0.03 * (lt / dur)
    sz = int(IW * zoom)
    icon = icon.resize((sz, sz), Image.BICUBIC)
    floaty = 8 * math.sin(t * 1.3)
    frame.alpha_composite(icon, (int(CX - sz / 2), int(CY - sz / 2 + floaty)))

    # title: rise + tracking-like scale
    ti = title_img(title)
    ta = ease((lt - 0.12) / 0.45) * a_out
    if ta > 0:
        sc = 1.06 - 0.06 * ease((lt - 0.12) / 0.6)
        tw_, th_ = int(ti.width * sc), int(ti.height * sc)
        tim = ti.resize((tw_, th_), Image.BICUBIC)
        if ta < 1:
            al = np.array(tim.getchannel("A"), np.float32) * ta
            tim.putalpha(Image.fromarray(al.astype(np.uint8)))
        rise = (1 - ease((lt - 0.12) / 0.5)) * 40
        frame.alpha_composite(tim, (int(W / 2 - tw_ / 2), int(TITLE_Y - th_ / 2 + rise)))

    draw_sub(frame, t)

    # progress segments (story-style) at top
    d = ImageDraw.Draw(frame)
    n = len(SCENES); gap = 6; x0 = 60; tot = W - 120
    segw = (tot - gap * (n - 1)) / n
    for k in range(n):
        xa = x0 + k * (segw + gap)
        d.rounded_rectangle((xa, 92, xa + segw, 98), 3, fill=(255, 255, 255, 40))
        f = 1 if k < si else (clamp(lt / dur) if k == si else 0)
        if f > 0: d.rounded_rectangle((xa, 92, xa + max(6, segw * f), 98), 3, fill=col(GOLD, 0.9))
    return frame.convert("RGB").tobytes()

def chunk(args):
    a0, a1, path = args
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for fi in range(a0, a1):
        p.stdin.write(render(fi))
    p.stdin.close(); p.wait()
    return path

if __name__ == "__main__":
    out = sys.argv[1]
    if len(sys.argv) > 2 and sys.argv[2] == "stills":
        for tt in [float(x) for x in sys.argv[3].split(",")]:
            Image.frombytes("RGB", (W, H), render(int(tt * FPS))).save(f"{out}/still_{tt:06.2f}.jpg", quality=88)
        sys.exit()
    nproc = 4
    step = math.ceil(NF / nproc)
    jobs = [(i * step, min(NF, (i + 1) * step), f"{out}/part{i}.mp4") for i in range(nproc)]
    with Pool(nproc) as pool:
        parts = pool.map(chunk, jobs)
    with open(f"{out}/list.txt", "w") as f:
        for p_ in parts: f.write(f"file '{os.path.abspath(p_)}'\n")
    print("done")
