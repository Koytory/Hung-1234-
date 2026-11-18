"""Re-edit in the style of the reference videos:
- hook title card at the start (gold serif + script + big mint keyword)
- light-leak / white-flash / red-tint transitions, zoom punches, blur in/out
- 3-tier keyword text (small white line, big mint condensed keyword with motion-smear
  entry/exit, script accent word), italic subtitle with a mint-highlighted keyword
- tilted glass info card with mint border, 'LƯU VIDEO' + bookmark CTA at the end.
Reads rgb24 1080x1920 frames on stdin, writes rgb24 to stdout."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
F = {k: os.path.join(FD, v) for k, v in dict(
    cond="Barlow-XB.ttf", script="Dancing.ttf", serif="Playfair-XB.ttf", light="BVP-Light.ttf",
    med="BVP-Medium.ttf", it="BVP-MedIt.ttf", black="BVP-Black.ttf").items()}
W, H, FPS, DUR = 1080, 1920, 30, 6.17
MINT, MINT_GLOW = (100, 255, 210), (0, 200, 160)
WHITE, GOLD_TOP, GOLD_BOT = (255, 255, 255), (255, 244, 214), (214, 170, 96)


def ease(x):
    x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3


# ---------------------------------------------------------------- text rendering
def text_img(text, font, size, fill=WHITE, glow=None, glow_r=14, shadow=True, max_w=None, grad=None, stroke=0):
    f = ImageFont.truetype(F[font], size)
    while max_w and f.getlength(text) > max_w and size > 20:
        size -= 4; f = ImageFont.truetype(F[font], size)
    l, _, r, _ = f.getbbox(text, stroke_width=stroke); asc, desc = f.getmetrics()
    pad = glow_r * 3 + 12
    w, h = int(r - l + 2 * pad), int(asc + desc + 2 * pad + stroke * 2)
    mask = Image.new("L", (w, h)); empty = Image.new("RGBA", (w, h))
    ImageDraw.Draw(mask).text((pad - l, pad + stroke), text, font=f, fill=255, stroke_width=stroke, stroke_fill=255)
    out = Image.new("RGBA", (w, h))
    if shadow:
        sh = mask.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(6))
        out.paste(Image.new("RGBA", (w, h), (0, 0, 0, 190)), (0, 4), sh)
    if glow:
        g = mask.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(glow_r))
        for _ in range(2):
            out = Image.alpha_composite(out, Image.composite(Image.new("RGBA", (w, h), glow + (255,)), empty, g))
    if grad:
        y = np.linspace(0, 1, h)[:, None, None]
        arr = (np.array(grad[0]) * (1 - y) + np.array(grad[1]) * y) * np.ones((1, w, 1))
        fillimg = Image.fromarray(arr.astype(np.uint8)).convert("RGBA")
    else:
        fillimg = Image.new("RGBA", (w, h), fill + (255,))
    return Image.alpha_composite(out, Image.composite(fillimg, empty, mask))


def stack(parts, gap=0):
    """parts: list of (img, dx, dy) relative offsets -> single composed image centred at (0,0)."""
    xs = [dx - im.width / 2 for im, dx, dy in parts] + [dx + im.width / 2 for im, dx, dy in parts]
    ys = [dy - im.height / 2 for im, dx, dy in parts] + [dy + im.height / 2 for im, dx, dy in parts]
    x0, y0 = min(xs), min(ys)
    c = Image.new("RGBA", (int(max(xs) - x0) + 2, int(max(ys) - y0) + 2))
    for im, dx, dy in parts:
        c.alpha_composite(im, (int(dx - im.width / 2 - x0), int(dy - im.height / 2 - y0)))
    return c, -x0 - c.width / 2, -y0 - c.height / 2  # image and offset of (0,0) from its centre


def alpha_mul(im, a):
    if a >= 0.999: return im
    im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * max(0, a)))); return im


def smear(im, amount, direction=1):
    """Horizontal motion smear + shear, like the references' text whip."""
    if amount < 0.02: return im
    n = 9; dist = int(140 * amount)
    arr = np.asarray(im).astype(np.float32)
    pm = arr.copy(); pm[..., :3] *= pm[..., 3:4] / 255
    padw = dist + 4
    acc = np.zeros((arr.shape[0], arr.shape[1] + 2 * padw, 4), np.float32)
    for k in range(n):
        off = padw + int((k / (n - 1) - 0.5) * dist * direction)
        acc[:, off:off + arr.shape[1]] += pm
    acc /= n
    rgb = np.where(acc[..., 3:4] > 0, acc[..., :3] * 255 / np.maximum(acc[..., 3:4], 1e-3), 0)
    out = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), acc[..., 3]]).astype(np.uint8), "RGBA")
    sh = 0.35 * amount * direction
    return out.transform(out.size, Image.AFFINE, (1, sh, -sh * out.height / 2, 0, 1, 0), Image.BILINEAR)


class El:
    """mode: 'smear' (whip in from left, whip out right), 'pop', 'fade', 'blur' (blur in)."""
    def __init__(self, img, cx, cy, t0, t1, mode="fade", tin=0.22, tout=0.2, exit="smear"):
        self.img, self.cx, self.cy, self.t0, self.t1 = img, cx, cy, t0, t1
        self.mode, self.tin, self.tout, self.exit = mode, tin, tout, exit

    def draw(self, c, t):
        if not (self.t0 <= t <= self.t1): return
        p = ease((t - self.t0) / self.tin); q = max(0.0, 1 - (self.t1 - t) / self.tout)
        im, x, a = self.img, self.cx, p * (1 - q)
        if self.mode == "smear" and p < 1:
            im = smear(im, 1 - p, 1); x -= 220 * (1 - p)
        elif self.mode == "pop" and p < 1:
            s = 1.35 - 0.35 * p; im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        elif self.mode == "blur" and p < 1:
            im = im.filter(ImageFilter.GaussianBlur(14 * (1 - p)))
        if q > 0:
            if self.exit == "smear": im = smear(im, q, 1); x += 220 * q
            else: im = im.filter(ImageFilter.GaussianBlur(14 * q))
        im = alpha_mul(im, a)
        c.alpha_composite(im, (int(x - im.width / 2), int(self.cy - im.height / 2)))


def words(text, font, size, cy, t0, t1, step=0.12, fill=WHITE, hl=(), x_center=W / 2):
    """Word-by-word reveal; words in `hl` are mint."""
    f = ImageFont.truetype(F[font], size)
    x = x_center - f.getlength(text) / 2
    out, prefix = [], ""
    for i, wd in enumerate(text.split(" ")):
        col = MINT if wd in hl else fill
        im = text_img(wd, font, size, col, glow_r=4)
        pad = 4 * 3 + 12
        out.append(El(im, x + f.getlength(prefix) + im.width / 2 - pad, cy, t0 + i * step, t1, "fade", 0.1, 0.15, "blur"))
        prefix += wd + " "
    return out


def glass_card(lines, w=640, tilt=-6):
    pad = 34; f = ImageFont.truetype(F["med"], 44); fb = ImageFont.truetype(F["black"], 50)
    asc, desc = f.getmetrics(); lh = asc + desc + 8
    h = pad * 2 + lh * len(lines)
    card = Image.new("RGBA", (w + 60, h + 60))
    d = ImageDraw.Draw(card)
    glow = Image.new("RGBA", card.size)
    ImageDraw.Draw(glow).rounded_rectangle([30, 30, 30 + w, 30 + h], 26, outline=MINT + (255,), width=8)
    card.alpha_composite(glow.filter(ImageFilter.GaussianBlur(10)))
    d.rounded_rectangle([30, 30, 30 + w, 30 + h], 26, fill=(255, 255, 255, 55), outline=MINT + (255,), width=3)
    y = 30 + pad
    for i, ln in enumerate(lines):
        d.text((30 + pad, y), ln, font=fb if i == 0 else f, fill=MINT if i == 0 else WHITE)
        y += lh
    mask = Image.new("L", card.size)
    ImageDraw.Draw(mask).rounded_rectangle([30, 30, 30 + w, 30 + h], 26, fill=255)
    return card.rotate(tilt, Image.BICUBIC, expand=True), mask.rotate(tilt, Image.BICUBIC, expand=True)


class Glass(El):
    """Glass card that blurs the frame behind it (frosted)."""
    def __init__(self, card, mask, cx, cy, t0, t1):
        super().__init__(card, cx, cy, t0, t1, "pop", 0.22, 0.2, "blur"); self.mask = mask

    def draw(self, c, t):
        if not (self.t0 <= t <= self.t1): return
        p = ease((t - self.t0) / self.tin); q = max(0.0, 1 - (self.t1 - t) / self.tout); a = p * (1 - q)
        s = 1.2 - 0.2 * p
        im = self.img.resize((int(self.img.width * s), int(self.img.height * s)), Image.LANCZOS)
        m = self.mask.resize(im.size, Image.LANCZOS)
        x0, y0 = int(self.cx - im.width / 2), int(self.cy - im.height / 2)
        region = c.crop((x0, y0, x0 + im.width, y0 + im.height)).filter(ImageFilter.GaussianBlur(18))
        c.paste(region, (x0, y0), m.point(lambda v: int(v * a)))
        c.alpha_composite(alpha_mul(im, a), (x0, y0))


def bookmark_icon(size=110):
    im = Image.new("RGBA", (size + 40, size + 40)); d = ImageDraw.Draw(im)
    d.ellipse([20, 20, 20 + size, 20 + size], outline=WHITE + (255,), width=5)
    cx, cy, s = 20 + size / 2, 20 + size / 2, size * 0.24
    d.polygon([(cx - s, cy - s * 1.4), (cx + s, cy - s * 1.4), (cx + s, cy + s * 1.4), (cx, cy + s * 0.6), (cx - s, cy + s * 1.4)],
              fill=(255, 200, 40, 255))
    sh = Image.new("RGBA", im.size); sh.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(5)).point(lambda v: v // 2))
    return Image.alpha_composite(sh, im)


# ---------------------------------------------------------------- timeline
E = []
# HOOK title card (0 - 1.3 s)
_gl = text_img("giữa lòng", "script", 76, WHITE)
_tp = text_img("THÀNH PHỐ", "serif", 104, grad=(GOLD_TOP, GOLD_BOT))
_row = _gl.width + _tp.width - 2 * 54 + 20        # 54 = text padding inside each image
hook, ox, oy = stack([
    (text_img("ĐÔ THỊ VEN SÔNG", "serif", 104, grad=(GOLD_TOP, GOLD_BOT), max_w=W * 0.9), 0, -250),
    (_gl, -_row / 2 + _gl.width / 2 - 54, -128),
    (_tp, _row / 2 - _tp.width / 2 + 54, -135),
    (text_img("Khám phá sa bàn", "script", 74, WHITE), -110, 10),
    (text_img("PALM CITY", "cond", 230, MINT, glow=MINT_GLOW, glow_r=18), 0, 135),
])
E.append(El(hook, W / 2 + ox, 1000 + oy, 0.0, 1.3, "pop", 0.25, 0.25, "blur"))

# Scene A (1.45 - 3.0): 3-tier keyword
E.append(El(text_img("Tận mắt xem", "light", 60), W / 2 - 60, 1015, 1.45, 3.0, "fade", 0.15, 0.2))
E.append(El(text_img("SA BÀN", "cond", 210, MINT, glow=MINT_GLOW), W / 2, 1140, 1.65, 3.0, "smear"))
E.append(El(text_img("dự án thực tế", "script", 72, WHITE), W / 2 + 150, 1265, 1.95, 3.0, "fade", 0.15, 0.2))
E += words("Tận mắt xem sa bàn dự án thực tế", "it", 46, 1560, 1.5, 3.0, hl=("sa", "bàn"))

# Scene B (3.2 - 4.75): script accent + keyword + glass card
E.append(El(text_img("Trọn tầm", "script", 80, WHITE), W / 2 - 160, 470, 3.25, 4.75, "fade", 0.15, 0.2))
E.append(El(text_img("VIEW SÔNG", "cond", 190, MINT, glow=MINT_GLOW), W / 2, 590, 3.35, 4.75, "smear"))
card, cmask = glass_card(["PALM CITY", "Tổng diện tích 30,6 HA", "Bao quanh công viên xanh"])
E.append(Glass(card, cmask, W / 2 + 40, 1260, 3.7, 4.75))
E += words("căn hộ ven sông giữa công viên xanh", "it", 46, 1560, 3.25, 4.75, hl=("ven", "sông"))

# Scene C (4.95 - 6.17): CTA
E.append(El(text_img("Inbox ngay để nhận", "light", 60), W / 2, 880, 4.95, 5.55, "fade", 0.15, 0.2))
E.append(El(text_img("BẢNG GIÁ", "cond", 220, MINT, glow=MINT_GLOW), W / 2, 1010, 5.05, 5.55, "smear"))
E.append(El(text_img("chi tiết", "script", 76, WHITE), W / 2 + 190, 1135, 5.2, 5.55, "fade", 0.15, 0.2))
E.append(El(text_img("LƯU VIDEO", "cond", 170, MINT, glow=MINT_GLOW), W / 2 + 70, 1060, 5.62, 6.17, "pop", 0.15, 0.01))
E.append(El(bookmark_icon(), W / 2 - 300, 1040, 5.7, 6.17, "pop", 0.15, 0.01))
E += words("lưu lại để xem bảng giá nhé", "it", 46, 1560, 4.95, 6.17, hl=("bảng", "giá"))

# ---------------------------------------------------------------- frame FX
LEAKS = [(1.15, 1.6, 0), (4.6, 5.05, 1)]
FLASH = (2.9, 3.3)            # red tint -> white flash
PUNCHES = [1.45, 3.15, 4.95, 5.62]


def make_leak(flip):
    yy, xx = np.mgrid[0:H // 4, 0:W // 4].astype(np.float32)
    img = np.zeros((H // 4, W // 4, 3), np.float32)
    for (bx, by), r, col in [((0.2, 0.3), 0.55, (1, .45, .1)), ((0.7, 0.55), 0.5, (1, .8, .3)), ((0.4, 0.8), 0.45, (1, .6, .2))]:
        if flip: by = 1 - by
        d = ((xx / (W / 4) - bx) ** 2 + (yy / (H / 4) - by) ** 2 * 0.35) / r ** 2
        img += np.exp(-d * 2.5)[..., None] * np.array(col, np.float32)
    return np.asarray(Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).resize((W * 2, H), Image.BILINEAR)).astype(np.float32) / 255


LEAK = [make_leak(0), make_leak(1)]


def zoom_at(t):
    z = 1.0 + 0.05 * t / DUR
    for p in PUNCHES:
        if t >= p: z += 0.09 * (1 - ease((t - p) / 0.35))
    return z


def frame_fx(fr, t):
    z = zoom_at(t)
    cw, ch = W / z, H / z
    fr = fr.resize((W, H), Image.BICUBIC, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2))
    blur = 0
    if t < 1.3: blur = 6                                     # hook: soft background
    if 3.15 <= t < 3.45: blur = 16 * (1 - ease((t - 3.15) / 0.3))
    if t > 5.62: blur = 10 * ease((t - 5.62) / 0.3)
    if blur > 0.3: fr = fr.filter(ImageFilter.GaussianBlur(blur))
    a = np.asarray(fr).astype(np.float32) / 255
    if t < 1.3: a *= 0.62                                    # hook: darken for title legibility
    for t0, t1, k in LEAKS:
        if t0 <= t <= t1:
            p = (t - t0) / (t1 - t0); s = np.sin(np.pi * p) ** 1.5 * 0.9; off = int(W * p)
            lk = LEAK[k][:, off:off + W] if k == 0 else LEAK[k][:, W - off:2 * W - off]
            a = 1 - (1 - a) * (1 - lk * s)
            a = a * (1 - 0.25 * s) + 0.25 * s * np.array([1, .85, .6])
    f0, f1 = FLASH
    if f0 <= t <= f1:
        p = (t - f0) / (f1 - f0)
        if p < 0.4: a = a * (1 - 0.5 * p / 0.4) + np.array([0.9, 0.15, 0.1]) * 0.5 * p / 0.4   # red tint
        else:
            w = np.sin(np.pi * (p - 0.4) / 0.6); a = a * (1 - w) + w                       # white flash
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert("RGBA")


fsize = W * H * 3; n = 0
inp, outp = sys.stdin.buffer, sys.stdout.buffer
while True:
    buf = inp.read(fsize)
    if len(buf) < fsize: break
    t = n / FPS
    fr = frame_fx(Image.frombuffer("RGB", (W, H), buf), t)
    for e in E: e.draw(fr, t)
    outp.write(fr.convert("RGB").tobytes()); n += 1
