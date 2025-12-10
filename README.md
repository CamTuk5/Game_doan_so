# 🎲 Game Đoán Số Nhiều Người Chơi(Python, Socket, Threading)
Danh sách thành viên:
  - Đặng Thị Diễm My
  - Nguyễn Hồ Cẩm Tú
  - Nguyễn Đỗ Bảo Ngọc

1 Mô tả:
Là một trò chơi "đoán số nhiều người chơi" chạy trên mô hình "Client–Server":
- "Server" nghĩ ra một số bí mật trong khoảng `[MIN_VALUE, MAX_VALUE]` (mặc định `[1, 100]`).
- "Nhiều Client" có thể kết nối đến server cùng lúc.
- Mỗi người chơi:
  - Nhập "tên (username)" khi vào game.
  - Nhập "số dự đoán" gửi lên server.
- Server phản hồi:
  - `LỚN HƠN` nếu số bí mật > số đoán
  - `NHỎ HƠN` nếu số bí mật < số đoán
  - `ĐÚNG` nếu người chơi đoán chính xác
- Khi có người đoán đúng:
  - Server "thông báo cho tất cả người chơi" ai là người thắng.
  - Tự động "bắt đầu ván mới" với số bí mật mới.

> Mục tiêu: luyện tập lập trình mạng với "Python", sử dụng "socket" và "threading" để xử lý nhiều client đồng thời và quản lý trạng thái game trên server.
2 Công nghệ sử dụng
- Ngôn ngữ: Python 3
- Thư viện chuẩn:
  - `socket` – lập trình TCP socket.
  - `threading` – tạo thread cho từng client.
  - `random` – sinh số bí mật ngẫu nhiên.
  - `tkinter` – dùng cho client giao diện (`client_gui.py`).

Cấu trúc thư mục
Ví dụ cấu trúc:
```text
Game_doan_so/
├─ server.py        # Server game đoán số
└─ client_gui.py    # (tuỳ chọn) Client giao diện dùng tkinter
3 Cài đặt và chạy dự án
tải code: git clone https://github.com/CamTuk5/Game_doan_so.git
chạy sever trên terminal vscode: python server.py
chạy client trên terminal vscode: python client_gui.py
nhập tên,nhập ip,nhập port,kết nối
