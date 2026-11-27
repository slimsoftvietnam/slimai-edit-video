# slimai-edit-video

Agent skill cho Claude Code: dựng video nói chuyện, phỏng vấn, podcast thành bản dọc 9:16 cho TikTok và bản ngang HD cho YouTube, toàn bộ bằng code.

Trước khi dựng, Claude gửi hai ảnh lấy từ chính video của bạn rồi hỏi bạn chọn:

- **Phong cách dựng:** một trong bốn kiểu.
  - **Tiêu chuẩn** (mặc định): nhịp nhanh, chữ đứng sau người nói, sơ đồ; ra cả bản dọc và bản ngang.
  - **Trailer phim**: màn đen chèn chữ, trống dồn, twist và một câu kêu gọi follow hài hước ở cuối; 45-90 giây, cho TikTok.
  - **Vlog chill (khớp nhạc)**: nhịp chậm kiểu vlog du lịch, giữ gần hết câu chuyện, mọi nhát cắt và chữ hiện đúng phách nhạc lo-fi do code viết, thẻ chương trên cảnh hậu trường; bản ngang YouTube.
  - **Motion viral (TikTok)**: 2 giây đầu nói rõ chủ đề với người tách nền như sticker trên nền tia sáng và tiêu đề 3D, một hình ảnh chạy xuyên suốt video (như con trỏ chuột tự bấm), chữ khoét lỗ bay xuyên qua, phụ đề màu xếp tầng, lời kêu gọi đặt ngay sau ý mạnh nhất; 60-95 giây.
- **Màu:** màu gốc iPhone (mặc định), màu phim ấm, màu phim tương phản hoặc màu trung tính. Màu gốc iPhone giữ hình như file quay: không khử nhiễu, không làm nét thêm, vùng nắng vẫn giữ chi tiết.

Video có phụ đề theo từng từ, chữ đứng sau người nói, sơ đồ motion graphic, thu nhỏ người nói vào khung khi cần chỗ trình bày, nhạc và hiệu ứng âm thanh tự viết bằng code. Video hai người có thể chia đôi khung dọc, nam trên nữ dưới, ở những câu hỏi hay phản ứng cần thấy cả hai gương mặt. Skill cũng xuất thumbnail, phụ đề SRT, danh sách chương và bộ nội dung đăng YouTube: ba tiêu đề để YouTube thử xem tiêu đề nào giữ người xem lâu hơn, mô tả, thẻ và bình luận ghim. Từ khóa lấy từ gợi ý tìm kiếm của chính YouTube.

## Cài đặt

Cần Python 3.12 và ffmpeg có `libx264`, `zscale`, `lut3d` trong PATH.

```bash
git clone https://github.com/slimsoftvietnam/slimai-edit-video.git ~/.claude/skills/slimai-edit-video
cd ~/.claude/skills/slimai-edit-video
pip install -r requirements.txt
python scripts/doctor.py
```

Lần nhận dạng lời nói đầu tiên, Whisper tải model khoảng 1,5 GB.

## Cách dùng

Nói với Claude Code, kèm đường dẫn video:

```text
Edit video này thành bản TikTok và YouTube: D:\Videos\phong-van.mov
```

Hoặc gõ `/slimai-edit-video`. Claude nghe toàn bộ lời thoại, chọn câu chuyện, viết thiết kế cho video, soát ảnh tĩnh, rồi render và tự kiểm tra kết quả.

Mỗi video là một tập, có thư mục kết quả riêng trong `output/`.

- **Số tập** lấy từ số đầu tên file gốc: `01_Phong_van.mov` là tập 01, kết quả nằm trong `output/01_Phong_van/`. File gốc chưa có số thì Claude hỏi.
- **Ngoài cùng thư mục tập** là bản mới nhất để đăng, ví dụ `01_Phong_van_TikTok_v2.mp4`, kèm bản xem trên điện thoại, ảnh bìa, phụ đề và nội dung đăng YouTube.
- **Bản cũ** tự chuyển vào `ban_cu/`. Ảnh so sánh nằm trong `so_sanh/`.

Trên laptop i5, video 2 phút từ nguồn 6 phút cần khoảng 1 giờ máy chạy. Quy trình chi tiết nằm trong [SKILL.md](SKILL.md).

## Nguồn video

Đã chạy thử với nguồn ngang và dọc, 1080p và 4K, HLG và SDR, một người và hai người.

- Camera phải đứng yên.
- Chưa hỗ trợ video quay log.
- HDR dạng PQ đã có code nhưng chưa chạy thử trên clip thật.
- Nguồn quay dọc chỉ nên xuất bản dọc, vì bản ngang sẽ bị cắt sát mặt.

## Cấu trúc

| Thư mục | Nội dung |
|---|---|
| `SKILL.md` | Quy trình Claude làm theo |
| `scripts/` | Toàn bộ code: màu phim, dựng hình, kiểu trailer, kiểu vlog cắt theo phách nhạc, hiệu ứng motion và phụ đề màu, âm thanh, ảnh minh họa phong cách và màu, kiểm tra, từ khóa YouTube |
| `references/` | Cẩm nang thiết kế, cách dựng trailer, vlog và motion viral, màu và độ nét, thông số nền tảng và cách soạn nội dung đăng YouTube, các lỗi đã gặp |
| `examples/` | Bảy dự án thật (clip 40 giây, video 2 phút, ba trailer 55, 88 và 89 giây, bản vlog YouTube 4 phút 44 và bản motion TikTok 89 giây của cùng một tập), kèm bộ nội dung đăng YouTube mẫu. Không kèm video nguồn và nhạc có bản quyền |
| `assets/` | Font và model tách người |
| `tests/regress.py` | Kiểm tra trước và sau khi sửa code: chạy lại bản sao của một project, so từng khung hình và từng file tiếng |

Các bước và file chính trong `scripts/`:

| Bước | File |
|---|---|
| Nhận video, nghe lời thoại | `init_project.py`, `transcribe.py`, `find_faces.py`, `speaker_hints.py` |
| Hỏi phong cách và màu | `style_preview.py`, `look_preview.py` |
| Cắt | `select.json` → `build_timeline.py`; kiểu vlog: `vlog_cut.json` → `beat_fit.py`, `clamp_words.py` |
| Master và tách người | `build_master.py` (màu, `film_look.py`), `matte.py` |
| Thiết kế (`design.py` của project) | `story.py` và `engine.py`, `gfx.py`; kiểu trailer: `trailer.py`; vlog: `vlog.py`; motion: `fx.py`, `rawstyle.py`, `rawgroups.py`; giao diện máy tính: `ui.py` |
| Âm thanh | `audio_mix.py` (preset `standard`, `score`, `score_solo`, `vlog`) gọi `compose.py`, `vlog_music.py`, `trailer_score.py`, `modern_score.py`, `track_music.py`, `modern_sfx.py`, `audio_engine.py`; nhạc có bản quyền: `music_analyse.py` |
| Render, soát | `render.py`, `review.py` |
| Giao | `episode.py`, `finish.py`, `export_captions.py`, `thumbnail.py`, `youtube_meta.py` |

## Kiểm tra khi sửa skill

Trước khi sửa code, tạo bản sao của một vài project đã giao và chụp mốc; sửa xong chụp lại và so. Hình và tiếng phải giống hệt từng bit, trừ chỗ cố ý thay đổi.

```bash
python tests/regress.py clone projects/tap16 projects/_regress/tap16      # master, matte, tiếng gốc: hardlink
python tests/regress.py snapshot projects/_regress/tap16 snap/truoc       # theo regress.json trong bản sao
python tests/regress.py snapshot projects/_regress/tap16 snap/sau
python tests/regress.py compare snap/truoc snap/sau
```

`regress.json` của bản sao liệt kê các lệnh cần chạy (dựng timeline, trộn tiếng...), các thời điểm lấy khung hình và các file cần so. Xem đầu file `tests/regress.py`.

## Bên thứ ba

Font và model tách người có giấy phép riêng, xem [assets/README.txt](assets/README.txt). Cần kiểm tra các giấy phép này trước khi chia sẻ repo ra ngoài.
