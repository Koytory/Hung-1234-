---
name: bds-video-edit
description: Phong cách edit video bất động sản (BĐS) dạng TikTok/Reels dọc 9:16 mà người dùng đã chọn — chữ xanh ngọc phát sáng, chữ viết tay điểm nhấn, chuyển cảnh light leak / chớp trắng, nhạc nền + SFX tự tạo. Dùng khi người dùng gửi video và nhờ "thêm text", "edit", "làm video BĐS", hoặc gửi video mẫu để "học thêm" phong cách mới (khi đó cập nhật file này).
---

# Phong cách edit video BĐS

Người dùng nói tiếng Việt → trả lời bằng tiếng Việt. Video đầu ra: MP4 dọc 1080x1920, 30fps, H.264 + AAC, âm lượng ~ -15 LUFS.

## Công cụ có sẵn trong skill này
- `scripts/make_video.py` — hiệu ứng hình + chữ, đọc/ghi frame rgb24 qua stdin/stdout. Phần `# --- timeline` là nơi viết nội dung chữ và thời điểm.
- `scripts/make_audio.py` — tự tạo nhạc nền (pad + pluck arpeggio + kick/hat 120bpm) và SFX (pop, tick, whoosh, riser, impact, ding, shimmer). Phần `# ---------- SFX ----------` (các dòng `add(...)`) là nơi căn thời điểm SFX khớp với chữ/chuyển cảnh.
- `scripts/render.sh <input> <output.mp4> [ambient_vol]` — chạy toàn bộ: tạo audio, render hình, trộn tiếng gốc (mặc định 15%).
- `fonts/` — font hỗ trợ đủ dấu tiếng Việt (OFL, từ Google Fonts):
  - `Barlow-XB` (chữ khóa to, đậm hẹp) · `Dancing` (chữ viết tay) · `Playfair-XB` (chữ có chân, tiêu đề hook)
  - `BVP-Light` (dòng trắng mảnh) · `BVP-Medium` · `BVP-MedIt` (phụ đề nghiêng) · `BVP-Black`

Cần Python 3 + Pillow + numpy và ffmpeg. Thời lượng tự lấy từ video gốc (`VIDEO_DUR`), nhưng **timeline chữ và SFX phải viết lại theo nội dung/độ dài video mới**.

## Quy trình
1. Xem video gốc: `ffprobe` (độ dài, xoay), xuất lưới khung hình (`fps=0.5,scale=..,tile=`) để hiểu nội dung.
2. Viết kịch bản chữ theo cấu trúc bên dưới; sửa timeline trong `make_video.py` và SFX trong `make_audio.py` cho khớp.
3. Chạy `scripts/render.sh`.
4. **Luôn kiểm tra**: xuất vài khung (`select='eq(n\,N)+...',tile=`) xem chữ có đè nhau / tràn khung / mất dấu không; đo `ebur128`. Sửa rồi render lại.
5. Gửi file cho người dùng; nói rõ những phần chưa làm được và số liệu cần họ kiểm tra lại.

## Cấu trúc video (mặc định)
| Đoạn | Nội dung |
|---|---|
| **Hook** (~1,3s đầu) | Nền tối 62% + mờ nhẹ. Khung tiêu đề nhiều tầng: dòng chữ có chân màu vàng ánh kim (gradient #FFF4D6→#D6AA60), chữ viết tay trắng xen giữa ("giữa lòng"), chữ viết tay "Khám phá…", tên dự án cực to màu xanh ngọc phát sáng. Pop-in + tiếng impact. |
| **Các cảnh giữa** | Mỗi cảnh 1 ý: chữ khóa 3 tầng + phụ đề. Có thể thêm thẻ kính mờ chứa số liệu. |
| **CTA cuối** | "Inbox ngay để nhận / **BẢNG GIÁ** / *chi tiết*" → "**LƯU VIDEO**" + biểu tượng bookmark vàng, tiếng ding. Nền mờ dần ở cuối. |

## Cách viết chữ
- **Chữ khóa 3 tầng**: dòng trắng mảnh nhỏ ở trên (BVP-Light ~60px) → chữ khóa IN HOA to (Barlow-XB 190–230px, màu #64FFD2, glow #00C8A0) → chữ viết tay nhỏ lệch phải bên dưới (Dancing ~72px, trắng).
- Chữ khóa **lao vào từ trái có vệt nhòe + nghiêng** (smear), **lao ra bên phải** khi hết cảnh. Dòng phụ thì fade; khi biến mất thì mờ dần (blur-out).
- Chữ viết tay dùng làm **điểm nhấn cảm xúc** ("Trọn tầm", "dự án thực tế", "lờ mờ", "Dự án").
- Màu đỏ (#E81C24) chỉ dùng cho từ cần nhấn rất mạnh (kiểu "MỸ TỪ").
- **Phụ đề**: chữ nghiêng trắng (BVP-MedIt ~46px) ở ~81% chiều cao, hiện **từng từ** (0,12s/từ), từ quan trọng tô xanh ngọc. Phong cách cũ hơn: chữ trắng trên hộp tối bo góc.
- **Thẻ kính mờ**: bo góc, nghiêng -6°, làm mờ nền phía sau, viền xanh ngọc phát sáng; dòng đầu xanh ngọc đậm, các dòng sau trắng.
- Chữ khóa đặt ở ~55–60% chiều cao; dòng chữ mảnh dạng câu dài có thể đặt ở ~25%.
- Không dùng hộp nền màu cho chữ khóa. Luôn có bóng đổ mờ để đọc được trên nền sáng.

## Chuyển cảnh & chuyển động
- **Light leak cam vàng** (screen blend, lướt ngang, ~0,45s) — chuyển cảnh chính.
- **Ngả đỏ → chớp trắng** (~0,4s) — dùng 1 lần giữa video cho nhịp mạnh, kèm riser → impact.
- **Zoom giật** +9% rồi trả về trong 0,35s ngay sau mỗi chuyển cảnh; cả video zoom chậm +5% (Ken Burns).
- **Blur → nét** khi vào cảnh sau chớp trắng; **nét → blur** ở cuối video.

## Âm thanh
- Nhạc nền tự tạo (không dùng nhạc có bản quyền của video mẫu). Giữ tiếng gốc ở ~15%.
- SFX khớp chuyển động: impact (hook), whoosh (light leak & smear chữ), tick (từng từ phụ đề), pop (chữ pop/thẻ kính), shimmer (thẻ/tiêu đề), riser→impact (chớp trắng), ding (CTA).

## Lưu ý
- Không chép logo/watermark của kênh khác (vd. "Q." góc phải trên); dùng logo người dùng nếu họ gửi.
- Số liệu dự án (diện tích, số tòa…) lấy từ video mẫu → nhắc người dùng kiểm tra lại.
- Video gốc chỉ có 1 cảnh thì không làm được lật trang / chú thích từng tòa; đề nghị người dùng gửi thêm cảnh quay.

## Nhật ký học (thêm mục mới mỗi khi người dùng gửi video mẫu mới)
1. **Video mẫu 1** (talking head, sa bàn): chữ khóa xanh ngọc phát sáng, dòng trắng nhỏ đi kèm, chữ đỏ nhấn mạnh, chữ mảnh hiện từng từ, blur-out khi biến mất, light leak cam, chớp trắng, thẻ thông tin dự án, nhạc nền + nhiều SFX (pop, whoosh, riser).
2. **Video mẫu 2** (phòng thu, so sánh 2 dự án): mở bằng zoom chậm, chữ khóa lao vào/lao ra có vệt nhòe, cấu trúc 3 tầng, "#1 / #2" đánh số ý, khung ảnh nhỏ bo góc, CTA "LƯU VIDEO" + bookmark, chớp trắng in hình người cắt nền.
3. **Video mẫu 3** (trong xe + công trường): khung hook tiêu đề nhiều tầng ở frame đầu (vàng ánh kim + viết tay + tên dự án xanh ngọc), chữ viết tay điểm nhấn, phụ đề nghiêng tô màu từ khóa, nhãn "THÁP 1–4" trên từng tòa, thẻ kính nghiêng viền xanh ngọc, hiệu ứng lật trang, ngả đỏ trước chớp sáng.

**Chưa làm (cần thêm cảnh/giọng nói):** chớp trắng in hình người (cần tách nền), lật trang, nhãn chú thích từng tòa, khung ảnh nhỏ bo góc, phụ đề khớp giọng thuyết minh.
