"""fxlib — thư viện hiệu ứng dùng chung cho skill bds.
Import:  sys.path.insert(0, "<skill>/scripts"); from fxlib import *
Gồm: text_img, stack, smear, El (smear/pop/fade/blur), Wipe, Drop, words (phụ đề từng từ),
glass_card/Glass (thẻ kính), bookmark_icon, make_leak/apply_leak (light leak), flash (ngả đỏ→chớp trắng),
zoom_blur (chuyển cảnh lao tới có nhòe tâm), grade_spring / grade_cinematic, petals,
PersonMask + Behind (chữ nằm SAU người), silhouette_flash (chớp trắng in hình người),
lower_third (thẻ tên + số điện thoại), run(frame_fx, elements) vòng lặp stdin→stdout."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts")
MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models", "selfie_segmenter.tflite")
F = {k: os.path.join(FD, v) for k, v in dict(
    cond="Barlow-XB.ttf", script="Dancing.ttf", serif="Playfair-XB.ttf", light="BVP-Light.ttf",
    med="BVP-Medium.ttf", it="BVP-MedIt.ttf", black="BVP-Black.ttf").items()}
W, H, FPS = 1080, 1920, 30
DUR = float(os.environ.get("VIDEO_DUR", "6.17"))
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




class Wipe(El):
    """Left-to-right reveal with a bright glowing edge + blur-out exit."""
    def draw(self, c, t):
        if not (self.t0 <= t <= self.t1): return
        p = ease((t - self.t0) / 0.42); q = max(0.0, 1 - (self.t1 - t) / 0.2)
        im = self.img.copy(); x = int(im.width * p)
        m = Image.new("L", im.size); ImageDraw.Draw(m).rectangle([0, 0, x, im.height], fill=255)
        im.putalpha(Image.composite(im.getchannel("A"), Image.new("L", im.size), m))
        if p < 1:
            bar = Image.new("RGBA", im.size)
            ImageDraw.Draw(bar).rectangle([x - 12, im.height * .2, x + 12, im.height * .8], fill=(220, 255, 245, 255))
            im = Image.alpha_composite(im, bar.filter(ImageFilter.GaussianBlur(16)))
        if q > 0: im = alpha_mul(im.filter(ImageFilter.GaussianBlur(14 * q)), 1 - q)
        c.alpha_composite(im, (int(self.cx - im.width / 2), int(self.cy - im.height / 2)))


class Drop(El):
    """Falls from above with a small bounce (title slam)."""
    def draw(self, c, t):
        if not (self.t0 <= t <= self.t1): return
        p = (t - self.t0) / 0.32; q = max(0.0, 1 - (self.t1 - t) / 0.2)
        if p < 1:
            y = self.cy - 160 * (1 - p) ** 2 + 18 * np.sin(np.pi * p) * (p > 0.7)
            a = min(1, p * 2.5)
        else:
            y, a = self.cy, 1
        im = self.img
        if p < 0.6: im = im.filter(ImageFilter.GaussianBlur(6 * (1 - p / 0.6)))
        if q > 0: im = im.filter(ImageFilter.GaussianBlur(14 * q))
        im = alpha_mul(im, a * (1 - q))
        c.alpha_composite(im, (int(self.cx - im.width / 2), int(y - im.height / 2)))


# ---------------- petals (hoa đào / hoa mai rơi) ----------------
PINK, YELLOW = (255, 183, 197), (255, 211, 77)


def petal_sprite(col, size):
    q = size * 4
    im = Image.new("RGBA", (q, q)); d = ImageDraw.Draw(im)
    d.ellipse([q * .3, q * .15, q * .7, q * .85], fill=col + (235,))
    d.ellipse([q * .42, q * .2, q * .58, q * .5], fill=(255, 255, 255, 90))
    return im.resize((size, size), Image.LANCZOS)


def make_petals(n=40, seed=3):
    rng = np.random.default_rng(seed); out = []
    for _ in range(n):
        size = int(rng.uniform(26, 62)); col = PINK if rng.random() < 0.65 else YELLOW
        spr = petal_sprite(col, size)
        if size > 50: spr = spr.filter(ImageFilter.GaussianBlur(2))
        out.append(dict(spr=spr, x=rng.uniform(-100, W), y=rng.uniform(-1900, H), vx=rng.uniform(60, 160),
                        vy=rng.uniform(220, 420), rot=rng.uniform(0, 360), vr=rng.uniform(-200, 200),
                        sway=rng.uniform(20, 60), ph=rng.uniform(0, 6.3)))
    return out


def draw_petals(c, t, alpha, petals):
    for p in petals:
        x = (p["x"] + p["vx"] * t + p["sway"] * np.sin(2 * t + p["ph"])) % (W + 200) - 100
        y = (p["y"] + p["vy"] * t) % (H + 200) - 100
        im = p["spr"].rotate(p["rot"] + p["vr"] * t, Image.BICUBIC, expand=True)
        c.alpha_composite(alpha_mul(im, alpha), (int(x), int(y)))


# ---------------- frame helpers (numpy float RGB 0..1) ----------------
def to_arr(fr): return np.asarray(fr.convert("RGB")).astype(np.float32) / 255
def to_img(a): return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert("RGBA")


def push_zoom(fr, z):
    """Crop-zoom around the centre (Ken Burns / punch)."""
    if z <= 1.001: return fr
    cw, ch = W / z, H / z
    return fr.resize((W, H), Image.BICUBIC, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2))


def make_leak(flip=False, warm=((1, .45, .1), (1, .8, .3), (1, .6, .2))):
    yy, xx = np.mgrid[0:H // 4, 0:W // 4].astype(np.float32)
    img = np.zeros((H // 4, W // 4, 3), np.float32)
    for (bx, by), r, col in zip([(0.2, 0.3), (0.7, 0.55), (0.4, 0.8)], [0.55, 0.5, 0.45], warm):
        if flip: by = 1 - by
        d = ((xx / (W / 4) - bx) ** 2 + (yy / (H / 4) - by) ** 2 * 0.35) / r ** 2
        img += np.exp(-d * 2.5)[..., None] * np.array(col, np.float32)
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).resize((W * 2, H), Image.BILINEAR)
    return np.asarray(im).astype(np.float32) / 255


def apply_leak(a, leak, p, strength=0.9):
    """p in 0..1 across the transition; screen-blend a sliding light leak."""
    s = np.sin(np.pi * p) ** 1.5 * strength; off = int(W * p)
    a = 1 - (1 - a) * (1 - leak[:, off:off + W] * s)
    return a * (1 - .25 * s) + .25 * s * np.array([1, .85, .6])


def flash(a, p, tint=(.95, .2, .25)):
    """p 0..1: red tint for the first 45 %, then white flash."""
    if p < .45: return a * (1 - .45 * p / .45) + np.array(tint) * .45 * p / .45
    w = np.sin(np.pi * (p - .45) / .55); return a * (1 - w) + w


def zoom_blur(fr, amount, steps=8):
    """Radial 'rush-in' blur (video mẫu 4: camera lao tới rồi cắt). amount 0..1."""
    if amount < 0.02: return fr
    acc = np.zeros((H, W, 3), np.float32)
    for k in range(steps):
        acc += to_arr(push_zoom(fr, 1 + 0.35 * amount * k / (steps - 1)))
    return to_img(acc / steps)


def grade_spring(a, sat=1.22):
    lum = a.mean(axis=2, keepdims=True); a = lum + (a - lum) * sat
    return a * np.array([1.06, 1.02, 0.95]) + np.array([0.02, 0.01, 0.0])


def grade_cinematic(a, sat=1.18):
    """Teal-orange, contrast and vignette like video mẫu 4."""
    lum = a.mean(axis=2, keepdims=True); a = lum + (a - lum) * sat
    shadows = np.clip(1 - lum * 2, 0, 1); highs = np.clip(lum * 2 - 1, 0, 1)
    a = a + shadows * np.array([-.03, .02, .05]) + highs * np.array([.05, .02, -.04])
    a = (a - .5) * 1.08 + .5
    return a * VIGNETTE_SOFT


_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIGNETTE = (1 - 0.55 * (((_xx / W - .5) ** 2 + (_yy / H - .5) ** 2 * .6) / .35).clip(0, 1))[..., None]
VIGNETTE_SOFT = 0.75 + 0.25 * VIGNETTE


# ---------------- person segmentation: chữ nằm sau người ----------------
class PersonMask:
    """Per-frame person mask (MediaPipe selfie segmenter). Needs: pip install mediapipe, apt libegl1 libgles2."""
    def __init__(self):
        import mediapipe as mp
        from mediapipe.tasks.python import vision, BaseOptions
        self.mp = mp
        self.seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
            base_options=BaseOptions(model_asset_path=MODEL), output_confidence_masks=True))
        self.cache = {}

    def get(self, fr, key):
        if key in self.cache: return self.cache[key]
        small = np.ascontiguousarray(np.asarray(fr.convert("RGB").resize((W // 2, H // 2))))
        r = self.seg.segment(self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=small))
        m = np.clip(np.array(r.confidence_masks[0].numpy_view()).squeeze(), 0, 1)
        m = Image.fromarray((m * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(2))
        self.cache = {key: m}
        return m


class Behind:
    """Wrap an element so the person in the frame is drawn OVER it (text behind subject)."""
    def __init__(self, el, pm): self.el, self.pm = el, pm; self.t0, self.t1 = el.t0, el.t1

    def draw(self, c, t, base=None):
        if not (self.t0 <= t <= self.t1): return
        person = c.copy() if base is None else base
        self.el.draw(c, t)
        c.paste(person, (0, 0), self.pm.get(person, round(t * FPS)))


def silhouette_flash(a, mask, p):
    """p 0..1: frame goes white except the person (video mẫu 2)."""
    w = np.sin(np.pi * p); m = np.asarray(mask).astype(np.float32)[..., None] / 255
    return a * m + (a * (1 - w) + w) * (1 - m)


def lower_third(name, line2, w=620):
    """Thẻ tên kính mờ (video mẫu 4: tên + số điện thoại khi dẫn ở cuối)."""
    f1 = ImageFont.truetype(F["black"], 46); f2 = ImageFont.truetype(F["med"], 36)
    h = 140; im = Image.new("RGBA", (w + 40, h + 40)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([20, 20, 20 + w, 20 + h], 28, fill=(20, 20, 20, 150), outline=MINT + (255,), width=3)
    d.ellipse([44, 44, 136, 136], fill=MINT + (255,))
    d.text((158, 36), name, font=f1, fill=WHITE); d.text((158, 96), line2, font=f2, fill=(220, 220, 220))
    return im


def run(frame_fx, elements, overlay=None):
    """Main loop: rgb24 1080x1920 frames on stdin -> fx -> elements -> stdout."""
    fsize = W * H * 3; n = 0
    inp, outp = sys.stdin.buffer, sys.stdout.buffer
    while True:
        buf = inp.read(fsize)
        if len(buf) < fsize: break
        t = n / FPS
        fr = frame_fx(Image.frombuffer("RGB", (W, H), buf).convert("RGBA"), t)
        base = fr.copy()
        if overlay: overlay(fr, t)
        for e in elements:
            if isinstance(e, Behind): e.draw(fr, t, base)
            else: e.draw(fr, t)
        outp.write(fr.convert("RGB").tobytes()); n += 1


# ================= /bds 2 — người dẫn + tour điện ảnh (video mẫu 4 + 5) =================
PURPLE, TEAL, PILL_Y, STRIKE_RED = (124, 77, 196), (63, 184, 196), (245, 197, 24), (230, 40, 50)


def gradient_text(text, font, size, c1=(255, 90, 220), c2=(90, 230, 255), glow=True):
    """Chữ gradient ngang hồng→xanh có glow (kiểu 'TOP 1%')."""
    base = text_img(text, font, size, WHITE, glow=None, shadow=False)
    w, h = base.size
    x = np.linspace(0, 1, w)[None, :, None]
    arr = (np.array(c1) * (1 - x) + np.array(c2) * x) * np.ones((h, 1, 1))
    col = Image.fromarray(arr.astype(np.uint8)).convert("RGBA"); col.putalpha(base.getchannel("A"))
    if not glow: return col
    g = col.filter(ImageFilter.GaussianBlur(16))
    out = Image.alpha_composite(Image.new("RGBA", (w, h)), g)
    out = Image.alpha_composite(out, g)
    return Image.alpha_composite(out, col)


def strike(im, color=STRIKE_RED, width=10):
    """Gạch ngang đỏ qua chữ (kiểu 'IS NOT')."""
    im = im.copy(); a = np.asarray(im.getchannel("A")) > 40
    ys, xs = np.where(a)
    if len(xs):
        y = int(ys.mean()); ImageDraw.Draw(im).line([(xs.min() - 10, y), (xs.max() + 10, y)], fill=color + (255,), width=width)
    return im


def pill_tag(text, size=40):
    """Nhãn viên thuốc đen viền vàng (kiểu 'Character', 'Integrity') bật ra quanh người."""
    f = ImageFont.truetype(F["black"], size); l, _, r, _ = f.getbbox(text); asc, desc = f.getmetrics()
    w, h = int(r - l + size * 1.4), int(asc + desc + size * .7)
    im = Image.new("RGBA", (w + 30, h + 30)); d = ImageDraw.Draw(im)
    sh = Image.new("RGBA", im.size); ImageDraw.Draw(sh).rounded_rectangle([15, 19, 15 + w, 19 + h], h // 2, fill=(0, 0, 0, 120))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    d.rounded_rectangle([15, 15, 15 + w, 15 + h], h // 2, fill=(20, 20, 20, 235), outline=PILL_Y + (255,), width=4)
    d.text((15 + size * .7 - l, 15 + size * .3), text, font=f, fill=WHITE)
    return im


def cta_pill(text, size=34):
    """Nút CTA bo tròn có avatar tròn (kiểu 'Click the link in my bio')."""
    f = ImageFont.truetype(F["med"], size); l, _, r, _ = f.getbbox(text)
    h = int(size * 2.1); w = int(r - l + h + size * 1.2)
    im = Image.new("RGBA", (w + 20, h + 20)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([10, 10, 10 + w, 10 + h], h // 2, fill=(245, 245, 245, 235))
    d.ellipse([16, 16, 4 + h, 4 + h], fill=TEAL + (255,))
    d.text((10 + h + size * .4 - l, 10 + (h - size) / 2 - 4), text, font=f, fill=(30, 30, 30))
    return im


def bloom_flash(a, p):
    """Cắt cảnh 'cháy sáng' (video mẫu 5): khung lóa trắng + loang sáng, p 0..1."""
    w = np.sin(np.pi * p)
    small = to_img(a).resize((W // 4, H // 4)).filter(ImageFilter.GaussianBlur(12)).resize((W, H))
    b = to_arr(small)
    return np.clip(a * (1 + 1.6 * w) + b * 1.2 * w + 0.25 * w, 0, 1)


KSTYLE = {   # kiểu chữ từ khóa của phụ đề động (/bds 2)
    "thin":   lambda s: text_img(s, "light", 64, WHITE, glow_r=4),
    "serif":  lambda s: text_img(s.upper(), "serif", 120, PURPLE, glow_r=6, max_w=W * .9),
    "bold":   lambda s: text_img(s.upper(), "black", 92, PURPLE, glow_r=6, max_w=W * .9),
    "script": lambda s: text_img(s, "script", 120, TEAL, glow_r=6, max_w=W * .9),
    "teal":   lambda s: text_img(s.upper(), "black", 104, TEAL, glow_r=6, max_w=W * .9),
    "mint":   lambda s: text_img(s.upper(), "cond", 190, MINT, glow=MINT_GLOW, max_w=W * .9),
    "glow":   lambda s: gradient_text(s.upper(), "black", 150),
    "strike": lambda s: strike(text_img(s.upper(), "black", 104, WHITE, glow_r=6)),
}


def kinetic(lines, t0, t1, cy=1000, gap=12, step=0.18, pm=None, behind=()):
    """Phụ đề động kiểu video mẫu 5: các dòng xếp chồng giữa ngực người dẫn, mỗi dòng 1 kiểu
    (lines = [("để mình", "thin"), ("BẢNG GIÁ", "serif"), ...]); từng dòng blur-in lần lượt.
    Dòng có index trong `behind` nằm sau người (cần pm=PersonMask())."""
    imgs = [KSTYLE[st](tx) for tx, st in lines]
    hs = [im.height - 40 for im in imgs]; total = sum(hs) + gap * (len(imgs) - 1)
    y = cy - total / 2; out = []
    for i, im in enumerate(imgs):
        el = El(im, W / 2, y + hs[i] / 2, t0 + i * step, t1, "blur", .16, .18, "blur")
        out.append(Behind(el, pm) if (pm is not None and i in behind) else el)
        y += hs[i] + gap
    return out
