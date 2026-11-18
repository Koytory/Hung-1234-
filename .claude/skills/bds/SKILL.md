---
name: bds
description: Phong cách quay + edit video bất động sản (BĐS) dạng TikTok/Reels dọc 9:16 mà người dùng đã chọn — chữ xanh ngọc phát sáng, chữ viết tay điểm nhấn, chữ nằm sau người, chuyển cảnh light leak / chớp trắng / lao tới nhòe tâm, nhạc nền + SFX tự tạo, kèm hướng dẫn cách quay. Dùng khi người dùng gửi video và nhờ "thêm text", "edit", "làm video BĐS", hỏi cách quay, hoặc gửi video mẫu để "học thêm" phong cách mới (khi đó cập nhật file này).
---

# Phong cách quay & edit video BĐS

Người dùng nói tiếng Việt → trả lời bằng tiếng Việt. Video đầu ra: MP4 dọc 1080x1920, 30fps, H.264 + AAC, âm lượng ~ -14/-15 LUFS, đỉnh ≤ -1 dBTP.

## Công cụ có sẵn trong skill này
- `scripts/setup.sh` — cài phụ thuộc (numpy, Pillow, mediapipe, libegl1/libgles2). Chạy 1 lần mỗi máy.
- `scripts/fxlib.py` — **thư viện hiệu ứng dùng chung** (`from fxlib import *`):
  - Chữ: `text_img`, `stack`, `El` (smear / pop / fade / blur), `Wipe`, `Drop`, `words` (phụ đề từng từ, tô màu từ khóa), `glass_card` + `Glass`, `bookmark_icon`, `lower_third` (thẻ tên + SĐT).
  - Hình: `push_zoom`, `make_leak` + `apply_leak`, `flash` (ngả đỏ → chớp trắng), `zoom_blur` (lao tới nhòe tâm), `grade_spring`, `grade_cinematic` (teal-orange), `VIGNETTE`, `make_petals` + `draw_petals`.
  - Tách người: `PersonMask` (MediaPipe, model ở `models/selfie_segmenter.tflite`), `Behind(el, pm)` = **chữ nằm sau người**, `silhouette_flash` = **chớp trắng in hình người**.
  - `run(frame_fx, elements, overlay)` — vòng lặp đọc/ghi frame rgb24 qua stdin/stdout.
- `scripts/template_tour.py` — **mẫu đầy đủ mới nhất** (video "Đi thăm phân khu Mùa Xuân", 38s, nhiều cảnh). Copy rồi sửa timeline.
- `scripts/make_video.py` + `make_audio.py` + `render.sh` — bản cũ cho video 1 cảnh ngắn (vẫn dùng được).
- `fonts/` — font đủ dấu tiếng Việt (OFL): `Barlow-XB` (chữ khóa), `Dancing` (viết tay), `Playfair-XB` (tiêu đề hook), `BVP-Light/Medium/MedIt/Black`.
- Mẫu âm thanh nhiều cảnh (nhạc build→drop, reverb, SFX): xem `eco2/full_audio.py` trong repo.

## Quy trình
1. Lấy video: file đính kèm (`/root/.claude/uploads/...`) hoặc Google Drive. Công cụ Drive chỉ tải được file **< 10MB**; file lớn cần người dùng mở "Bất kỳ ai có đường liên kết" rồi tải qua `drive.usercontent.google.com/download?id=...&export=download&confirm=t` (môi trường `Hung-1234-` đã mở host này). Sau khi tải, nhắc người dùng đổi lại "Bị hạn chế".
2. Xem video gốc: `ffprobe` (độ dài, xoay), lưới khung hình (`fps=N/dur,scale=..,tile=`), `volumedetect`/`silencedetect` để biết có giọng nói không.
3. Ghép nguồn 1080x1920@30 bằng ffmpeg (`concat`). Cần kéo dài → làm chậm 0,8–0,9x với `minterpolate=mi_mode=mci` (chậm: ~10 phút/10s 4K, chạy nền), giữ khung cuối bằng `tpad=stop_mode=clone`.
4. Viết kịch bản chữ theo cấu trúc bên dưới; copy `template_tour.py`, sửa timeline; viết audio cùng mốc thời gian.
5. Render: `ffmpeg ... -f rawvideo - | python3 script.py | ffmpeg ... -i mix.wav` rồi `loudnorm=I=-14:TP=-2,alimiter=limit=0.84`.
6. **Luôn kiểm tra**: xuất khung (`select='eq(n\,N)+...',tile=`) xem chữ đè nhau / tràn / mất dấu; đo `ebur128=peak=true`. Sửa rồi render lại.
7. Gửi file; nói rõ phần chưa làm được và số liệu cần kiểm tra lại.

## Cấu trúc video (mặc định)
| Đoạn | Nội dung |
|---|---|
| **Hook** (~2s đầu) | Frame đầu chớp trắng + zoom-in từ mờ sang nét. Khung tiêu đề nhiều tầng: dòng chữ có chân vàng ánh kim (gradient #FFF4D6→#D6AA60) rơi xuống nảy nhẹ, chữ viết tay trắng ("Khám phá", "cùng mình"), keyword cực to xanh ngọc wipe trái→phải có vệt sáng. Viền tối nhẹ. Impact + chuông lấp lánh. |
| **Các cảnh giữa** | Mỗi cảnh 1 ý (2–7s): chữ khóa 3 tầng + phụ đề. Có thể thêm thẻ kính mờ chứa thông tin. Keyword **nằm sau người** khi có người trong khung. |
| **CTA cuối** | "Inbox ngay để nhận / **BẢNG GIÁ** / *chi tiết*" → "**LƯU VIDEO**" + bookmark vàng, ding. Nền mờ dần. Nếu có tên/SĐT người dẫn → `lower_third`. |

## Cách viết chữ
- **Chữ khóa 3 tầng**: dòng trắng mảnh nhỏ ở trên (BVP-Light ~60px) → chữ khóa IN HOA to (Barlow-XB 190–250px, #64FFD2, glow #00C8A0) → chữ viết tay nhỏ lệch phải bên dưới (Dancing ~72px, trắng).
- Chữ khóa **lao vào từ trái có vệt nhòe + nghiêng** (smear), **lao ra bên phải**. Dòng phụ fade; biến mất thì blur-out.
- **Chữ nằm sau người** (video mẫu 4): keyword đặt ngang thân người, người che một phần chữ → cảm giác 3D. Dùng `Behind(El(...), PersonMask())`.
- Chữ viết tay = **điểm nhấn cảm xúc** ("Trọn tầm", "rợp bóng hoa giấy", "an yên mỗi ngày").
- Màu đỏ (#E81C24) chỉ cho từ cần nhấn rất mạnh.
- **Phụ đề**: chữ nghiêng trắng (BVP-MedIt ~46px) ở ~81% chiều cao, hiện **từng từ** (0,12s/từ), từ quan trọng tô xanh ngọc.
- **Kiểu tối giản** (video mẫu 4, dùng khi có người dẫn nói): chỉ 1–2 từ mỗi lúc, chữ thường trắng mảnh nhỏ + 1 từ khóa đậm rất to ("if you / **Love**", "fully / **remodeled**"), đặt giữa khung, không nền.
- **Thẻ kính mờ**: bo góc, nghiêng -6°, làm mờ nền phía sau, viền xanh ngọc phát sáng.
- Không dùng hộp nền màu cho chữ khóa. Luôn có bóng đổ mờ.
- Chỉ viết điều thấy được trong hình; không bịa số liệu, loại nhà, giá. Hỏi người dùng tên phân khu/dự án/loại nhà.

## Chuyển cảnh & chuyển động
- **Light leak** (cam vàng; mùa Xuân: hồng cam) lướt ngang ~0,45–0,5s — chuyển cảnh chính.
- **Ngả đỏ → chớp trắng** (~0,45s) — 1 lần giữa video, kèm riser → impact + crash, nhạc "drop" lần 2.
- **Lao tới nhòe tâm / speed ramp** (`zoom_blur`, video mẫu 4): 0,3s cuối cảnh trước nhòe tăng dần → cắt → 0,25s đầu cảnh sau nhòe giảm dần. Kèm whoosh.
- **Chớp trắng in hình người** (`silhouette_flash`, ~0,45s): cả khung trắng, chỉ còn người — dùng lúc người quay đầu/đổi hướng.
- **Zoom giật** +9% → về trong 0,35s sau mỗi cắt; mỗi shot zoom chậm +5% (Ken Burns).
- **Blur → nét** sau chớp trắng; **nét → blur** ở cuối.
- Màu: chủ đề mùa Xuân → `grade_spring` (ấm, +22% bão hòa) + hoa đào/mai rơi; video tour nhà điện ảnh → `grade_cinematic` (teal-orange, tương phản, vignette).

## Âm thanh
- Nhạc nền tự tạo (không dùng nhạc bản quyền). Giữ tiếng gốc ~15–25%.
- **Build → drop**: phần hook nhạc bị lọc thấp (low-pass 500→4000Hz) và không trống, đến cắt cảnh đầu tiên thì "drop" đủ trống + bass. Giữa video lặp lại 1 lần (lọc + tắt trống 1s trước chớp trắng → drop 2). Cuối: tắt trống, pad ngân, fade.
- SFX có **reverb** (IR nhiễu suy giảm 1,6s, FFT convolution) + **sidechain** hạ nhạc dưới impact: impact sub-boom (hook, drop), crash, whoosh (light leak, smear, zoom-blur), thud (tiêu đề rơi), chuông lấp lánh glissando (keyword wipe, thẻ kính), pop, tick theo từng từ phụ đề, riser → impact, ding (LƯU VIDEO).

## Hướng dẫn QUAY (tư vấn người dùng trước khi quay — học từ video mẫu 4)
**Thiết bị & cài đặt**
- Điện thoại quay **dọc 9:16**, **4K 30fps** (hoặc 1080p 30fps nếu cần file nhẹ để gửi). Khóa phơi sáng/lấy nét (giữ chạm màn hình). Ống **góc rộng 0.5x** cho nội thất & ngoại cảnh; **1x/2x + chế độ Chân dung/Cinematic** cho người dẫn (xóa phông).
- **Gimbal** (hoặc cầm 2 tay sát người, bước "gót-mũi" chậm) để máy trôi mượt. Quay giờ nắng đẹp (sáng sớm/chiều), trời xanh.
- Mỗi shot quay **5–10s**, dư đầu-đuôi 1s để cắt; đứng yên 1s trước khi di chuyển.

**Danh sách shot nên có (shot list)**
1. **Hook – người dẫn nói vào máy**: đứng giữa lối đi trước nhà, máy ngang ngực, xóa phông nhà phía sau, người dẫn bước chậm về phía máy (người quay lùi lại), tay mở ra giới thiệu. Câu đầu 1–2s phải gây tò mò ("Nếu bạn thích…", "Căn này…").
2. **Ngoại cảnh góc thấp**: hạ máy sát mặt đất/cỏ, góc rộng, đẩy chậm về phía nhà; lấy tán lá cây làm **tiền cảnh** che mép trên.
3. **Shot "lao tới"** (để làm chuyển cảnh nhòe tâm): đi/chạy nhanh về phía nhà 1–2s rồi dừng — hoặc lao qua bụi cây/cửa.
4. **Lia ngang dãy nhà** chậm, đều tay (như IMG_2419).
5. **Người đi trên lối đi**: quay sau lưng đi xa, rồi quay đầu đi về máy (dùng chớp trắng in hình người lúc quay đầu).
6. **Nội thất**: lướt máy thấp sát mặt bàn bếp/đảo bếp, đẩy qua khung cửa vào phòng, ngửa máy nhìn trần/đèn/quạt, chi tiết từ trên xuống (khay, lọ hoa), góc phòng ngủ/tắm rộng. Mỗi phòng 2–3 shot 2s.
7. **Cảnh cầm vật/giới thiệu**: người dẫn ngửa bàn tay như đang "nâng" ngôi nhà (về sau ghép thẻ giá/ảnh bay trên tay).
8. **Kết**: người dẫn trong bếp/phòng khách nói lời kêu gọi + **flycam** kéo lùi lên cao toàn khu (nếu có).
- **Nhịp dựng**: cắt theo nhịp nhạc, mỗi shot 1–3s ở đoạn giới thiệu nội thất (≈30 cắt/60s), shot người dẫn dài hơn.
- **Trang phục** người dẫn: đơn sắc (đen/trắng) nổi trên nền nhà.

## Lưu ý
- Không chép logo/watermark của kênh khác; dùng logo người dùng nếu họ gửi.
- Số liệu dự án lấy từ video mẫu → nhắc người dùng kiểm tra lại.
- Video không người dẫn/giọng nói → phụ đề do mình viết theo hình; đề nghị người dùng thu giọng để phụ đề khớp lời.

## Nhật ký học (thêm mục mới mỗi khi người dùng gửi video mẫu mới)
1. **Video mẫu 1** (talking head, sa bàn): chữ khóa xanh ngọc phát sáng, dòng trắng nhỏ đi kèm, chữ đỏ nhấn mạnh, chữ mảnh hiện từng từ, blur-out, light leak cam, chớp trắng, thẻ thông tin, nhạc nền + nhiều SFX.
2. **Video mẫu 2** (phòng thu, so sánh 2 dự án): zoom chậm, chữ khóa lao vào/ra có vệt nhòe, cấu trúc 3 tầng, "#1 / #2", khung ảnh nhỏ bo góc, CTA "LƯU VIDEO" + bookmark, chớp trắng in hình người.
3. **Video mẫu 3** (trong xe + công trường): hook tiêu đề nhiều tầng (vàng ánh kim + viết tay + tên dự án xanh ngọc), phụ đề nghiêng tô màu từ khóa, nhãn "THÁP 1–4", thẻ kính nghiêng, lật trang, ngả đỏ trước chớp sáng.
4. **Video mẫu 4** (tour nhà điện ảnh, người dẫn nữ): **cách quay** — người dẫn bước tới máy xóa phông, góc thấp siêu rộng ngoại cảnh, tiền cảnh lá cây, shot lao tới làm chuyển cảnh nhòe tâm/speed ramp, lướt máy sát mặt bàn bếp, đẩy qua cửa, ngửa nhìn trần, chi tiết từ trên xuống, flycam kết; cắt nhanh theo nhịp (~30 cắt/phút); màu teal-orange tương phản; chữ tối giản 1–2 từ, từ khóa to đậm **nằm sau người**; thẻ giá nổi trên lòng bàn tay; thẻ tên + SĐT ở cuối; nhạc beat liên tục dưới giọng nói.

**Đã làm được từ v3:** chữ nằm sau người, chớp trắng in hình người, chuyển cảnh lao tới nhòe tâm.
**Chưa làm:** lật trang, nhãn chú thích từng tòa (cần chọn điểm theo dõi), thẻ giá bám theo lòng bàn tay (cần theo dõi tay), phụ đề khớp giọng (cần file giọng nói).
