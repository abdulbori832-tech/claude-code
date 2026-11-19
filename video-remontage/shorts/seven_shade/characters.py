"""Faceless glowing 'figure of light' characters for the shorts renderer.

A figure wears a long robe (thobe), has a round head with no face and two
articulated arms. Poses: stand, walk, sit (kneeling). Angles are radians from
straight down; positive = towards the side the figure faces.
"""
import math
from PIL import Image, ImageDraw, ImageFilter


def _rgba(c, a):
    return (int(c[0]), int(c[1]), int(c[2]), int(max(0, min(1, a)) * 255))


def figure(d, x, y, h, color, a, facing=1, lean=0.0, head_down=0.0, mode="stand",
           phase=0.0, front=(0.15, 0.1), back=(-0.12, 0.08), head_turn=0.0):
    """Draw one figure. (x, y) = point between the feet on the ground."""
    if a <= 0:
        return
    f = facing
    fill = _rgba(color, a)
    if mode == "sit":
        hip = (x - 0.02 * h * f, y - 0.2 * h)
        torso_len = 0.33 * h
    else:
        hip = (x, y - 0.46 * h)
        torso_len = 0.34 * h
    sh = (hip[0] + math.sin(lean) * torso_len * f, hip[1] - math.cos(lean) * torso_len)
    # head
    hl = lean + head_down
    hr = 0.078 * h
    head = (sh[0] + math.sin(hl) * 0.12 * h * f + head_turn * 0.02 * h, sh[1] - math.cos(hl) * 0.12 * h)
    d.ellipse((head[0] - hr, head[1] - hr, head[0] + hr, head[1] + hr), fill=fill)
    # neck
    d.line((sh[0], sh[1], head[0], head[1]), fill=fill, width=int(0.06 * h))
    # robe (local coords: dx is towards the facing side)
    def P(dx, dy):
        return (x + dx * f, y + dy)
    sw = 0.09 * h
    if mode == "sit":
        poly = [(sh[0] - sw * f, sh[1]), (sh[0] + sw * f, sh[1]), P(0.13 * h, -0.2 * h), P(0.24 * h, -0.06 * h),
                P(0.24 * h, 0), P(-0.12 * h, 0), P(-0.13 * h, -0.12 * h), P(-0.1 * h, -0.24 * h)]
        d.polygon(poly, fill=fill)
        d.ellipse((sh[0] - sw, sh[1] - 0.045 * h, sh[0] + sw, sh[1] + 0.05 * h), fill=fill)
        bx0, bx1 = sorted((x - 0.13 * h * f, x + 0.26 * h * f))
        d.rounded_rectangle((bx0, y - 0.08 * h, bx1, y), 0.04 * h, fill=fill)
    else:
        sway = math.sin(phase) * 0.025 * h if mode == "walk" else 0
        hem = y - 0.035 * h
        poly = [(sh[0] - sw, sh[1]), (sh[0] + sw, sh[1]), (hip[0] + 0.085 * h, hip[1]),
                (x + 0.15 * h + sway, hem), (x - 0.15 * h + sway, hem), (hip[0] - 0.085 * h, hip[1])]
        d.polygon(poly, fill=fill)
        d.ellipse((sh[0] - sw, sh[1] - 0.045 * h, sh[0] + sw, sh[1] + 0.05 * h), fill=fill)
        d.rounded_rectangle((x - 0.15 * h + sway, hem - 0.03 * h, x + 0.15 * h + sway, hem + 0.004 * h), 0.015 * h, fill=fill)
        st = math.sin(phase) * 0.06 * h if mode == "walk" else 0
        for k, off in ((1, st), (-1, -st)):
            fx = x + k * 0.05 * h + off * f
            lift = max(0, math.sin(phase * (1 if k > 0 else -1))) * 0.015 * h if mode == "walk" else 0
            d.ellipse((fx - 0.05 * h + 0.02 * h * f, y - 0.035 * h - lift, fx + 0.05 * h + 0.02 * h * f, y - lift), fill=fill)
    # arms (back arm first so the front arm is drawn over the robe)
    aw = int(0.048 * h)
    for (a1, a2) in (back, front):
        L1, L2 = 0.165 * h, 0.155 * h
        el = (sh[0] + math.sin(a1 + lean) * L1 * f, sh[1] + 0.02 * h + math.cos(a1 + lean) * L1)
        hd = (el[0] + math.sin(a1 + a2 + lean) * L2 * f, el[1] + math.cos(a1 + a2 + lean) * L2)
        edge = _rgba(tuple(v * 0.62 for v in color), a)
        for wdt, cc in ((aw + max(3, int(0.012 * h)), edge), (aw, fill)):
            d.line((sh[0], sh[1] + 0.02 * h, el[0], el[1]), fill=cc, width=wdt)
            d.line((el[0], el[1], hd[0], hd[1]), fill=cc, width=wdt)
            r0 = wdt / 2
            d.ellipse((el[0] - r0, el[1] - r0, el[0] + r0, el[1] + r0), fill=cc)
        for p, r in ((el, aw / 2), (hd, aw * 0.62)):
            d.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=fill)
    return {"head": head, "chest": ((sh[0] + hip[0]) / 2 + 0.03 * h * f, sh[1] + 0.09 * h), "shoulder": sh}


def hand_pos(x, y, h, facing, lean, arm, mode="stand"):
    """Where the hand of `arm` ends up (same maths as figure)."""
    f = facing
    hip = (x - 0.02 * h * f, y - 0.2 * h) if mode == "sit" else (x, y - 0.46 * h)
    tl = 0.33 * h if mode == "sit" else 0.34 * h
    sh = (hip[0] + math.sin(lean) * tl * f, hip[1] - math.cos(lean) * tl)
    a1, a2 = arm
    el = (sh[0] + math.sin(a1 + lean) * 0.165 * h * f, sh[1] + 0.02 * h + math.cos(a1 + lean) * 0.165 * h)
    return (el[0] + math.sin(a1 + a2 + lean) * 0.155 * h * f, el[1] + math.cos(a1 + a2 + lean) * 0.155 * h)


def glow_layer(lay, strength=1.0, radius=10):
    """Soft bloom for a figure layer (computed at quarter size for speed)."""
    small = lay.resize((lay.width // 4, lay.height // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(radius))
    g = small.resize(lay.size, Image.BILINEAR)
    if strength != 1.0:
        al = g.getchannel("A").point(lambda v: min(255, int(v * strength)))
        g.putalpha(al)
    out = Image.new("RGBA", lay.size, (0, 0, 0, 0))
    out.alpha_composite(g)
    out.alpha_composite(lay)
    return out


# Poses (front arm, back arm)
ARMS_DOWN = ((0.12, 0.08), (-0.1, 0.06))
ARMS_DUA = ((0.55, 2.05), (0.4, 2.1))           # hands raised in front of the chest
ARM_STOP = ((1.3, 1.15), (-0.1, 0.06))           # palm forward: "stop"
ARM_GIVE = ((0.95, 0.35), (-0.55, -1.2))           # front arm out and down, back arm behind the back
ARMS_SHADE = ((2.2, 1.75), (-0.08, 0.06))          # hand above the eyes
ARMS_READ = ((0.45, 1.45), (0.35, 1.5))            # holding a book
ARM_REACH = ((1.25, 0.15), (-0.1, 0.06))           # handshake reach
