import math as m
import random as r
import turtle as t
import tkinter.font as tkf

SC = 21
OY = 20
DURATION = 10
TICK = 16
ANIM = 42
LIFT = 34
GAP = 7
SIZES = (9, 10, 11, 12)
FONT = "Arial"
BG = "#030005"

s = t.Screen()
s.setup(800, 800)
s.bgcolor(BG)
s.title("Love Heart")
s.tracer(0)

cv = s.getcanvas()
rng = r.Random(11)

PHRASES = [
    "I love you", "Seni seviyorum", "Te amo", "Je t'aime",
    "Ich liebe dich", "Ti amo", "Eu te amo", "Я тебя люблю",
    "사랑해", "愛してる", "我爱你", "मैं तुमसे प्यार करता हूँ",
    "Σ' αγαπώ", "Ik hou van jou", "Jag älskar dig", "Kocham cię",
    "ฉันรักเธอ", "Anh yêu em", "Aku cinta kamu", "Я тебе кохаю",
]

_fonts = {}


def font_for(size):
    if size not in _fonts:
        _fonts[size] = tkf.Font(
            root=cv, family=FONT, size=size, weight="bold"
        )
    return _fonts[size]


def heart(a):
    x = 16 * (m.sin(a) ** 3)
    y = (
        13 * m.cos(a)
        - 5 * m.cos(2 * a)
        - 2 * m.cos(3 * a)
        - m.cos(4 * a)
    )
    return x * SC, y * SC + OY


def hx(c):
    return "#%02x%02x%02x" % tuple(
        int(max(0, min(1, v)) * 255) for v in c
    )


def mix(a, b, k):
    return tuple(p + (q - p) * k for p, q in zip(a, b))


def dim(c, k):
    return tuple(v * k for v in c)


POLY = [heart(2 * m.pi * i / 720) for i in range(720)]
EDGES = list(zip(POLY, POLY[1:] + POLY[:1]))
YMAX = max(p[1] for p in POLY)
YMIN = min(p[1] for p in POLY)
CY = (YMAX + YMIN) / 2


def spans(y):
    xs = []
    for (x1, y1), (x2, y2) in EDGES:
        if (y1 <= y < y2) or (y2 <= y < y1):
            xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
    xs.sort()
    return list(zip(xs[0::2], xs[1::2]))


def intersect(A, B):
    out = []
    for a in A:
        for b in B:
            lo, hi = max(a[0], b[0]), min(a[1], b[1])
            if hi - lo > 14:
                out.append((lo, hi))
    return out


def phrase_cycle():
    while True:
        order = PHRASES[:]
        rng.shuffle(order)
        yield from order


def build():
    cycle = phrase_cycle()
    row_h = max(font_for(z).metrics("linespace") for z in SIZES) + 4
    half = row_h / 2
    placed = []

    y = YMAX - half
    while y > YMIN + half:
        row = intersect(spans(y + half), spans(y - half))

        for lo, hi in row:
            lo += 4
            hi -= 4
            cur = lo + rng.uniform(0, 8)
            line = []

            while True:
                fit = None
                for _ in range(10):
                    text = next(cycle)
                    size = rng.choice(SIZES)
                    w = font_for(size).measure(text)
                    if cur + w <= hi:
                        fit = (text, size, w)
                        break
                if not fit:
                    break
                text, size, w = fit
                line.append([cur + w / 2, text, size, w])
                cur += w + GAP

            if not line:
                continue

            if len(line) > 1:
                left = hi - (line[-1][0] + line[-1][3] / 2)
                for i, it in enumerate(line):
                    it[0] += left * i / (len(line) - 1)
            else:
                line[0][0] = (lo + hi) / 2

            for i, (x, text, size, w) in enumerate(line):
                edge = i == 0 or i == len(line) - 1
                placed.append(dict(x=x, y=y, text=text, size=size, edge=edge))

        y -= row_h

    wine = (0.30, 0.04, 0.62)
    crimson = (0.55, 0.12, 0.88)
    blood = (0.72, 0.28, 1.0)
    for p in placed:
        rad = min(1.0, math_dist(p["x"], p["y"]))
        base = mix(wine, crimson, 0.25 + 0.75 * rad)
        base = mix(base, blood, rng.uniform(0, 0.35) + (0.3 if p["edge"] else 0))
        p["color"] = tuple(min(1, v) for v in base)
        p["rad"] = rad

    edges = [p for p in placed if p["edge"]]
    inner = [p for p in placed if not p["edge"]]
    edges.sort(key=lambda p: m.atan2(p["x"], p["y"] - CY) % (2 * m.pi))
    inner.sort(key=lambda p: -p["rad"] + rng.uniform(0, 0.08))
    return edges + inner


def math_dist(x, y):
    return m.hypot(x / (16 * SC), (y - CY) / (14.5 * SC))


FLASH = (0.88, 0.76, 1.0)
WORD_COLORS = (
    (1.0, 0.25, 0.35),
    (1.0, 0.65, 0.15),
    (1.0, 0.9, 0.25),
    (0.25, 1.0, 0.55),
    (0.2, 0.75, 1.0),
    (0.8, 0.4, 1.0),
)
main_ids = []
active = []
tick_no = 0


def clamp(v):
    return max(0.0, min(1.0, v))


def spawn(p):
    x, y = p["x"], -p["y"]
    size, text = p["size"], p["text"]
    font = (FONT, size, "bold")
    big = (FONT, size + 1, "bold")
    words = text.split()
    word_widths = [font_for(size).measure(word) for word in words]
    space_width = font_for(size).measure(" ")
    total_width = sum(word_widths) + space_width * (len(words) - 1)
    left = x - total_width / 2
    color_offset = rng.randrange(len(WORD_COLORS))
    layers = []

    for i, (word, width) in enumerate(zip(words, word_widths)):
        word_x = left + width / 2
        word_color = WORD_COLORS[(color_offset + i) % len(WORD_COLORS)]
        shadow = cv.create_text(
            word_x + 2, y + 3, text=word, font=font, fill=BG
        )
        halo = cv.create_text(word_x, y, text=word, font=big, fill=BG)
        main = cv.create_text(word_x, y - LIFT, text=word, font=font, fill=BG)
        layers.append((shadow, halo, main, word_color, word_x))
        main_ids.append((main, word_color))
        left += width + space_width

    p.update(layers=layers, f=0, dx=rng.uniform(-10, 10))
    active.append(p)


def animate(p):
    p["f"] += 1
    u = clamp(p["f"] / ANIM)
    e = 1 - (1 - u) ** 3
    y = -p["y"]
    hover = (1 - e) * LIFT
    py = y - hover

    flash = 0.75 * math_sin(clamp((u - 0.55) / 0.45))
    for shadow, halo, main, c, x in p["layers"]:
        px = x + p["dx"] * (1 - e)
        cv.itemconfig(shadow, fill=hx(mix(BGC, dim(c, 0.30), e)))
        cv.itemconfig(halo, fill=hx(mix(BGC, dim(c, 0.20), e * e)))
        cv.coords(halo, px, py)

        col = mix(mix(BGC, c, e ** 1.5), FLASH, flash)
        cv.itemconfig(main, fill=hx(col))
        cv.coords(main, px, py)

        if u >= 1:
            cv.coords(halo, x, y)
            cv.coords(main, x, y)
            cv.itemconfig(main, fill=hx(c))
    if u < 1:
        return True
    return False


def math_sin(v):
    return m.sin(m.pi * v)


BGC = tuple(int(BG[i:i + 2], 16) / 255 for i in (1, 3, 5))
ORDER = build()
items = iter(ORDER)
RATE = len(ORDER) / (DURATION * 1000 / TICK)
acc = 0.0
spawning = True


def step():
    global spawning, acc
    if spawning:
        acc += RATE
        try:
            while acc >= 1:
                acc -= 1
                spawn(next(items))
        except StopIteration:
            spawning = False

    active[:] = [p for p in active if animate(p)]

    if not spawning and not active:
        shimmer()
        return
    cv.after(TICK, step)


def _safe(i, c):
    try:
        cv.itemconfig(i, fill=hx(c))
    except Exception:
        pass


def shimmer():
    for _ in range(1):
        i, c = rng.choice(main_ids)
        _safe(i, mix(c, FLASH, 0.6))
        cv.after(260, lambda i=i, c=c: _safe(i, c))
    cv.after(140, shimmer)


try:
    cv.after(200, step)
    t.done()
except (t.Terminator, Exception):
    pass