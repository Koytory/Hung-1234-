
# ================================================================ OPENING: "Đi thăm phân khu Mùa Xuân"
CUT = 2.1          # clip boundary (IMG_2411 -> IMG_2415)
PINK, YELLOW = (255, 183, 197), (255, 211, 77)


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


# ---------------- petals (hoa đào / hoa mai) ----------------
def petal_sprite(col, size):
    s = size * 4
    im = Image.new("RGBA", (s, s)); d = ImageDraw.Draw(im)
    d.ellipse([s * .3, s * .15, s * .7, s * .85], fill=col + (235,))
    d.ellipse([s * .42, s * .2, s * .58, s * .5], fill=(255, 255, 255, 90))
    return im.resize((size, size), Image.LANCZOS)


rng = np.random.default_rng(3)
PETALS = []
for i in range(40):
    size = int(rng.uniform(26, 62)); col = PINK if rng.random() < 0.65 else YELLOW
    PETALS.append(dict(spr=petal_sprite(col, size), x=rng.uniform(-100, W), y=rng.uniform(-1900, H),
                       vx=rng.uniform(60, 160), vy=rng.uniform(220, 420), rot=rng.uniform(0, 360),
                       vr=rng.uniform(-200, 200), sway=rng.uniform(20, 60), ph=rng.uniform(0, 6.3),
                       blur=2 if size > 50 else 0))
for p in PETALS:
    if p["blur"]: p["spr"] = p["spr"].filter(ImageFilter.GaussianBlur(p["blur"]))


def draw_petals(c, t, alpha):
    for p in PETALS:
        x = (p["x"] + p["vx"] * t + p["sway"] * np.sin(2 * t + p["ph"])) % (W + 200) - 100
        y = (p["y"] + p["vy"] * t) % (H + 200) - 100
        im = p["spr"].rotate(p["rot"] + p["vr"] * t, Image.BICUBIC, expand=True)
        c.alpha_composite(alpha_mul(im, alpha), (int(x), int(y)))


# ---------------- timeline ----------------
E = []
E.append(Drop(text_img("ĐI THĂM PHÂN KHU", "serif", 100, grad=(GOLD_TOP, GOLD_BOT), max_w=W * .9), W / 2, 700, 0.05, 2.05))
E.append(El(text_img("Khám phá", "script", 84, WHITE), W / 2 - 200, 828, 0.35, 2.05, "fade", .2, .2))
E.append(Wipe(text_img("MÙA XUÂN", "cond", 250, MINT, glow=MINT_GLOW, glow_r=18), W / 2, 1015, 0.45, 2.05))
E.append(El(text_img("cùng mình", "script", 76, WHITE), W / 2 + 230, 1165, 0.95, 2.05, "fade", .2, .2))
E += words("cùng mình đi thăm phân khu Mùa Xuân", "it", 46, 1560, 0.5, 2.05, hl=("Mùa", "Xuân"))

E.append(El(text_img("Tận mắt xem", "light", 60), W / 2 - 60, 1015, CUT + .1, 4.06, "fade", .15, .2))
E.append(El(text_img("THỰC TẾ", "cond", 220, MINT, glow=MINT_GLOW), W / 2, 1140, CUT + .25, 4.06, "smear"))
E.append(El(text_img("từng góc phân khu", "script", 72, WHITE), W / 2 + 160, 1295, CUT + .55, 4.06, "fade", .15, .2))
E += words("cây xanh phủ kín mọi lối đi", "it", 46, 1560, CUT + .15, 4.06, hl=("cây", "xanh"))

LEAK_T = (1.85, 2.35)
PUNCHES = [0.0, CUT]


def make_leak():
    yy, xx = np.mgrid[0:H // 4, 0:W // 4].astype(np.float32)
    img = np.zeros((H // 4, W // 4, 3), np.float32)
    for (bx, by), r, col in [((0.2, 0.3), 0.55, (1, .55, .6)), ((0.7, 0.55), 0.5, (1, .85, .35)), ((0.4, 0.8), 0.45, (1, .6, .45))]:
        d = ((xx / (W / 4) - bx) ** 2 + (yy / (H / 4) - by) ** 2 * 0.35) / r ** 2
        img += np.exp(-d * 2.5)[..., None] * np.array(col, np.float32)
    return np.asarray(Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).resize((W * 2, H), Image.BILINEAR)).astype(np.float32) / 255


LEAK = make_leak()
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIGNETTE = (1 - 0.55 * (((xx / W - .5) ** 2 + (yy / H - .5) ** 2 * .6) / .35).clip(0, 1))[..., None]


def frame_fx(fr, t):
    z = 1.0 + 0.05 * t / 4.06
    if t < 0.4: z += 0.2 * (1 - ease(t / 0.4))                  # snap-in from zoomed
    if t >= CUT: z += 0.09 * (1 - ease((t - CUT) / 0.35))
    cw, ch = W / z, H / z
    fr = fr.resize((W, H), Image.BICUBIC, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2))
    blur = 0
    if t < 0.3: blur = 14 * (1 - t / 0.3)
    elif t < CUT: blur = 3
    if t > 3.8: blur = 10 * ease((t - 3.8) / 0.26)
    if blur > .3: fr = fr.filter(ImageFilter.GaussianBlur(blur))
    a = np.asarray(fr).astype(np.float32) / 255
    lum = a.mean(axis=2, keepdims=True)
    a = lum + (a - lum) * 1.22                                  # spring grade: more saturation
    a = a * np.array([1.06, 1.02, 0.95]) + np.array([0.02, 0.01, 0.0])   # warm
    if t < CUT:                                                 # hook: soft vignette for title legibility
        a = a * (0.35 + 0.65 * VIGNETTE) * 0.9
    if t < 0.12: a = a * (t / 0.12) + (1 - t / 0.12)           # white flash on the first frames
    t0, t1 = LEAK_T
    if t0 <= t <= t1:
        p = (t - t0) / (t1 - t0); s = np.sin(np.pi * p) ** 1.5 * 0.9; off = int(W * p)
        a = 1 - (1 - a) * (1 - LEAK[:, off:off + W] * s)
        a = a * (1 - .25 * s) + .25 * s * np.array([1, .88, .75])
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert("RGBA")


fsize = W * H * 3; n = 0
inp, outp = sys.stdin.buffer, sys.stdout.buffer
while True:
    buf = inp.read(fsize)
    if len(buf) < fsize: break
    t = n / FPS
    fr = frame_fx(Image.frombuffer("RGB", (W, H), buf), t)
    draw_petals(fr, t, 1.0 if t < CUT else 0.55)
    for e in E: e.draw(fr, t)
    outp.write(fr.convert("RGB").tobytes()); n += 1
