"""Eco 2 — Đi thăm phân khu Mùa Xuân (v3): adds text-behind-person, zoom-blur rush cut,
silhouette white flash (learned from reference video 4). Uses the bds skill fxlib."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fxlib import *

CUT = 2.1
PM = PersonMask()
PETALS = make_petals()
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
def tier(top, big, script, t0, t1, y=1140, sx=150, behind=False):
    k = El(text_img(big, "cond", 220, MINT, glow=MINT_GLOW, max_w=W * .9), W / 2, y, t0 + .15, t1, "smear")
    out = [El(text_img(top, "light", 60), W / 2 - 60, y - 125, t0, t1, "fade", .15, .2),
           Behind(k, PM) if behind else k,
           El(text_img(script, "script", 72, WHITE), W / 2 + sx, y + 155, t0 + .45, t1, "fade", .15, .2)]
    return out
E += tier("Tận mắt xem", "THỰC TẾ", "từng góc phân khu", CUT + .1, C2, behind=True)
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
E += tier("Lối đi", "NỘI KHU", "rợp bóng hoa giấy", C3 + .25, TURN - .1, y=1060, behind=True)
E += words("lối đi nội khu rợp bóng hoa giấy", "it", 46, 1560, C3 + .3, TURN - .1, hl=("hoa", "giấy"))
E += tier("Về đây", "SỐNG CHẬM", "an yên mỗi ngày", TURN + .2, 27.7 + D, y=1060, behind=True)
E += words("về đây sống chậm, an yên mỗi ngày", "it", 46, 1560, TURN + .25, 27.7 + D, hl=("an", "yên"))
# E. CTA
E.append(El(text_img("Inbox ngay để nhận", "light", 60), W / 2, 880, 27.9 + D, 29.6 + D, "fade", .15, .2))
E.append(Behind(El(text_img("BẢNG GIÁ", "cond", 220, MINT, glow=MINT_GLOW), W / 2, 1010, 28.05 + D, 29.6 + D, "smear"), PM))
E.append(El(text_img("chi tiết", "script", 76, WHITE), W / 2 + 190, 1135, 28.3 + D, 29.6 + D, "fade", .15, .2))
E.append(El(text_img("LƯU VIDEO", "cond", 170, MINT, glow=MINT_GLOW), W / 2 + 70, 1060, 29.7 + D, END, "pop", 0.15, 0.01))
E.append(El(bookmark_icon(), W / 2 - 300, 1040, 29.78 + D, END, "pop", 0.15, 0.01))
E += words("lưu lại để xem bảng giá nhé", "it", 46, 1560, 27.95 + D, END, hl=("bảng", "giá"))

LEAKS = [(1.85, 2.35), (3.75, 4.25), (27.65 + D, 28.15 + D)]
FLASH = (C3 - .3, C3 + .15)
SIL = (TURN - .22, TURN + .22)          # silhouette white flash on the turn-around
RUSH = (C2B - .3, C2B + .25)            # zoom-blur rush cut 2414 -> 2419
PUNCHES = [CUT, C2, C3]
LEAK = make_leak(warm=((1, .55, .6), (1, .85, .35), (1, .6, .45)))


def frame_fx(fr, t):
    seg0 = max(x for x in (0, CUT, C2, C2B, C3) if x <= t)
    z = 1.0 + 0.05 * min(1, (t - seg0) / 9)
    if t < 0.4: z += 0.2 * (1 - ease(t / 0.4))
    for p in PUNCHES:
        if t >= p: z += 0.09 * (1 - ease((t - p) / 0.35))
    fr = push_zoom(fr, z)
    r0, r1 = RUSH
    if r0 <= t < C2B: fr = zoom_blur(fr, ease((t - r0) / (C2B - r0)))
    elif C2B <= t < r1: fr = zoom_blur(fr, 1 - ease((t - C2B) / (r1 - C2B)))
    blur = 0
    if t < 0.3: blur = 14 * (1 - t / 0.3)
    elif t < CUT: blur = 3
    if C3 <= t < C3 + .3: blur = 16 * (1 - ease((t - C3) / .3))
    if t > 29.55 + D: blur = 11 * ease((t - 29.55 - D) / .4)
    if blur > .3: fr = fr.filter(ImageFilter.GaussianBlur(blur))
    a = grade_spring(to_arr(fr))
    if t < CUT: a = a * (0.35 + 0.65 * VIGNETTE) * 0.9
    if t < 0.12: a = a * (t / 0.12) + (1 - t / 0.12)
    for t0, t1 in LEAKS:
        if t0 <= t <= t1: a = apply_leak(a, LEAK, (t - t0) / (t1 - t0))
    if FLASH[0] <= t <= FLASH[1]: a = flash(a, (t - FLASH[0]) / (FLASH[1] - FLASH[0]))
    if SIL[0] <= t <= SIL[1]:
        a = silhouette_flash(a, PM.get(fr, round(t * FPS)), (t - SIL[0]) / (SIL[1] - SIL[0]))
    return to_img(a)


run(frame_fx, E, overlay=lambda fr, t: draw_petals(fr, t, 1.0 if t < CUT else (0.5 if t > 27.6 + D else 0.38), PETALS))
