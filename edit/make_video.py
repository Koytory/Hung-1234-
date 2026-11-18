"""Frame-by-frame edit in the reference video's style: Ken Burns + zoom punches,
orange light-leak transitions, blur in/out, glowing keyword wipe/pop, word-by-word
light text, boxed subtitles. Reads rgb24 1080x1920 frames on stdin, writes rgb24 to stdout."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FD = os.path.join(HERE, "fonts")
W, H, FPS = 1080, 1920, 30
BLACK, MED, LIGHT = (os.path.join(FD, f) for f in ("BVP-Black.ttf", "BVP-Medium.ttf", "BVP-Light.ttf"))
MINT, MINT_GLOW = (110, 255, 214), (0, 214, 170)
RED, RED_GLOW = (232, 28, 36), (120, 0, 0)
WHITE = (255, 255, 255)


def ease(x):
    x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3


def text_img(text, font, size, fill, glow=None, glow_r=16, shadow=True, max_w=None):
    f = ImageFont.truetype(font, size)
    while max_w and f.getlength(text) > max_w and size > 20:
        size -= 4; f = ImageFont.truetype(font, size)
    l, _, r, _ = f.getbbox(text)
    asc, desc = f.getmetrics()
    pad = glow_r * 3 + 10
    w, h = int(r - l + 2 * pad), int(asc + desc + 2 * pad)
    base = Image.new("RGBA", (w, h)); mask = Image.new("L", (w, h))
    ImageDraw.Draw(mask).text((pad - l, pad), text, font=f, fill=255)
    out = Image.new("RGBA", (w, h))
    if shadow:
        sh = mask.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(5))
        out.paste(Image.new("RGBA", (w, h), (0, 0, 0, 200)), (0, 3), sh)
    if glow:
        g = mask.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(glow_r))
        layer = Image.new("RGBA", (w, h), glow + (255,))
        for _ in range(2):
            out = Image.alpha_composite(out, Image.composite(layer, base, g))
    out = Image.alpha_composite(out, Image.composite(Image.new("RGBA", (w, h), fill + (255,)), base, mask))
    return out, pad


def with_alpha(im, a):
    if a >= 1: return im
    im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a))); return im


class Pop:
    """Pop-in (scale 1.35->1 + fade), blur-out exit like the reference."""
    def __init__(self, img, cx, cy, t0, t1, pop=True, blur_out=True):
        self.img, self.cx, self.cy, self.t0, self.t1, self.pop, self.blur_out = img, cx, cy, t0, t1, pop, blur_out

    def draw(self, c, t):
        if not (self.t0 <= t <= self.t1): return
        p = ease((t - self.t0) / 0.18)
        out = max(0.0, 1 - (self.t1 - t) / 0.2)  # 0 -> 1 during the last 0.2 s
        im = self.img
        s = 1.35 - 0.35 * p if self.pop else 1.0
        if s != 1.0:
            im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        if self.blur_out and out > 0:
            im = im.filter(ImageFilter.GaussianBlur(out * 14))
        im = with_alpha(im, p * (1 - out))
        c.alpha_composite(im, (int(self.cx - im.width / 2), int(self.cy - im.height / 2)))


class Wipe(Pop):
    """Left-to-right reveal with a bright glowing edge (reference 'Bảo Chứng' style)."""
    def draw(self, c, t):
        if not (self.t0 <= t <= self.t1): return
        p = ease((t - self.t0) / 0.4)
        out = max(0.0, 1 - (self.t1 - t) / 0.2)
        im = self.img.copy()
        x = int(im.width * p)
        a = im.getchannel("A")
        m = Image.new("L", im.size); ImageDraw.Draw(m).rectangle([0, 0, x, im.height], fill=255)
        im.putalpha(Image.composite(a, Image.new("L", im.size), m))
        if p < 1:
            bar = Image.new("RGBA", im.size)
            ImageDraw.Draw(bar).rectangle([x - 10, im.height * 0.25, x + 10, im.height * 0.75], fill=(200, 255, 240, 255))
            bar = bar.filter(ImageFilter.GaussianBlur(14))
            im = Image.alpha_composite(im, bar)
        if out > 0:
            im = with_alpha(im.filter(ImageFilter.GaussianBlur(out * 14)), 1 - out)
        c.alpha_composite(im, (int(self.cx - im.width / 2), int(self.cy - im.height / 2)))


def subtitle(text, t0, t1, cy=1540):
    f = ImageFont.truetype(MED, 40)
    l, _, r, _ = f.getbbox(text); asc, desc = f.getmetrics()
    w, h = int(r - l + 44), int(asc + desc + 22)
    im = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=12, fill=(30, 30, 30, 140))
    d.text((22 - l, 9), text, font=f, fill=WHITE)
    return Pop(im, W / 2, cy, t0, t1, pop=False, blur_out=False)


def words_line(text, size, cy, t0, t1, step=0.14):
    f = ImageFont.truetype(LIGHT, size)
    x = (W - f.getlength(text)) / 2
    items, prefix = [], ""
    for i, wd in enumerate(text.split(" ")):
        img, pad = text_img(wd, LIGHT, size, WHITE, glow_r=4)
        items.append(Pop(img, x + f.getlength(prefix) + img.width / 2 - pad, cy, t0 + i * step, t1, pop=False))
        prefix += wd + " "
    return items


# ---------------- timeline ----------------
E = []
big, _ = text_img("PALM CITY", BLACK, 160, MINT, glow=MINT_GLOW, max_w=W * 0.86)
E.append(Wipe(big, W / 2, 1060, 0.05, 1.9))
s1, _ = text_img("Tổng diện tích 30,6 HA", MED, 50, WHITE)
E.append(Pop(s1, W / 2, 1180, 0.55, 1.9, pop=False))
E.append(subtitle("sa bàn dự án Palm City", 0.1, 1.95))

E += words_line("Tận mắt xem sa bàn", 66, 470, 2.15, 4.0)
E += words_line("dự án thực tế", 66, 560, 2.75, 4.0)
vs, _ = text_img("VIEW SÔNG", BLACK, 150, MINT, glow=MINT_GLOW, max_w=W * 0.86)
E.append(Pop(vs, W / 2, 1080, 3.05, 4.0))
E.append(subtitle("căn hộ ven sông, bao quanh công viên xanh", 2.15, 4.0))

s3, _ = text_img("liên hệ ngay để nhận", MED, 54, WHITE)
E.append(Pop(s3, W / 2, 1010, 4.2, 6.2, pop=False))
bg, _ = text_img("BẢNG GIÁ", BLACK, 170, RED, glow=RED_GLOW, glow_r=10, max_w=W * 0.86)
E.append(Pop(bg, W / 2, 1150, 4.4, 6.2))
E.append(subtitle("inbox để được tư vấn chi tiết", 4.3, 6.2))

PUNCHES = [2.05, 4.1]           # zoom punch right after each transition
LEAKS = [(1.8, 2.3, 0), (3.9, 4.35, 1)]  # orange light-leak transitions


def make_leak(seed):
    yy, xx = np.mgrid[0:H // 4, 0:W // 4].astype(np.float32)
    img = np.zeros((H // 4, W // 4, 3), np.float32)
    blobs = [((0.2, 0.3), 0.55, (1.0, 0.45, 0.1)), ((0.7, 0.55), 0.5, (1.0, 0.8, 0.3)), ((0.4, 0.8), 0.45, (1.0, 0.6, 0.2))]
    if seed: blobs = [((x, 1 - y), r, col) for (x, y), r, col in blobs]
    for (bx, by), r, col in blobs:
        d = ((xx / (W / 4) - bx) ** 2 + (yy / (H / 4) - by) ** 2 * 0.35) / r ** 2
        img += np.exp(-d * 2.5)[..., None] * np.array(col, np.float32)
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).resize((W * 2, H), Image.BILINEAR)
    return np.asarray(im).astype(np.float32) / 255


leak_imgs = [make_leak(0), make_leak(1)]


def zoom_at(t):
    z = 1.0 + 0.04 * t / 6.2
    for p in PUNCHES:
        if t >= p: z += 0.10 * (1 - ease((t - p) / 0.35))
    return z


def blur_at(t):
    r = 0.0
    if 4.0 <= t < 4.35: r = 18 * (1 - ease((t - 4.0) / 0.35))      # blur -> sharp after transition 2
    if t > 5.8: r = max(r, 16 * ease((t - 5.8) / 0.37))          # ending blur-out
    return r


fsize = W * H * 3
n = 0
inp, outp = sys.stdin.buffer, sys.stdout.buffer
while True:
    buf = inp.read(fsize)
    if len(buf) < fsize: break
    t = n / FPS
    fr = Image.frombuffer("RGB", (W, H), buf)
    z = zoom_at(t)
    if z > 1.001:
        cw, ch = W / z, H / z
        fr = fr.resize((W, H), Image.BICUBIC, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2))
    r = blur_at(t)
    if r > 0.3: fr = fr.filter(ImageFilter.GaussianBlur(r))
    a = np.asarray(fr).astype(np.float32) / 255
    for (t0, t1, k) in LEAKS:
        if t0 <= t <= t1:
            p = (t - t0) / (t1 - t0)
            strength = np.sin(np.pi * p) ** 1.5 * 0.85
            off = int(W * p)
            lk = leak_imgs[k][:, off:off + W] if k == 0 else leak_imgs[k][:, W - off:2 * W - off]
            a = 1 - (1 - a) * (1 - lk * strength)          # screen blend
            a = a * (1 - 0.25 * strength) + 0.25 * strength * np.array([1, 0.85, 0.6])  # warm wash
    fr = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert("RGBA")
    for e in E: e.draw(fr, t)
    outp.write(fr.convert("RGB").tobytes())
    n += 1
