# slimai-edit-video

Agent skill cho Claude Code: dựng video nói chuyện, phỏng vấn, podcast thành bản dọc 9:16 cho TikTok và bản ngang HD cho YouTube, toàn bộ bằng code.

Trước khi dựng, Claude gửi một ảnh lấy từ chính video của bạn với 4 kiểu màu và hỏi bạn chọn: màu gốc iPhone (mặc định), màu phim ấm, màu phim tương phản hoặc màu trung tính. Video có phụ đề theo từng từ, chữ đứng sau người nói, sơ đồ motion graphic, thu nhỏ người nói vào khung khi cần chỗ trình bày, nhạc và hiệu ứng âm thanh tự viết bằng code. Skill cũng xuất thumbnail, phụ đề SRT và danh sách chương cho YouTube.

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
| `scripts/` | Toàn bộ code: màu phim, dựng hình, âm thanh, kiểm tra |
| `references/` | Cẩm nang thiết kế, màu và độ nét, thông số nền tảng, các lỗi đã gặp |
| `examples/` | Hai dự án thật: clip 40 giây và video 2 phút. Không kèm video nguồn |
| `assets/` | Font và model tách người |

## Bên thứ ba

Font và model tách người có giấy phép riêng, xem [assets/README.txt](assets/README.txt). Cần kiểm tra các giấy phép này trước khi chia sẻ repo ra ngoài.
