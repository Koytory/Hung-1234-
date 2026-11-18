
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
D = 6.8667                                          # inserted IMG_2414 length
C2, C2B, C3, C4, END = 4.0, 4.0 + D, 13.1667 + D, 28.9333 + D, 31.1333 + D   # 2415->2414, 2414->2419, 2419->2435, freeze, end
TURN = 21.0 + D                                        # walker turns back toward camera
E = []
# A. hook
E.append(Drop(text_img("ĐI THĂM PHÂN KHU", "serif", 100, grad=(GOLD_TOP, GOLD_BOT), max_w=W * .9), W / 2, 700, 0.05, 2.05))
E.append(El(text_img("Khám phá", "script", 84, WHITE), W / 2 - 200, 828, 0.35, 2.05, "fade", .2, .2))
E.append(Wipe(text_img("MÙA XUÂN", "cond", 250, MINT, glow=MINT_GLOW, glow_r=18), W / 2, 1015, 0.45, 2.05))
E.append(El(text_img("cùng mình", "script", 76, WHITE), W / 2 + 230, 1165, 0.95, 2.05, "fade", .2, .2))
E += words("cùng mình đi thăm phân khu Mùa Xuân", "it", 46, 1560, 0.5, 2.05, hl=("Mùa", "Xuân"))
# B. thực tế
def tier(top, big, script, t0, t1, y=1140, sx=150):
    out = [El(text_img(top, "light", 60), W / 2 - 60, y - 125, t0, t1, "fade", .15, .2),
           El(text_img(big, "cond", 220, MINT, glow=MINT_GLOW, max_w=W * .9), W / 2, y, t0 + .15, t1, "smear"),
           El(text_img(script, "script", 72, WHITE), W / 2 + sx, y + 155, t0 + .45, t1, "fade", .15, .2)]
    return out
E += tier("Tận mắt xem", "THỰC TẾ", "từng góc phân khu", CUT + .1, C2)
E += words("cây xanh phủ kín mọi lối đi", "it", 46, 1560, CUT + .15, C2, hl=("cây", "xanh"))
# C0. wide shot of the facade (IMG_2414)
E += tier("Mặt tiền", "THOÁNG ĐÃNG", "đón trọn gió trời", C2 + .15, C2 + 3.3)
E += words("mặt tiền nhìn thẳng ra đường nội khu", "it", 46, 1560, C2 + .2, C2 + 3.3, hl=("mặt", "tiền"))
E += tier("Khoảng sân", "XANH MÁT", "trước mỗi căn nhà", C2 + 3.5, C2B - .05)
E += words("sân trước trồng cây xanh mát quanh năm", "it", 46, 1560, C2 + 3.55, C2B - .05, hl=("xanh", "mát"))
# C. pan along villa row
E += tier("Từng dãy nhà", "XANH MƯỚT", "rợp bóng cây", C2B + .15, 7.8 + D)
E += words("mỗi dãy nhà đều phủ kín cây xanh", "it", 46, 1560, C2B + .2, 7.8 + D, hl=("cây", "xanh"))
card, cmask = glass_card(["PHÂN KHU MÙA XUÂN", "Cây xanh rợp bóng mọi lối đi", "Không gian sống yên bình"], w=720)
E.append(Glass(card, cmask, W / 2 + 20, 1080, 8.1 + D, 12.9 + D))
E += words("đi tới đâu cũng thấy mát mắt", "it", 46, 1560, 8.1 + D, 12.9 + D, hl=("mát", "mắt"))
# D. garden path walk
E += tier("Lối đi", "NỘI KHU", "rợp bóng hoa giấy", C3 + .25, TURN - .1, y=1060)
E += words("lối đi nội khu rợp bóng hoa giấy", "it", 46, 1560, C3 + .3, TURN - .1, hl=("hoa", "giấy"))
E += tier("Về đây", "SỐNG CHẬM", "an yên mỗi ngày", TURN + .2, 27.7 + D, y=1060)
E += words("về đây sống chậm, an yên mỗi ngày", "it", 46, 1560, TURN + .25, 27.7 + D, hl=("an", "yên"))
# E. CTA
E.append(El(text_img("Inbox ngay để nhận", "light", 60), W / 2, 880, 27.9 + D, 29.6 + D, "fade", .15, .2))
E.append(El(text_img("BẢNG GIÁ", "cond", 220, MINT, glow=MINT_GLOW), W / 2, 1010, 28.05 + D, 29.6 + D, "smear"))
E.append(El(text_img("chi tiết", "script", 76, WHITE), W / 2 + 190, 1135, 28.3 + D, 29.6 + D, "fade", .15, .2))
E.append(El(text_img("LƯU VIDEO", "cond", 170, MINT, glow=MINT_GLOW), W / 2 + 70, 1060, 29.7 + D, END, "pop", 0.15, 0.01))
E.append(El(bookmark_icon(), W / 2 - 300, 1040, 29.78 + D, END, "pop", 0.15, 0.01))
E += words("lưu lại để xem bảng giá nhé", "it", 46, 1560, 27.95 + D, END, hl=("bảng", "giá"))

LEAKS = [(1.85, 2.35), (3.75, 4.25), (C2B - .25, C2B + .25), (TURN - .25, TURN + .25), (27.65 + D, 28.15 + D)]
FLASH = (C3 - .3, C3 + .15)
PUNCHES = [CUT, C2, C2B, C3]


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
    seg0 = max(x for x in (0, CUT, C2, C2B, C3) if x <= t)
    z = 1.0 + 0.05 * min(1, (t - seg0) / 9)                     # slow push-in per shot
    if t < 0.4: z += 0.2 * (1 - ease(t / 0.4))                  # snap-in from zoomed
    for p in PUNCHES:
        if t >= p: z += 0.09 * (1 - ease((t - p) / 0.35))
    cw, ch = W / z, H / z
    fr = fr.resize((W, H), Image.BICUBIC, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2))
    blur = 0
    if t < 0.3: blur = 14 * (1 - t / 0.3)
    elif t < CUT: blur = 3
    if C3 <= t < C3 + .3: blur = 16 * (1 - ease((t - C3) / .3))
    if t > 29.55 + D: blur = 11 * ease((t - 29.55 - D) / .4)
    if blur > .3: fr = fr.filter(ImageFilter.GaussianBlur(blur))
    a = np.asarray(fr).astype(np.float32) / 255
    lum = a.mean(axis=2, keepdims=True)
    a = lum + (a - lum) * 1.22                                  # spring grade: more saturation
    a = a * np.array([1.06, 1.02, 0.95]) + np.array([0.02, 0.01, 0.0])   # warm
    if t < CUT:                                                 # hook: soft vignette for title legibility
        a = a * (0.35 + 0.65 * VIGNETTE) * 0.9
    if t < 0.12: a = a * (t / 0.12) + (1 - t / 0.12)           # white flash on the first frames
    for t0, t1 in LEAKS:
        if t0 <= t <= t1:
            p = (t - t0) / (t1 - t0); s = np.sin(np.pi * p) ** 1.5 * 0.9; off = int(W * p)
            a = 1 - (1 - a) * (1 - LEAK[:, off:off + W] * s)
            a = a * (1 - .25 * s) + .25 * s * np.array([1, .88, .75])
    f0, f1 = FLASH
    if f0 <= t <= f1:
        p = (t - f0) / (f1 - f0)
        if p < .45: a = a * (1 - .45 * p / .45) + np.array([.95, .2, .25]) * .45 * p / .45
        else: w = np.sin(np.pi * (p - .45) / .55); a = a * (1 - w) + w
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert("RGBA")


fsize = W * H * 3; n = 0
inp, outp = sys.stdin.buffer, sys.stdout.buffer
while True:
    buf = inp.read(fsize)
    if len(buf) < fsize: break
    t = n / FPS
    fr = frame_fx(Image.frombuffer("RGB", (W, H), buf), t)
    draw_petals(fr, t, 1.0 if t < CUT else (0.5 if t > 27.6 + D else 0.38))
    for e in E: e.draw(fr, t)
    outp.write(fr.convert("RGB").tobytes()); n += 1
