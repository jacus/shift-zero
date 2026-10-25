#!/usr/bin/env python3
"""Render the Shift Zero hero animation (README + X).

    python3 assets/render_hero.py            # frames -> assets/build/
    then see assets/README.md for the ffmpeg GIF/MP4 commands.

Storyboard by Fable: a TEST slider crawls left (test last -> CI -> dev ->
TDD) until it snaps to zero, and the monolith shatters into thin vertical,
end-to-end-green slices. Quality before the first line.
"""
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H, S = 1200, 675, 2          # logical size, supersampling factor
FPS, DUR = 20, 18.0
OUT = Path(__file__).resolve().parent / "build"

BG = (11, 15, 20)
GREY = (42, 49, 59)
TXT = (242, 244, 247)
TXT2 = (139, 149, 165)
RED = (255, 59, 92)
AMBER = (255, 176, 32)
GREEN = (34, 227, 154)
CYAN = (76, 201, 255)

FONT_DIR = "/usr/share/fonts"
HEAD = f"{FONT_DIR}/opentype/inter/InterDisplay-ExtraBold.otf"
MONO = f"{FONT_DIR}/truetype/dejavu/DejaVuSansMono-Bold.ttf"
_fonts = {}


def font(path, size):
    key = (path, size)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(path, size * S)
    return _fonts[key]


# ---------------------------------------------------------------- easing

def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def prog(t, start, dur):
    return clamp((t - start) / dur)


def ease_out_cubic(p):
    return 1 - (1 - p) ** 3


def ease_in_out(p):
    return 3 * p * p - 2 * p * p * p


def ease_out_back(p, k=1.9):
    return 1 + (k + 1) * (p - 1) ** 3 + k * (p - 1) ** 2


def lerp(a, b, p):
    return a + (b - a) * p


def mix(c1, c2, p):
    return tuple(int(lerp(a, b, p)) for a, b in zip(c1, c2))


def fade(c, a):
    """Blend colour c over the background with alpha a (flat palette = small GIF)."""
    return mix(BG, c, clamp(a))


def window(t, start, end, fin=0.25, fout=0.25):
    """Alpha for an element visible in [start, end] with fades."""
    if t < start or t > end:
        return 0.0
    return min(clamp((t - start) / fin) if fin else 1, clamp((end - t) / fout) if fout else 1)


# ---------------------------------------------------------------- drawing

class Canvas:
    def __init__(self):
        self.img = Image.new("RGB", (W * S, H * S), BG)
        self.d = ImageDraw.Draw(self.img)

    def rect(self, x0, y0, x1, y1, fill, r=0):
        box = [x0 * S, y0 * S, x1 * S, y1 * S]
        if r:
            self.d.rounded_rectangle(box, radius=r * S, fill=fill)
        else:
            self.d.rectangle(box, fill=fill)

    def line(self, x0, y0, x1, y1, fill, w=2):
        self.d.line([x0 * S, y0 * S, x1 * S, y1 * S], fill=fill, width=w * S)

    def circle(self, cx, cy, r, fill=None, outline=None, w=0):
        self.d.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S],
                       fill=fill, outline=outline, width=w * S)

    def text(self, x, y, s, path, size, fill, anchor="la"):
        self.d.text((x * S, y * S), s, font=font(path, size), fill=fill, anchor=anchor)

    def check(self, cx, cy, r, color):
        pts = [(cx - r * 0.45, cy + r * 0.02), (cx - r * 0.1, cy + r * 0.38),
               (cx + r * 0.5, cy - r * 0.35)]
        self.d.line([(px * S, py * S) for px, py in pts], fill=color, width=int(r * 0.28 * S),
                    joint="curve")


# ---------------------------------------------------------------- the story

TL_X0, TL_X1, TL_Y, TL_H = 120, 1080, 392, 34
SEGMENTS = ["DESIGN", "BUILD", "BUILD", "BUILD"]
SLIDER_STOPS = [  # (time, x, label)
    (1.5, 1080, "TEST"),
    (4.0, 840, "CI"),
    (6.5, 600, "DEV"),
    (8.5, 360, "TDD"),
    (10.5, 120, "ZERO"),
]
BUG_STEPS = [(0.15, 1.15, 0, 47), (4.0, 0.6, 47, 29), (6.5, 0.5, 29, 12),
             (8.5, 0.5, 12, 3), (10.55, 0.3, 3, 0)]

HEADLINES = [  # start, end, text, color, size, sub, sub color
    (0.05, 1.45, "Tests? Later.", TXT, 84, None, None),
    (1.5, 3.95, "Build everything. Test last.", TXT, 66, "Retrofit tests: painful", AMBER),
    (4.0, 6.45, "Shift left.", TXT, 84, "Tests in CI", TXT2),
    (6.5, 8.45, "Shift left.", TXT, 84, "Tests during dev", TXT2),
    (8.5, 10.4, "Shift left. Harder.", TXT, 84, "TDD: test, then code", TXT2),
    (10.5, 13.4, "SHIFT ZERO", GREEN, 104, "Testability designed in. Thin slices. End to end.", TXT),
]

N_SLICES = 8
SLICE_W, SLICE_GAP = 100, 20
SLICE_TOP, SLICE_BOT = 312, 566
LAYERS = [("UI", 0.0), ("API", 1 / 3), ("DB", 2 / 3)]

random.seed(7)
BLOCK_JITTER = [random.uniform(0, 0.9) for _ in range(48)]


def bug_count(t):
    n = 0
    for start, dur, a, b in BUG_STEPS:
        if t >= start:
            n = round(lerp(a, b, ease_out_cubic(prog(t, start, dur))))
    return n


def slider(t):
    x, label = SLIDER_STOPS[0][1], SLIDER_STOPS[0][2]
    for i, (start, sx, lab) in enumerate(SLIDER_STOPS[1:], 1):
        if t >= start:
            p = prog(t, start, 0.3 if lab == "ZERO" else 0.55)
            e = ease_out_back(p) if lab == "ZERO" else ease_out_cubic(p)
            x = lerp(SLIDER_STOPS[i - 1][1], sx, e)
            label = lab if p > 0.3 else SLIDER_STOPS[i - 1][2]
    return x, label


def draw_headline(c, t):
    for start, end, text, color, size, sub, subc in HEADLINES:
        a = window(t, start, end, 0.18, 0.18)
        if a <= 0:
            continue
        # gentle rise-in
        dy = (1 - ease_out_cubic(prog(t, start, 0.35))) * 14
        c.text(60, 58 + dy, text, HEAD, size, fade(color, a))
        if sub:
            sa = window(t, start + 0.2, end, 0.25, 0.18)
            c.text(62, 58 + size + 22 + dy, sub, MONO, 32, fade(subc, sa))


def draw_counter(c, t):
    if t < 0.1 or t > 13.45:
        return
    a = window(t, 0.1, 13.45, 0.1, 0.25)
    n = bug_count(t)
    col = GREEN if n == 0 else (AMBER if n <= 12 else RED)
    s = f"BUGS: {n:>2}"
    c.text(W - 60, 66, s, MONO, 40, fade(col, a), anchor="ra")


def draw_pile(c, t):
    """Red bug blocks piled bottom-right; one block per bug."""
    if t > 11.4:
        return
    n = bug_count(t)
    cols, bw, bh, gap = 8, 40, 16, 6
    x0, y_floor = 1140 - cols * (bw + gap), 640
    out_a = 1 - prog(t, 10.6, 0.7)
    for i in range(n):
        row, col = divmod(i, cols)
        x = x0 + col * (bw + gap)
        y = y_floor - (row + 1) * (bh + gap)
        # Hook: blocks drop in as the counter ticks up.
        appear = 0.15 + (i / 47) * 1.0
        p = ease_out_cubic(prog(t, appear, 0.25))
        if p <= 0:
            continue
        y = lerp(-30, y, p) if t < 1.6 else y
        # Late pile tilts while tests come last (scene 1).
        if 1.8 < t < 4.0:
            y += math.sin((t - 1.8) * 3 + col) * (row * 0.8)
        color = RED if n > 12 else (AMBER if n > 3 else mix(AMBER, GREEN, 0.5))
        c.rect(x, y, x + bw, y + bh, fade(color, out_a), r=3)


def draw_timeline(c, t):
    a = window(t, 1.5, 13.5, 0.4, 0.3)
    shatter = prog(t, 10.5, 0.15)
    if a <= 0:
        return
    seg_w = (TL_X1 - TL_X0) / len(SEGMENTS)
    if shatter < 1:
        bar_a = a * (1 - shatter)
        for i, name in enumerate(SEGMENTS):
            x0 = TL_X0 + i * seg_w
            col = (52, 60, 72) if name == "DESIGN" else GREY
            c.rect(x0 + 2, TL_Y, x0 + seg_w - 2, TL_Y + TL_H, fade(col, bar_a), r=4)
            c.text(x0 + seg_w / 2, TL_Y + TL_H + 18, name, MONO, 26,
                   fade(TXT2, bar_a), anchor="ma")


def draw_zero_pulse(c, t):
    if 10.15 <= t < 10.55:
        p = (t - 10.15) / 0.4
        a = 0.4 + 0.6 * abs(math.sin(p * math.pi * 3))
        c.line(TL_X0, TL_Y - 50, TL_X0, TL_Y + TL_H + 30, fade(CYAN, a), 3)
        c.text(TL_X0, TL_Y + TL_H + 52, "0", MONO, 26, fade(CYAN, a), anchor="ma")


def draw_slider(c, t):
    a = window(t, 1.6, 10.9, 0.3, 0.4)
    if a <= 0:
        return
    x, label = slider(t)
    c.line(x, TL_Y - 44, x, TL_Y + TL_H + 10, fade(CYAN, a), 4)
    tag = label if label == "TEST" else f"TEST·{label}"
    tw = font(MONO, 26).getlength(tag) / S
    c.rect(x - tw / 2 - 14, TL_Y - 92, x + tw / 2 + 14, TL_Y - 50, fade(CYAN, a), r=10)
    c.text(x, TL_Y - 71, tag, MONO, 26, fade(BG, 1) if a > 0.5 else fade(CYAN, a), anchor="mm")
    # Snap flash at zero.
    fl = prog(t, 10.75, 0.35)
    if 0 < fl < 1:
        r = 20 + 160 * ease_out_cubic(fl)
        c.circle(TL_X0, TL_Y + TL_H / 2, r, outline=fade(CYAN, 1 - fl), w=4)


def draw_slices(c, t):
    if t < 10.55:
        return
    dim = 1 - 0.88 * ease_in_out(prog(t, 13.45, 0.4))
    alpha = dim * window(t, 10.55, 15.05, 0.01, 0.3)
    if alpha <= 0:
        return
    # Layer labels: every slice crosses every layer — that's "vertical".
    la = alpha * prog(t, 11.2, 0.4)
    band = (SLICE_BOT - SLICE_TOP) / len(LAYERS)
    for name, f in LAYERS:
        y = SLICE_TOP + f * (SLICE_BOT - SLICE_TOP) + band / 2
        c.text(TL_X0 - 18, y, name, MONO, 22, fade(TXT2, la), anchor="rm")
    for i in range(N_SLICES):
        x0 = TL_X0 + i * (SLICE_W + SLICE_GAP)
        st = 10.6 + i * 0.075
        grow = ease_out_cubic(prog(t, st, 0.35))
        top = lerp(TL_Y, SLICE_TOP, grow)
        bot = lerp(TL_Y + TL_H, SLICE_BOT, grow)
        c.rect(x0, top, x0 + SLICE_W, bot, fade(GREY, alpha), r=6)
        for _, f in LAYERS[1:]:
            ly = lerp(TL_Y, SLICE_TOP + f * (SLICE_BOT - SLICE_TOP), grow)
            c.line(x0 + 6, ly, x0 + SLICE_W - 6, ly, fade(BG, alpha), 2)
        fill = ease_in_out(prog(t, st + 0.3, 0.45))
        if fill > 0:
            fy = lerp(top, bot, fill)
            c.rect(x0, top, x0 + SLICE_W, fy, fade(GREEN, alpha), r=6)
            for _, f in LAYERS[1:]:
                ly = SLICE_TOP + f * (SLICE_BOT - SLICE_TOP)
                if ly < fy:
                    c.line(x0 + 6, ly, x0 + SLICE_W - 6, ly, fade(mix(GREEN, BG, 0.45), alpha), 2)
        pop = prog(t, st + 0.7, 0.25)
        if pop > 0:
            r = 17 * ease_out_back(pop)
            cx, cy = x0 + SLICE_W / 2, SLICE_TOP - 32
            c.circle(cx, cy, r, fill=fade(GREEN, alpha))
            c.check(cx, cy, r, fade(BG, 1) if alpha > 0.5 else fade(GREEN, alpha))


def draw_keyline(c, t):
    a = window(t, 13.55, 15.0, 0.3, 0.25)
    if a <= 0:
        return
    dy = (1 - ease_out_cubic(prog(t, 13.55, 0.4))) * 16
    c.text(W / 2, 250 + dy, "Quality before", HEAD, 96, fade(TXT, a), anchor="mm")
    c.text(W / 2, 360 + dy, "the first line.", HEAD, 96, fade(GREEN, a), anchor="mm")
    sa = window(t, 13.9, 15.0, 0.3, 0.25)
    c.text(W / 2, 470, "Claude Code · any agent via AGENTS.md", MONO, 28, fade(TXT2, sa), anchor="mm")


def draw_endcard(c, t):
    a = window(t, 15.1, DUR, 0.35, 0.45)
    if a <= 0:
        return
    c.text(W / 2, 230, "Shift Zero", HEAD, 120, fade(GREEN, a), anchor="mm")
    c.text(W / 2, 340, "Quality from start.", HEAD, 64, fade(TXT, a), anchor="mm")
    c.text(W / 2, 450, "github.com/jacus/shift-zero", MONO, 36, fade(CYAN, a), anchor="mm")
    c.text(W / 2, 505, "Open source · installs into your coding agent", MONO, 24,
           fade(TXT2, a), anchor="mm")


def render(t):
    c = Canvas()
    draw_slices(c, t)
    draw_timeline(c, t)
    draw_zero_pulse(c, t)
    draw_pile(c, t)
    draw_slider(c, t)
    draw_headline(c, t)
    draw_counter(c, t)
    draw_keyline(c, t)
    draw_endcard(c, t)
    img = c.img.resize((W, H), Image.LANCZOS)
    # Hook: hard shake while the bug counter slams up.
    if t < 1.5:
        k = (1 - t / 1.5) * 7
        dx, dy = int(math.sin(t * 97) * k), int(math.cos(t * 71) * k * 0.6)
        shaken = Image.new("RGB", (W, H), BG)
        shaken.paste(img, (dx, dy))
        img = shaken
    return img


def main():
    OUT.mkdir(exist_ok=True)
    only = float(sys.argv[1]) if len(sys.argv) > 1 else None
    if only is not None:
        render(only).save(OUT / f"still_{only:05.2f}.png")
        return
    n = int(DUR * FPS)
    for i in range(n):
        render(i / FPS).save(OUT / f"f{i:04d}.png")
    print(f"{n} frames -> {OUT}")


if __name__ == "__main__":
    main()
