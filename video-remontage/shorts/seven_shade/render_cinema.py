"""'Cinema' style for Islamic shorts: night sky, milky way, shooting stars,
dunes with a golden horizon, gold serif titles, Arabic text of the source,
illustrations standing on the horizon, slide transitions.

Content: the hadith of the seven in the shade (Bukhari 660, Muslim 1031).
Timing: shares SEGMENTS / timings.json with render_seven.py.

usage: python3 render_cinema.py OUT_DIR [stills t1,t2,...]
"""
import math, os, sys, subprocess
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import characters as C
from render_seven import SEGMENTS, TIMES, SCENES, DUR  # shared timeline

W, H, FPS = 1080, 1920, 30
NF = int(DUR * FPS)
FONTS = os.path.abspath(os.path.join(HERE, "..", "..", "fonts"))
INTER = "/usr/share/fonts/opentype/inter/"


def serif(size, wght=700):
    f = ImageFont.truetype(os.path.join(FONTS, "CormorantGaramond[wght].ttf"), size)
    f.set_variation_by_axes([wght])
    return f


F_AR = ImageFont.truetype(os.path.join(FONTS, "AmiriQuran-Regular.ttf"), 50)
F_KICK = ImageFont.truetype(INTER + "Inter-Bold.otf", 30)
F_DESC = ImageFont.truetype(INTER + "Inter-Medium.otf", 40)
F_SRC = ImageFont.truetype(INTER + "Inter-SemiBold.otf", 27)
F_CNT, F_CNT_S = serif(64, 700), serif(30, 600)

GOLD_HI, GOLD_LO = np.array((255, 236, 186), np.float32), np.array((196, 140, 62), np.float32)
GOLD = (236, 200, 132)
CREAM = (255, 240, 205)
HZ = 1060          # horizon line
TXT_Y = 1210       # name baseline area

# per segment: counter, kicker, name, sub, desc, source, arabic
CONTENT = {
    "hook": (0, "", "СУДНЫЙ ДЕНЬ", "", "Солнце приблизится к людям,\nи не будет тени, кроме тени Аллаха", "Муслим 2864 · аль-Бухари 660",
             "يَوْمَ لاَ ظِلَّ إِلاَّ ظِلُّهُ"),
    "q": (0, "", "7 ЛЮДЕЙ", "ПОД ТЕНЬЮ АЛЛАХА", "Ты среди них?", "",
          "سَبْعَةٌ يُظِلُّهُمُ اللَّهُ فِي ظِلِّهِ"),
    "1": (1, "ПЕРВЫЙ", "ПРАВИТЕЛЬ", "", "справедливый правитель", "аль-Бухари 660 · Муслим 1031", "الإِمَامُ العَادِلُ"),
    "2": (2, "ВТОРОЙ", "ЮНОША", "", "вырос в поклонении\nсвоему Господу", "аль-Бухари 660 · Муслим 1031", "وَشَابٌّ نَشَأَ فِي عِبَادَةِ رَبِّهِ"),
    "3": (3, "ТРЕТИЙ", "СЕРДЦЕ", "", "привязано к мечетям", "аль-Бухари 660 · Муслим 1031", "وَرَجُلٌ قَلْبُهُ مُعَلَّقٌ فِي المَسَاجِدِ"),
    "4": (4, "ЧЕТВЁРТЫЙ", "ДВОЕ", "", "полюбили друг друга ради Аллаха,\nвстретились и расстались ради Него", "аль-Бухари 660 · Муслим 1031",
          "وَرَجُلاَنِ تَحَابَّا فِي اللَّهِ"),
    "5": (5, "ПЯТЫЙ", "«Я БОЮСЬ АЛЛАХА»", "", "его позвала знатная и красивая\nженщина, а он отказался", "аль-Бухари 660 · Муслим 1031",
          "فَقَالَ إِنِّي أَخَافُ اللَّهَ"),
    "6": (6, "ШЕСТОЙ", "МИЛОСТЫНЯ", "", "так скрытно, что левая рука\nне знала, что раздала правая", "аль-Бухари 660 · Муслим 1031",
          "حَتَّى لاَ تَعْلَمَ شِمَالُهُ مَا تُنْفِقُ يَمِينُهُ"),
    "7": (7, "СЕДЬМОЙ", "СЛЁЗЫ", "", "вспомнил Аллаха наедине,\nи глаза наполнились слезами", "аль-Бухари 660 · Муслим 1031",
          "وَرَجُلٌ ذَكَرَ اللَّهَ خَالِيًا فَفَاضَتْ عَيْنَاهُ"),
    "src": (0, "ПЕРЕДАЛ АБУ ХУРАЙРА", "ДОСТОВЕРНЫЙ", "ХАДИС", "аль-Бухари № 660 · Муслим № 1031", "", ""),
    "cta": (0, "", "СТАНЬ ОДНИМ", "ИЗ СЕМЕРЫХ", "Отправь тому, кого любишь\nради Аллаха", "", ""),
}


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def eio(x): x = clamp(x); return x * x * (3 - 2 * x)
def lerp(a, b, t): return a + (b - a) * t
def rgba(c, a): return (int(c[0]), int(c[1]), int(c[2]), int(clamp(a) * 255))


# ------------------------------------------------------------------ static sky / ground
rng = np.random.default_rng(3)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
top, mid, low = np.array((14, 12, 40)), np.array((34, 30, 82)), np.array((52, 40, 96))
g = np.clip(yy / HZ, 0, 1)[..., None]
SKY = np.where(g < 0.7, top + (mid - top) * (g / 0.7), mid + (low - mid) * ((g - 0.7) / 0.3)).astype(np.float32)
# milky way: diagonal band of soft noise
band = np.exp(-(((xx * 0.55 + yy * 0.85) - 1100) / 260) ** 2)
noise = Image.fromarray((rng.random((H // 8, W // 8)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(18))
nz = np.asarray(noise, np.float32) / 255
SKY += (band * (0.5 + nz))[..., None] * np.array((60, 52, 110), np.float32) * 0.55
# horizon haze
SKY += np.exp(-((yy - HZ) / 90) ** 2)[..., None] * np.array((70, 50, 60), np.float32)
SKY = np.clip(SKY, 0, 255)
sky_img = Image.fromarray(SKY.astype(np.uint8)).convert("RGBA")
sd = ImageDraw.Draw(sky_img)
for _ in range(900):  # static faint stars
    x, y = rng.uniform(0, W), rng.uniform(0, HZ - 20)
    b = rng.uniform(0.15, 0.6) * (1.3 if abs((x * 0.55 + y * 0.85) - 1100) < 300 else 1)
    r = rng.choice([0.6, 0.9, 1.3], p=[0.6, 0.3, 0.1])
    sd.ellipse((x - r, y - r, x + r, y + r), fill=rgba((235, 230, 255), b))
TWINKLE = rng.random((90, 4))
SKY_IMG = sky_img


def dune_layer(base, amp, freq, phase, color, rim=None):
    lay = Image.new("RGBA", (W * 2, H * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    pts = [(x * 2, (base + amp * math.sin(x / W * freq * math.pi + phase) + amp * 0.4 * math.sin(x / W * freq * 2.3 * math.pi + phase * 2)) * 2)
           for x in range(0, W + 1, 4)]
    d.polygon(pts + [(W * 2, H * 2), (0, H * 2)], fill=color)
    if rim:
        d.line(pts, fill=rim, width=4, joint="curve")
    return lay.resize((W, H), Image.LANCZOS), pts


FAR, _ = dune_layer(HZ - 6, 14, 1.4, 0.6, (30, 24, 58, 255))
NEAR, NEAR_PTS = dune_layer(HZ + 26, 18, 1.0, 2.2, (16, 13, 30, 255), rim=(236, 200, 132, 255))
# golden glow under the near rim
rim_mask = Image.new("L", (W, H), 0)
ImageDraw.Draw(rim_mask).line([(x / 2, y / 2) for x, y in NEAR_PTS], fill=255, width=6)
rim_glow = rim_mask.filter(ImageFilter.GaussianBlur(10))
RIM = Image.new("RGBA", (W, H), (236, 200, 132, 0))
RIM.putalpha(rim_glow.point(lambda v: min(255, int(v * 1.6))))
GROUND = Image.new("RGBA", (W, H), (0, 0, 0, 0))
GROUND.alpha_composite(RIM)
GROUND.alpha_composite(NEAR)
# darken the text area softly for legibility
shade = np.zeros((H, W, 4), np.uint8)
shade[..., 3] = (np.clip((yy - (HZ + 40)) / 500, 0, 1) * 120).astype(np.uint8)
GROUND.alpha_composite(Image.fromarray(shade))


# ------------------------------------------------------------------ text
TXT = {}


def gold_text(s, font, tracking=0, glow=0.55):
    key = (s, id(font), tracking, glow)
    if key in TXT: return TXT[key]
    widths = [font.getlength(ch) for ch in s]
    tw = int(sum(widths) + tracking * (len(s) - 1)) + 80
    asc, desc = font.getmetrics()
    th = asc + desc + 60
    mask = Image.new("L", (tw, th), 0)
    md = ImageDraw.Draw(mask)
    x = 40
    for ch, wch in zip(s, widths):
        md.text((x, 30), ch, font=font, fill=255)
        x += wch + tracking
    grad = np.linspace(0, 1, th)[:, None, None]
    col = GOLD_HI * (1 - grad) + GOLD_LO * grad
    img = np.concatenate([np.broadcast_to(col, (th, tw, 3)), np.asarray(mask, np.float32)[..., None]], -1)
    txt = Image.fromarray(img.astype(np.uint8), "RGBA")
    out = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    if glow:
        gl = Image.new("RGBA", (tw, th), GOLD + (0,))
        gl.putalpha(mask.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * glow)))
        out.alpha_composite(gl)
    out.alpha_composite(txt)
    TXT[key] = out
    return out


def plain_text(s, font, color, tracking=0, direction=None):
    key = (s, id(font), color, tracking, direction)
    if key in TXT: return TXT[key]
    lines = s.split("\n")
    lh = int(font.size * 1.3)
    tw = int(max(font.getlength(l) + tracking * len(l) for l in lines)) + 40
    im = Image.new("RGBA", (tw, lh * len(lines) + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        if direction:
            d.text((tw / 2, 15 + lh * i + lh / 2), l, font=font, fill=color, anchor="mm", direction=direction, language="ar")
        elif tracking:
            x = (tw - (font.getlength(l) + tracking * (len(l) - 1))) / 2
            for ch in l:
                d.text((x, 15 + lh * i), ch, font=font, fill=color); x += font.getlength(ch) + tracking
        else:
            d.text((tw / 2, 15 + lh * i), l, font=font, fill=color, anchor="ma")
    TXT[key] = im
    return im


def fit_serif(s, maxw, size=128):
    while size > 60:
        f = serif(size, 700)
        if f.getlength(s) + 4 * len(s) < maxw: return f
        size -= 6
    return serif(60, 700)


def put(frame, im, cx, cy, a, scale=1.0):
    if a <= 0: return
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if a < 1:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    frame.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


# ------------------------------------------------------------------ gold drawing helpers (supersampled canvas)
SS = 2
CW, CH = W, 860            # illustration canvas, logical px; bottom = HZ + 100
CY0 = HZ + 100 - CH        # canvas top in frame coordinates
GY = HZ - CY0              # horizon inside canvas
GRAD = None


def gold_grad():
    global GRAD
    if GRAD is None:
        t = np.linspace(0, 1, CH * SS)[:, None, None]
        c = GOLD_HI * (1 - t) + GOLD_LO * t
        side = (0.85 + 0.15 * np.cos(np.linspace(-1.2, 1.2, CW * SS)))[None, :, None]
        GRAD = Image.fromarray(np.clip(np.broadcast_to(c, (CH * SS, CW * SS, 3)) * side, 0, 255).astype(np.uint8)).convert("RGBA")
    return GRAD


class Canvas:
    def __init__(self):
        self.lay = Image.new("RGBA", (CW * SS, CH * SS), (0, 0, 0, 0))
        self.fig = Image.new("RGBA", (CW * SS, CH * SS), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.lay)
        self.fd = ImageDraw.Draw(self.fig)
        self.mask = Image.new("L", (CW * SS, CH * SS), 0)
        self.md = ImageDraw.Draw(self.mask)

    def P(self, x, y): return (x * SS, y * SS)

    def flush_gold(self, a=1.0):
        m = self.mask if a >= 1 else self.mask.point(lambda v: int(v * a))
        g = Image.new("RGBA", self.lay.size, (0, 0, 0, 0))
        g.paste(gold_grad(), (0, 0), m)
        glow = Image.new("RGBA", self.lay.size, GOLD + (0,))
        glow.putalpha(m.resize((CW // 2, CH // 2)).filter(ImageFilter.GaussianBlur(8)).resize(self.lay.size).point(lambda v: int(v * 0.5)))
        self.lay.alpha_composite(glow)
        self.lay.alpha_composite(g)
        self.mask = Image.new("L", self.lay.size, 0)
        self.md = ImageDraw.Draw(self.mask)

    def glow_dot(self, x, y, r, a, color=CREAM, draw=None):
        d = draw or self.d
        for k in range(6, 0, -1):
            rr = r * (1 + k * 0.6) * SS
            d.ellipse((x * SS - rr, y * SS - rr, x * SS + rr, y * SS + rr), fill=rgba(color, a * 0.05))
        d.ellipse(((x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS), fill=rgba(color, a))

    def figure(self, x, y, h, a, **kw):
        return C.figure(self.fd, x * SS, y * SS, h * SS, CREAM, a, **kw)

    def result(self, fig_glow=1.4):
        self.lay.alpha_composite(C.glow_layer(self.fig, fig_glow))
        return self.lay.resize((CW, CH), Image.LANCZOS)


def S_(v): return v * SS


# ------------------------------------------------------------------ illustrations (logical px; canvas centre x = 540)
def ill_sun(cv, lt, dur, a):
    cx, sy = 540, GY - 300 + (1 - ease(lt / 3)) * -60
    r = 120
    for k in range(10, 0, -1):
        rr = r * (1 + k * 0.22)
        cv.d.ellipse((S_(cx - rr), S_(sy - rr), S_(cx + rr), S_(sy + rr)), fill=rgba((255, 190, 120), a * 0.035))
    cv.md.ellipse((S_(cx - r), S_(sy - r), S_(cx + r), S_(sy + r)), fill=255)
    cv.flush_gold(a)
    for k in range(3):
        f = (lt * 0.45 + k / 3) % 1
        rr = r * (1.15 + 1.1 * f)
        cv.d.ellipse((S_(cx - rr), S_(sy - rr), S_(cx + rr), S_(sy + rr)), outline=rgba(GOLD, a * (1 - f) * 0.5), width=S_(2))
    for i in range(11):
        x = 540 + (i - 5) * 92
        arms = C.ARMS_SHADE if i % 3 == 0 else C.ARMS_DOWN
        C.figure(cv.d, S_(x), S_(GY + 6), S_(170 + 14 * ((i * 5) % 3)), (12, 10, 24), a, facing=1 if i % 2 else -1,
                 lean=0.05 * math.sin(lt * 1.2 + i), head_down=0 if i % 3 == 0 else 0.35, front=arms[0], back=arms[1])


def ill_canopy(cv, lt, dur, a, full=False):
    cx, top = 540, GY - 520
    aw, ah = 360 * ease(lt / 0.9), 300
    for k in range(5, 0, -1):
        pts = [(S_(cx + aw * (1 + k * 0.05) * math.cos(t)), S_(top + ah + ah * (1 + k * 0.06) * math.sin(t))) for t in np.linspace(math.pi, 2 * math.pi, 60)]
        cv.d.polygon(pts + [(S_(cx + aw), S_(GY)), (S_(cx - aw), S_(GY))], fill=rgba((255, 225, 160), a * 0.03))
    arc = [(S_(cx + aw * math.cos(t)), S_(top + ah + ah * math.sin(t))) for t in np.linspace(math.pi, 2 * math.pi, 90)]
    cv.md.line(arc, fill=255, width=S_(7), joint="curve")
    cv.md.ellipse((S_(cx - 16), S_(top - 16), S_(cx + 16), S_(top + 16)), fill=255)
    cv.flush_gold(a)
    if full:
        for i in range(30):
            t = math.pi + math.pi * (i + 0.5) / 30
            l0, l1 = 1.06, 1.22 + 0.08 * math.sin(lt * 2 + i)
            cv.d.line((S_(cx + aw * l0 * math.cos(t)), S_(top + ah + ah * l0 * math.sin(t)),
                       S_(cx + aw * l1 * math.cos(t)), S_(top + ah + ah * l1 * math.sin(t))), fill=rgba(GOLD, a * 0.6), width=S_(2))
    shown = 7 if full else clamp((lt - 0.6) / 2.4) * 7
    for i in range(7):
        q = 1 if full else clamp(shown - i)
        if q <= 0: continue
        arms = C.ARMS_DUA if full else C.ARMS_DOWN
        cv.figure(540 + (i - 3) * 86, GY - (1 - ease(q)) * 30, 175 + 12 * (i % 2), a * ease(q), facing=1 if i < 3 else -1,
                  head_down=0.1, front=arms[0], back=arms[1])
    if not full:
        for i in range(8):
            side = -1 if i % 2 else 1
            C.figure(cv.d, S_(540 + side * (420 + 25 * (i // 2))), S_(GY + 8), S_(130), (14, 12, 26), a, facing=-side, head_down=0.4)


def ill_scales(cv, lt, dur, a):
    cx, top = 540, GY - 560
    ang = 0.3 * math.exp(-lt * 0.8) * math.cos(lt * 3)
    L = 230
    cv.md.rectangle((S_(cx - 7), S_(top), S_(cx + 7), S_(GY - 40)), fill=255)
    cv.md.polygon([(S_(cx - 110), S_(GY - 10)), (S_(cx + 110), S_(GY - 10)), (S_(cx + 60), S_(GY - 50)), (S_(cx - 60), S_(GY - 50))], fill=255)
    cv.md.ellipse((S_(cx - 20), S_(top - 30), S_(cx + 20), S_(top + 10)), fill=255)
    ends = []
    for s in (-1, 1):
        ex, ey = cx + s * L * math.cos(ang), top + s * L * math.sin(ang)
        cv.md.line((S_(cx), S_(top), S_(ex), S_(ey)), fill=255, width=S_(10))
        py = ey + 190
        cv.md.line((S_(ex), S_(ey), S_(ex - 75), S_(py)), fill=255, width=S_(3))
        cv.md.line((S_(ex), S_(ey), S_(ex + 75), S_(py)), fill=255, width=S_(3))
        cv.md.chord((S_(ex - 100), S_(py - 40), S_(ex + 100), S_(py + 40)), 0, 180, fill=255)
        ends.append((ex, py))
    cv.flush_gold(a)
    for k, (ex, py) in enumerate(ends):
        f = (lt * 0.5 + k * 0.5) % 1
        cv.glow_dot(ex, py - 10 - 30 * math.sin(f * math.pi), 10, a * math.sin(f * math.pi))


def ill_youth(cv, lt, dur, a):
    g = ease(lt / max(dur * 0.7, 1))
    h = 250 + 110 * g
    x = 480
    cv.d.rounded_rectangle((S_(330), S_(GY - 8), S_(760), S_(GY + 6)), S_(6), fill=rgba((120, 40, 50), a), outline=rgba(GOLD, a * 0.7), width=S_(2))
    info = cv.figure(x, GY - 8, h, a, facing=1, mode="sit", lean=0.12, head_down=0.35, front=C.ARMS_READ[0], back=C.ARMS_READ[1])
    bx, by = C.hand_pos(x * SS, (GY - 8) * SS, h * SS, 1, 0.12, C.ARMS_READ[0], mode="sit")
    bx, by = bx / SS, by / SS
    bw = 0.15 * h
    for s in (-1, 1):
        cv.md.polygon([(S_(bx), S_(by - 0.03 * h)), (S_(bx + s * bw), S_(by - 0.07 * h)), (S_(bx + s * bw), S_(by + 0.05 * h)), (S_(bx), S_(by + 0.08 * h))], fill=255)
    cv.flush_gold(a)
    # beam of light from the book
    for k in range(8, 0, -1):
        wdt = 6 + k * 9
        cv.d.polygon([(S_(bx - wdt / 2), S_(by)), (S_(bx + wdt / 2), S_(by)), (S_(bx + wdt), S_(0)), (S_(bx - wdt), S_(0))], fill=rgba((255, 230, 170), a * 0.025))
    for k in range(10):
        f = (lt * 0.3 + k / 10) % 1
        cv.glow_dot(bx + 50 * math.sin(k * 2.3 + lt) * f, by - 30 - 520 * f, 4 - 2 * f, a * (1 - f))


def ill_mosque(cv, lt, dur, a):
    mx, base = 360, GY
    cv.md.rectangle((S_(mx - 170), S_(base - 210), S_(mx + 170), S_(base)), fill=255)
    cv.md.ellipse((S_(mx - 130), S_(base - 410), S_(mx + 130), S_(base - 150)), fill=255)
    cv.md.rectangle((S_(mx - 4), S_(base - 470), S_(mx + 4), S_(base - 405)), fill=255)
    for s in (-1, 1):
        x = mx + s * 225
        cv.md.rectangle((S_(x - 18), S_(base - 440), S_(x + 18), S_(base)), fill=255)
        cv.md.polygon([(S_(x - 26), S_(base - 440)), (S_(x + 26), S_(base - 440)), (S_(x), S_(base - 520))], fill=255)
        cv.md.rectangle((S_(x - 26), S_(base - 330), S_(x + 26), S_(base - 318)), fill=255)
    cv.flush_gold(a)
    # crescent on the dome and lit arched windows / door
    cv.d.ellipse((S_(mx - 16), S_(base - 500), S_(mx + 16), S_(base - 468)), fill=rgba(GOLD, a))
    cv.d.ellipse((S_(mx - 9), S_(base - 504), S_(mx + 19), S_(base - 472)), fill=(0, 0, 0, 0))
    for wx in (-95, 95):
        cv.d.rounded_rectangle((S_(mx + wx - 22), S_(base - 170), S_(mx + wx + 22), S_(base - 80)), S_(22), fill=rgba((60, 40, 30), a))
        cv.d.rounded_rectangle((S_(mx + wx - 16), S_(base - 164), S_(mx + wx + 16), S_(base - 86)), S_(16), fill=rgba((255, 214, 140), a * (0.7 + 0.3 * math.sin(lt * 2 + wx))))
    cv.d.rounded_rectangle((S_(mx - 38), S_(base - 150), S_(mx + 38), S_(base)), S_(38), fill=rgba((60, 40, 30), a))
    x = lerp(690, 860, clamp(lt / max(dur, 0.1)))
    info = cv.figure(x, GY, 300, a, facing=1, mode="walk", phase=lt * 3.2, head_down=0.05)
    hx, hy = info["chest"][0] / SS, info["chest"][1] / SS
    tx, ty = mx, base - 300
    pts = [(S_(lerp(hx, tx, s)), S_(lerp(hy, ty, s) - math.sin(s * math.pi) * 200)) for s in np.linspace(0, 1, 50)]
    cv.d.line(pts, fill=rgba(CREAM, a * 0.6), width=S_(2), joint="curve")
    for k in range(3):
        s = (lt * 0.3 + k / 3) % 1
        p = pts[int(s * 49)]
        cv.glow_dot(p[0] / SS, p[1] / SS, 6, a)
    cv.glow_dot(hx, hy, 11 * (1 + 0.2 * abs(math.sin(lt * 3.4))), a, draw=cv.fd)


def ill_two(cv, lt, dur, a):
    ph = clamp(lt / max(dur, 0.1))
    h = 330
    if ph < 0.35:
        off, inward, walk, arm = lerp(380, 92, ease(ph / 0.35)), True, True, C.ARMS_DOWN
    elif ph < 0.62:
        r = ease((ph - 0.35) / 0.08)
        off, inward, walk, arm = 92, True, False, ((lerp(0.12, 1.2, r), lerp(0.08, 0.15, r)), (-0.1, 0.06))
    else:
        off, inward, walk, arm = lerp(92, 330, ease((ph - 0.62) / 0.38)), False, True, C.ARMS_DOWN
    chests = []
    for s in (-1, 1):
        info = cv.figure(540 + s * off, GY, h, a, facing=-s if inward else s, mode="walk" if walk else "stand",
                         phase=lt * 3.4 + (0 if s < 0 else math.pi), front=arm[0], back=arm[1])
        chests.append((info["chest"][0] / SS, info["chest"][1] / SS))
    if ph >= 0.35:
        q = ease((ph - 0.35) / 0.1)
        cv.d.line((S_(chests[0][0]), S_(chests[0][1]), S_(chests[1][0]), S_(chests[1][1])), fill=rgba(GOLD, a * 0.7 * q), width=S_(3))
        for c_ in chests:
            cv.glow_dot(c_[0], c_[1], 9 * q, a, draw=cv.fd)
    cv.glow_dot(540, GY - 520, 18, a, color=GOLD)
    for c_ in chests:
        cv.d.line((S_(540), S_(GY - 505), S_(c_[0]), S_(c_[1])), fill=rgba(GOLD, a * 0.2), width=S_(2))


def ill_refuse(cv, lt, dur, a):
    ph = clamp(lt / max(dur, 0.1))
    dx = 250
    door = (dx - 95, GY - 380, dx + 95, GY)
    for k in range(5, 0, -1):
        g_ = k * 14
        cv.d.rounded_rectangle((S_(door[0] - g_), S_(door[1] - g_), S_(door[2] + g_), S_(door[3])), S_(95 + g_), fill=rgba((150, 80, 120), a * 0.04))
    cv.d.rounded_rectangle(tuple(S_(v) for v in door), S_(95), fill=rgba((40, 20, 40), a * 0.8), outline=rgba((150, 90, 130), a * 0.8), width=S_(3))
    calling = 1 - ease((ph - 0.45) / 0.1)
    for k in range(3):
        f = (lt * 0.5 + k / 3) % 1
        rr = 60 + 260 * f
        cv.d.arc((S_(dx - rr), S_(GY - 190 - rr), S_(dx + rr), S_(GY - 190 + rr)), -50, 50, fill=rgba((170, 100, 150), a * (1 - f) * 0.7 * calling), width=S_(3))
    bright = ease((ph - 0.68) / 0.3)
    cv.glow_dot(960, GY - 200, 22 + 22 * bright, a, color=GOLD)
    if ph < 0.45:
        cv.figure(600, GY, 340, a, facing=-1)
    elif ph < 0.68:
        r = ease((ph - 0.45) / 0.08)
        cv.figure(600, GY, 340, a, facing=-1, front=(lerp(0.12, C.ARM_STOP[0][0], r), lerp(0.08, C.ARM_STOP[0][1], r)), back=C.ARM_STOP[1])
    else:
        cv.figure(lerp(600, 820, ease((ph - 0.68) / 0.32)), GY, 340, a, facing=1, mode="walk", phase=lt * 3.2)


def ill_charity(cv, lt, dur, a):
    gx, rx = 400, 720
    cv.figure(gx, GY, 340, a, facing=1, lean=0.25, head_down=0.15, front=C.ARM_GIVE[0], back=C.ARM_GIVE[1])
    recv = ((1.1, 0.35), (-0.1, 0.06))
    cv.figure(rx, GY, 260, a * 0.9, facing=-1, mode="sit", lean=0.05, front=recv[0], back=recv[1])
    h0 = C.hand_pos(gx * SS, GY * SS, 340 * SS, 1, 0.25, C.ARM_GIVE[0])
    h1 = C.hand_pos(rx * SS, GY * SS, 260 * SS, -1, 0.05, recv[0], mode="sit")
    f = (lt * 0.45) % 1
    x = lerp(h0[0], h1[0], ease(f)) / SS
    y = (lerp(h0[1], h1[1], ease(f)) / SS) - math.sin(f * math.pi) * 40
    cv.md.ellipse((S_(x - 14), S_(y - 14), S_(x + 14), S_(y + 14)), fill=255)
    cv.flush_gold(a)
    cv.glow_dot(x, y, 4, a)
    # the hidden left hand: a soft veil behind the giver
    for k in range(6):
        cv.d.rectangle((S_(gx - 230 + k * 10), S_(GY - 420), S_(gx - 120), S_(GY)), fill=(10, 8, 22, int(18 * a)))


def ill_night(cv, lt, dur, a):
    mx, my, r = 880, 230, 62
    cv.md.ellipse((S_(mx - r), S_(my - r), S_(mx + r), S_(my + r)), fill=255)
    cv.md.ellipse((S_(mx - r + 32), S_(my - r - 10), S_(mx + r + 32), S_(my + r - 10)), fill=0)
    cv.flush_gold(a)
    cv.d.rounded_rectangle((S_(330), S_(GY - 8), S_(740), S_(GY + 6)), S_(6), fill=rgba((120, 40, 50), a), outline=rgba(GOLD, a * 0.7), width=S_(2))
    info = cv.figure(500, GY - 8, 330, a, facing=1, mode="sit", lean=0.06, head_down=0.3, front=C.ARMS_DUA[0], back=C.ARMS_DUA[1])
    hx, hy = info["head"][0] / SS, info["head"][1] / SS
    for k in range(3):
        f = ((lt - 1.0) * 0.5 + k / 3) % 1 if lt > 1.0 else -1
        if f < 0: continue
        ty = hy + 28 + 240 * f ** 1.5
        s = 9
        tx = hx + 32
        cv.fd.polygon([(S_(tx), S_(ty - s * 1.9)), (S_(tx + s), S_(ty)), (S_(tx - s), S_(ty))], fill=rgba((200, 225, 255), a * (1 - f)))
        cv.fd.ellipse((S_(tx - s), S_(ty - s), S_(tx + s), S_(ty + s)), fill=rgba((200, 225, 255), a * (1 - f)))


def ill_book(cv, lt, dur, a):
    cx, by = 540, GY - 30
    op = ease(lt / 0.8)
    for k in range(10, 0, -1):
        wdt = 10 + k * 14
        cv.d.polygon([(S_(cx - wdt / 2), S_(by - 60)), (S_(cx + wdt / 2), S_(by - 60)), (S_(cx + wdt * 0.6), S_(0)), (S_(cx - wdt * 0.6), S_(0))],
                     fill=rgba((255, 232, 170), a * 0.03 * op))
    cv.d.line((S_(cx), S_(by - 60), S_(cx), S_(0)), fill=rgba((255, 240, 200), a * 0.8 * op), width=S_(2))
    for i in range(14):
        ang = -math.pi / 2 + (i - 6.5) * 0.11
        L = 320 + 60 * math.sin(lt * 1.5 + i)
        cv.d.line((S_(cx), S_(by - 60), S_(cx + L * math.cos(ang)), S_(by - 60 + L * math.sin(ang))), fill=rgba((255, 230, 170), a * 0.25 * op), width=S_(2))
    for s in (-1, 1):
        cv.md.polygon([(S_(cx), S_(by - 70)), (S_(cx + s * 170 * op), S_(by - 90)), (S_(cx + s * 175 * op), S_(by + 20)), (S_(cx), S_(by + 30))], fill=255)
    cv.flush_gold(a)
    for s in (-1, 1):
        for k in range(7):
            yl = by - 70 + k * 13
            cv.d.line((S_(cx + s * 20), S_(yl), S_(cx + s * 150 * op), S_(yl - 14)), fill=rgba((150, 100, 40), a * 0.6), width=S_(2))


ILL = {"sun": ill_sun, "canopy": ill_canopy, "canopy_full": lambda cv, lt, dur, a: ill_canopy(cv, lt, dur, a, full=True),
       "scales": ill_scales, "sprout": ill_youth, "mosque": ill_mosque, "two": ill_two, "turn": ill_refuse,
       "hands": ill_charity, "eye": ill_night, "book": ill_book}


# ------------------------------------------------------------------ frame
def shooting_stars(d, t):
    for k in range(int(t / 2.3) - 1, int(t / 2.3) + 1):
        if k < 0: continue
        r = np.random.default_rng(1000 + k)
        t0 = k * 2.3 + r.uniform(0, 1.2)
        f = (t - t0) / 0.9
        if not 0 <= f <= 1: continue
        x0, y0 = r.uniform(300, W + 100), r.uniform(-50, 500)
        ang = math.radians(r.uniform(112, 125))
        L = 900
        hx, hy = x0 + math.cos(ang) * L * f, y0 + math.sin(ang) * L * f
        fade = math.sin(f * math.pi)
        for i in range(14):
            s = i / 14
            ax, ay = hx - math.cos(ang) * 190 * s, hy - math.sin(ang) * 190 * s
            bx, by_ = hx - math.cos(ang) * 190 * (s + 1 / 14), hy - math.sin(ang) * 190 * (s + 1 / 14)
            d.line((ax, ay, bx, by_), fill=rgba((255, 245, 225), fade * (1 - s) * 0.9), width=max(1, int(3 * (1 - s))))


def render(fi):
    t = fi / FPS
    si = max(i for i, s in enumerate(SCENES) if s[0] <= t) if t >= SCENES[0][0] else 0
    s0, s1, seg = SCENES[si]
    sid, kind = seg[0], seg[2]
    lt, dur = t - s0, s1 - s0
    last = si == len(SCENES) - 1
    out_k = eio((lt - (dur - 0.35)) / 0.35) if not last else eio((t - (DUR - 0.8)) / 0.8)
    in_k = ease(lt / 0.55)
    a = in_k * (1 - out_k)

    frame = SKY_IMG.copy()
    d = ImageDraw.Draw(frame)
    for x, y, sp, ph in TWINKLE:
        b = 0.5 + 0.5 * math.sin(t * (1.5 + 2 * sp) + ph * 20)
        X, Y = x * W, y * (HZ - 40)
        rr = 1.6 + 1.2 * sp
        d.ellipse((X - rr, Y - rr, X + rr, Y + rr), fill=rgba((255, 250, 235), 0.3 + 0.7 * b))
        if sp > 0.85:
            d.line((X - 8 * b, Y, X + 8 * b, Y), fill=rgba((255, 250, 235), 0.5 * b), width=1)
            d.line((X, Y - 8 * b, X, Y + 8 * b), fill=rgba((255, 250, 235), 0.5 * b), width=1)
    shooting_stars(d, t)
    frame.alpha_composite(FAR)

    # illustration slides in from the right and out to the left
    cv = Canvas()
    ILL[kind](cv, lt, dur, 1.0)
    ill = cv.result()
    slide = (1 - in_k) * 520 - out_k * 520
    put(frame, ill, W / 2 + slide, CY0 + CH / 2, min(1, a * 1.3))
    frame.alpha_composite(GROUND)

    num, kick, name, sub, desc, src, ar = {**{k: v for k, v in CONTENT.items()}}[sid]
    ta = ease((lt - 0.15) / 0.5) * (1 - out_k)
    rise = (1 - ease((lt - 0.15) / 0.6)) * 30
    y = TXT_Y
    if kick:
        put(frame, plain_text(kick.lower() if num else kick, F_KICK, GOLD + (255,), tracking=2 if not num else 0), W / 2, y - 92 + rise, ta)
    fname = fit_serif(name, W - 120)
    nm = gold_text(name, fname, tracking=4)
    put(frame, nm, W / 2, y + rise, ta)
    # flourish under the name
    fw = min(nm.width - 120, 520) * ease((lt - 0.3) / 0.7)
    if fw > 4:
        yy_ = y + fname.size * 0.52 + rise
        d = ImageDraw.Draw(frame)
        d.line((W / 2 - fw / 2, yy_, W / 2 + fw / 2, yy_), fill=rgba(GOLD, 0.8 * ta), width=2)
        d.polygon([(W / 2, yy_ - 7), (W / 2 + 7, yy_), (W / 2, yy_ + 7), (W / 2 - 7, yy_)], fill=rgba(GOLD, ta))
    yb = y + fname.size * 0.52 + 30
    if sub:
        sm = gold_text(sub, serif(54, 600), tracking=10, glow=0.4)
        put(frame, sm, W / 2, yb + 40 + rise, ta)
        yb += 80
    if desc:
        da = ease((lt - 0.45) / 0.5) * (1 - out_k)
        dm = plain_text(desc, F_DESC, (250, 246, 240, 255))
        put(frame, dm, W / 2, yb + 18 + dm.height / 2 + rise * 0.6, da)
        yb += dm.height + 10
    if src:
        sa = ease((lt - 0.8) / 0.5) * (1 - out_k)
        put(frame, plain_text(src, F_SRC, (214, 178, 112, 255)), W / 2, yb + 30, sa)
    if ar:
        aa = ease((lt - 0.6) / 0.8) * (1 - out_k)
        am = plain_text(ar, F_AR, (240, 212, 150, 255), direction="rtl")
        put(frame, am, W / 2, 340 - 10 * ease(lt / max(dur, 1)), aa * 0.95)
    # counter
    if num:
        ca = ease(lt / 0.4) * (1 - out_k)
        c1 = gold_text(f"0{num}", F_CNT, tracking=2, glow=0.35)
        c2 = plain_text("/ 07", F_CNT_S, (214, 178, 112, 255))
        put(frame, c1, W / 2 - 30, 190, ca)
        put(frame, c2, W / 2 + 48, 202, ca)
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
