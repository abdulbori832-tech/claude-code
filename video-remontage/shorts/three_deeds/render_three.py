"""Short: "3 deeds whose reward continues after death" (Muslim 1631), cinema style.

Reuses ../seven_shade/render_cinema.py (sky, dunes, gold text, characters) and
swaps in this short's scenes, text and illustrations.

usage: python3 render_three.py OUT_DIR [stills t1,t2,...]
"""
import json, math, os, sys
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "seven_shade"))
import numpy as np
from PIL import Image
import render_cinema as RC
import characters as C
from render_cinema import S_, GY, SS, rgba, ease, clamp, lerp, GOLD, CREAM

AR_FULL = "إِذَا مَاتَ الإِنْسَانُ انْقَطَعَ عَنْهُ عَمَلُهُ"
SRC = "Муслим 1631"

# id, illustration, voice text (for timing estimate only)
SEGMENTS = [
    ("hook", "after", "Когда ты умрёшь, все твои дела прекратятся. Кроме трёх."),
    ("q", "three", "Пророк, мир ему, сказал: «Когда человек умирает, его дела прекращаются, кроме трёх». Знаешь, каких?"),
    ("1", "well", "Первое — непрерывная милостыня. Например, колодец, мечеть или посаженное дерево: пока ими пользуются люди, тебе пишется награда."),
    ("2", "teach", "Второе — знание, которое приносит пользу. Ты научил кого-то благому, и пока этим знанием пользуются, награда доходит и до тебя."),
    ("3", "child", "Третье — праведный ребёнок, который делает за тебя дуа."),
    ("src", "book", "Этот хадис передал Абу Хурайра, его приводит имам Муслим."),
    ("cta", "merge", "Сделай сегодня хотя бы одно из трёх. И отправь это своим родителям."),
]

CONTENT = {
    "hook": (0, "", "ПОСЛЕ СМЕРТИ", "", "все дела прекратятся,\nкроме трёх", "", AR_FULL),
    "q": (0, "", "3 ДЕЛА", "НАГРАДА ПОСЛЕ СМЕРТИ", "Знаешь, каких?", SRC, "إِلاَّ مِنْ ثَلاَثَةٍ"),
    "1": (1, "ПЕРВОЕ", "МИЛОСТЫНЯ", "", "непрерывная милостыня:\nколодец, мечеть, дерево", SRC, "صَدَقَةٍ جَارِيَةٍ"),
    "2": (2, "ВТОРОЕ", "ЗНАНИЕ", "", "знание, которое\nприносит пользу", SRC, "عِلْمٍ يُنْتَفَعُ بِهِ"),
    "3": (3, "ТРЕТЬЕ", "ДУА РЕБЁНКА", "", "праведный ребёнок,\nкоторый делает за тебя дуа", SRC, "وَلَدٍ صَالِحٍ يَدْعُو لَهُ"),
    "src": (0, "ПЕРЕДАЛ АБУ ХУРАЙРА", "ДОСТОВЕРНЫЙ", "ХАДИС", "Сахих Муслим № 1631", "", ""),
    "cta": (0, "", "НАЧНИ СЕГОДНЯ", "", "Отправь это своим родителям", "", ""),
}


def lamp(cv, x, y, s, a, flick=0.0):
    """Golden oil lamp with a flame; (x, y) = base centre."""
    cv.md.ellipse((S_(x - 46 * s), S_(y - 34 * s), S_(x + 46 * s), S_(y + 4 * s)), fill=255)
    cv.md.polygon([(S_(x + 30 * s), S_(y - 26 * s)), (S_(x + 78 * s), S_(y - 40 * s)), (S_(x + 70 * s), S_(y - 26 * s)), (S_(x + 34 * s), S_(y - 8 * s))], fill=255)
    cv.md.rectangle((S_(x - 8 * s), S_(y - 44 * s), S_(x + 8 * s), S_(y - 30 * s)), fill=255)
    fx, fy = x + 74 * s, y - 44 * s
    h = (34 + 6 * math.sin(flick * 9)) * s
    for k in range(6, 0, -1):
        rr = 14 * s * (1 + k * 0.7)
        cv.d.ellipse((S_(fx - rr), S_(fy - h / 2 - rr), S_(fx + rr), S_(fy - h / 2 + rr)), fill=rgba((255, 200, 120), a * 0.05))
    cv.d.polygon([(S_(fx - 9 * s), S_(fy)), (S_(fx + 9 * s), S_(fy)), (S_(fx + 2 * s * math.sin(flick * 7)), S_(fy - h))], fill=rgba((255, 236, 180), a))
    cv.d.ellipse((S_(fx - 9 * s), S_(fy - 8 * s), S_(fx + 9 * s), S_(fy + 6 * s)), fill=rgba((255, 236, 180), a))


def ill_after(cv, lt, dur, a):
    ph = clamp(lt / max(dur, 0.1))
    rs = np.random.default_rng(5)
    pts = [(rs.uniform(80, 1000), rs.uniform(120, GY - 160)) for _ in range(24)]
    keep = {3, 11, 19}
    for i, (x, y) in enumerate(pts):
        fade = 1.0 if i in keep else 1 - clamp((ph * 1.4) - i / 30)
        if i in keep and ph > 0.55:
            cv.glow_dot(x, y, 10 + 4 * math.sin(lt * 3 + i), a, color=GOLD)
        elif fade > 0:
            cv.glow_dot(x, y, 6, a * fade * 0.8)
    x = lerp(380, 640, ph)
    h = lerp(320, 250, ph)
    cv.figure(x, GY, h, a * (1 - 0.35 * ph), facing=1, mode="walk", phase=lt * 3.0, head_down=0.15)


def ill_three(cv, lt, dur, a):
    for i, x in enumerate((250, 540, 830)):
        q = ease((lt - 0.4 - i * 0.5) / 0.6)
        if q <= 0:
            continue
        lamp(cv, x - 60, GY - 6, 2.1, a * q, flick=lt + i)
    cv.flush_gold(a)


def ill_well(cv, lt, dur, a):
    wx, base = 430, GY
    # well: stone ring, two posts, roof, rope and bucket
    cv.md.rounded_rectangle((S_(wx - 130), S_(base - 120), S_(wx + 130), S_(base)), S_(14), fill=255)
    for s in (-1, 1):
        cv.md.rectangle((S_(wx + s * 115 - 8), S_(base - 330), S_(wx + s * 115 + 8), S_(base - 110)), fill=255)
    cv.md.polygon([(S_(wx - 165), S_(base - 320)), (S_(wx + 165), S_(base - 320)), (S_(wx), S_(base - 420))], fill=255)
    cv.md.rectangle((S_(wx - 120), S_(base - 300), S_(wx + 120), S_(base - 290)), fill=255)
    by = base - 290 + 60 + 40 * math.sin(lt * 1.4)
    cv.md.line((S_(wx), S_(base - 290), S_(wx), S_(by)), fill=255, width=S_(3))
    cv.md.polygon([(S_(wx - 26), S_(by)), (S_(wx + 26), S_(by)), (S_(wx + 20), S_(by + 40)), (S_(wx - 20), S_(by + 40))], fill=255)
    # tree growing at the right
    g = ease(lt / max(dur * 0.6, 1))
    tx = 820
    cv.md.polygon([(S_(tx - 14), S_(base)), (S_(tx + 14), S_(base)), (S_(tx + 6), S_(base - 260 * g)), (S_(tx - 6), S_(base - 260 * g))], fill=255)
    for k, (dx, dy, r) in enumerate(((0, -300, 95), (-80, -240, 70), (80, -235, 72), (-40, -340, 60), (50, -345, 58))):
        q = clamp((g - 0.4 - k * 0.08) / 0.3)
        if q > 0:
            rr = r * ease(q)
            cv.md.ellipse((S_(tx + dx - rr), S_(base + dy - rr), S_(tx + dx + rr), S_(base + dy + rr)), fill=255)
    cv.flush_gold(a)
    # water inside the well and drops
    cv.d.ellipse((S_(wx - 110), S_(base - 128), S_(wx + 110), S_(base - 108)), fill=rgba((90, 150, 220), a * 0.9))
    for k in range(3):
        f = (lt * 0.8 + k / 3) % 1
        cv.d.ellipse((S_(wx - 4 + 10 * k - 10), S_(by + 44 + 60 * f), S_(wx + 4 + 10 * k - 10), S_(by + 54 + 60 * f)), fill=rgba((160, 200, 255), a * (1 - f)))
    # a person drinking from the well, and a bird at the tree
    cv.figure(220, GY, 280, a, facing=1, lean=0.2, front=(1.0, 0.9), back=(0.9, 1.0), head_down=0.2)
    bx, by2 = tx + 60 * math.cos(lt * 0.9), base - 420 + 15 * math.sin(lt * 1.8)
    cv.d.line([(S_(bx - 22), S_(by2 - 8 * math.sin(lt * 9))), (S_(bx), S_(by2)), (S_(bx + 22), S_(by2 - 8 * math.sin(lt * 9)))], fill=rgba(CREAM, a), width=S_(4), joint="curve")


def ill_teach(cv, lt, dur, a):
    h_t, h_s = 300, 240
    tx, sx, s2x = 280, 560, 820
    cv.d.rounded_rectangle((S_(150), S_(GY - 8), S_(900), S_(GY + 6)), S_(6), fill=rgba((120, 40, 50), a), outline=rgba(GOLD, a * 0.7), width=S_(2))
    cv.figure(tx, GY - 8, h_t, a, facing=1, mode="sit", lean=0.08, head_down=0.2, front=C.ARMS_READ[0], back=C.ARMS_READ[1])
    bx, by = C.hand_pos(tx * SS, (GY - 8) * SS, h_t * SS, 1, 0.08, C.ARMS_READ[0], mode="sit")
    bx, by = bx / SS, by / SS
    for s in (-1, 1):
        cv.md.polygon([(S_(bx), S_(by - 10)), (S_(bx + s * 46), S_(by - 22)), (S_(bx + s * 46), S_(by + 14)), (S_(bx), S_(by + 24))], fill=255)
    cv.flush_gold(a)
    cv.figure(sx, GY - 8, h_s, a * 0.95, facing=-1, mode="sit", head_down=0.1)
    s2 = ease((lt - 2.0) / 0.8)
    if s2 > 0:
        cv.figure(s2x, GY - 8, 200, a * s2, facing=-1, mode="sit", head_down=0.1)
    # light passes: book -> student -> next student
    hs = (sx, GY - 8 - h_s * 0.62)
    hs2 = (s2x, GY - 8 - 200 * 0.62)
    for k in range(2):
        f = (lt * 0.5 + k * 0.5) % 1
        x = lerp(bx, hs[0], ease(f)); y = lerp(by, hs[1], ease(f)) - math.sin(f * math.pi) * 90
        cv.glow_dot(x, y, 9, a * math.sin(f * math.pi), color=GOLD)
        if s2 > 0.5:
            f2 = (f + 0.5) % 1
            x = lerp(hs[0], hs2[0], ease(f2)); y = lerp(hs[1], hs2[1], ease(f2)) - math.sin(f2 * math.pi) * 70
            cv.glow_dot(x, y, 7, a * math.sin(f2 * math.pi) * s2, color=GOLD)
    for p, r in ((hs, 1.0), (hs2, s2)):
        if r > 0:
            cv.glow_dot(p[0], p[1], 8 * (1 + 0.2 * math.sin(lt * 3)), a * r, draw=cv.fd)


def ill_child(cv, lt, dur, a):
    mx, my, r = 840, 170, 62
    cv.md.ellipse((S_(mx - r), S_(my - r), S_(mx + r), S_(my + r)), fill=255)
    cv.md.ellipse((S_(mx - r + 30), S_(my - r - 10), S_(mx + r + 30), S_(my + r - 10)), fill=0)
    cv.flush_gold(a)
    cv.d.rounded_rectangle((S_(370), S_(GY - 8), S_(700), S_(GY + 6)), S_(6), fill=rgba((120, 40, 50), a), outline=rgba(GOLD, a * 0.7), width=S_(2))
    info = cv.figure(520, GY - 8, 255, a, facing=1, mode="sit", lean=0.02, head_down=0.15, front=C.ARMS_DUA[0], back=C.ARMS_DUA[1])
    hx, hy = info["head"][0] / SS, info["head"][1] / SS
    # dua rises as light towards the sky
    for k in range(6):
        f = (lt * 0.35 + k / 6) % 1
        cv.glow_dot(hx + 60 + 30 * math.sin(k * 2 + lt), hy - 40 - 520 * f, 6 - 3 * f, a * (1 - f), color=GOLD)
    cv.glow_dot(hx + 60, 120, 12 + 3 * math.sin(lt * 2), a * ease((lt - 1) / 1.5), color=GOLD)


def ill_merge(cv, lt, dur, a):
    k = ease((lt - 0.5) / 2.0)
    cx, cy = 540, GY - 460
    pos = [(lerp(x, cx, k), lerp(GY - 140, cy, k)) for x in (300, 540, 780)]
    for i, (x, y) in enumerate(pos):
        cv.glow_dot(x, y, 14 + 4 * math.sin(lt * 3 + i), a * (1 - 0.6 * k), color=GOLD)
    if k > 0.6:
        q = (k - 0.6) / 0.4
        for j in range(24):
            ang = 2 * math.pi * j / 24 + lt * 0.2
            l0, l1 = 50, 50 + (70 + 40 * math.sin(lt * 2 + j)) * q
            cv.d.line((S_(cx + l0 * math.cos(ang)), S_(cy + l0 * math.sin(ang)), S_(cx + l1 * math.cos(ang)), S_(cy + l1 * math.sin(ang))), fill=rgba(GOLD, a * 0.5 * q), width=S_(2))
        cv.glow_dot(cx, cy, 30 * q, a, color=(255, 236, 190))
    cv.figure(540, GY, 300, a, facing=1, front=C.ARMS_DUA[0], back=C.ARMS_DUA[1], head_down=-0.1)


ILL = {"after": ill_after, "three": ill_three, "well": ill_well, "teach": ill_teach, "child": ill_child,
       "book": RC.ill_book, "merge": ill_merge}

# ---- timeline
TP = os.path.join(HERE, "timings.json")
if os.path.exists(TP):
    TIMES = json.load(open(TP))["segments"]
else:
    t, TIMES = 0.4, []
    for seg in SEGMENTS:
        d = len(seg[2]) / 13 + 0.3
        TIMES.append([t, t + d]); t += d + 0.6
DUR = TIMES[-1][1] + 2.6
SCENES = []
for i, seg in enumerate(SEGMENTS):
    a0 = 0.0 if i == 0 else TIMES[i][0] - 0.25
    b0 = TIMES[i + 1][0] - 0.25 if i + 1 < len(TIMES) else DUR + 1
    SCENES.append((a0, b0, (seg[0], "", seg[1], seg[2], [], 0)))

RC.CONTENT, RC.ILL, RC.SCENES, RC.DUR, RC.NF, RC.TOTAL = CONTENT, ILL, SCENES, DUR, int(DUR * RC.FPS), 3

if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    if len(sys.argv) > 2 and sys.argv[2] == "stills":
        for tt in [float(x) for x in sys.argv[3].split(",")]:
            Image.frombytes("RGB", (RC.W, RC.H), RC.render(int(tt * RC.FPS))).save(f"{out}/still_{tt:06.2f}.jpg", quality=88)
        sys.exit()
    NF = RC.NF
    print(f"duration {DUR:.1f}s, {NF} frames")
    step = math.ceil(NF / 4)
    jobs = [(i * step, min(NF, (i + 1) * step), f"{out}/part{i}.mp4") for i in range(4)]
    with Pool(4) as pool:
        parts = pool.map(RC.chunk, jobs)
    with open(f"{out}/list.txt", "w") as f:
        for p_ in parts: f.write(f"file '{os.path.abspath(p_)}'\n")
    print("done")
