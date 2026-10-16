# 💰 Thu Chi AI Pro Backend

Backend API cho ứng dụng **Thu Chi AI Pro**, được xây dựng bằng **FastAPI + PostgreSQL + Google Gemini AI**.

Backend hỗ trợ quản lý tài khoản, ghi nhận thu chi bằng câu nhập tự nhiên, quét hóa đơn bằng AI và lưu lịch sử giao dịch.

---

## 🚀 Công nghệ sử dụng

- **Python 3.10+**
- **FastAPI**
- **PostgreSQL**
- **psycopg2**
- **Pydantic**
- **Google Gemini AI**
- **Uvicorn**
- **Base64**
- **SHA-256**

---

## 📁 Cấu trúc project

```text
ThuChiAI/
│
├── main.py
├── requirements.txt
├── README.md
└── .gitignore
```

> Nếu file Python của anh có tên khác `main.py` thì thay `main` bằng tên file tương ứng khi chạy.

---

# ⚙️ 1. Cài đặt

Cài các thư viện cần thiết:

```bash
pip install fastapi uvicorn psycopg2-binary pydantic google-generativeai
```

Hoặc sử dụng `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

# 📦 2. requirements.txt

Tạo file `requirements.txt`:

```txt
fastapi
uvicorn
psycopg2-binary
pydantic
google-generativeai
```

---

# 🔐 3. Environment Variables

Backend cần 2 biến môi trường:

```text
DATABASE_URL
GEMINI_API_KEY
```

## DATABASE_URL

Ví dụ:

```text
postgresql://username:password@host:5432/database
```

Nếu sử dụng **Supabase PostgreSQL**, lấy Connection String của database và cấu hình vào:

```text
DATABASE_URL
```

Backend đã hỗ trợ tự chuyển:

```text
postgres://
```

sang:

```text
postgresql://
```

---

## GEMINI_API_KEY

Cấu hình API Key của Google Gemini:

```text
GEMINI_API_KEY=your_api_key
```

**Không ghi API Key trực tiếp vào source code.**

Không đưa các thông tin sau lên GitHub:

```text
DATABASE_URL
GEMINI_API_KEY
password
secret key
```

---

# ▶️ 4. Chạy Backend

Nếu file chính là:

```text
main.py
```

chạy:

```bash
uvicorn main:app --reload
```

Backend sẽ chạy tại:

```text
http://127.0.0.1:8000
```

Nếu muốn cho thiết bị khác trong mạng truy cập:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

# 🧪 5. Kiểm tra Backend

Mở trình duyệt:

```text
http://127.0.0.1:8000/
```

Kết quả:

```json
{
  "status": "ok",
  "message": "Backend Thu Chi AI Pro đang hoạt động"
}
```

---

# 📚 6. Swagger API

FastAPI tự động tạo giao diện kiểm tra API.

Mở:

```text
http://127.0.0.1:8000/docs
```

Tại đây có thể kiểm tra trực tiếp tất cả API:

```text
GET  /
POST /register
POST /login
POST /add-transaction-ai
POST /scan-bill
GET  /transactions/{user_id}
```

---

# 🗄️ 7. Database

Khi Backend khởi động, hệ thống tự tạo các bảng nếu chưa tồn tại.

## Bảng `users`

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Bảng `transactions`

```sql
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    type VARCHAR(50) NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    category VARCHAR(100),
    note TEXT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

# 👤 8. API Đăng ký

## POST `/register`

Request:

```json
{
  "username": "nguyenquoc",
  "password": "123456"
}
```

Response:

```json
{
  "status": "success",
  "user_id": 1,
  "username": "nguyenquoc"
}
```

---

# 🔑 9. API Đăng nhập

## POST `/login`

Request:

```json
{
  "username": "nguyenquoc",
  "password": "123456"
}
```

Response:

```json
{
  "status": "success",
  "user_id": 1,
  "username": "nguyenquoc"
}
```

Nếu đăng nhập sai:

```json
{
  "detail": "Sai thông tin đăng nhập!"
}
```

---

# 💸 10. Thêm giao dịch bằng AI

## POST `/add-transaction-ai`

Cho phép người dùng nhập câu tự nhiên.

Ví dụ:

```text
Ăn cơm 50k
```

```text
Mua xăng 100 nghìn
```

```text
Nhận lương 15 triệu
```

Request:

```json
{
  "user_id": 1,
  "text": "Ăn cơm 50k"
}
```

Backend sẽ tự nhận diện:

- Số tiền
- Thu hoặc chi
- Danh mục
- Nội dung giao dịch

Response:

```json
{
  "status": "success",
  "message": "Đã ghi nhận: Ăn cơm 50k",
  "data": {
    "id": 1,
    "type": "chi",
    "amount": 50000,
    "category": "Ăn uống",
    "note": "Ăn cơm 50k"
  }
}
```

---

## 💰 Các đơn vị tiền được hỗ trợ

Ví dụ:

```text
50k
50 nghìn
50 ngan
1m
1 triệu
1tr
1 triệu đồng
```

Backend tự chuyển đổi về VND.

Ví dụ:

```text
50k → 50.000
1 triệu → 1.000.000
15 triệu → 15.000.000
```

---

# 🧾 11. Quét hóa đơn bằng Gemini AI

## POST `/scan-bill`

API nhận hình ảnh hóa đơn được mã hóa bằng Base64.

Request:

```json
{
  "user_id": 1,
  "image_base64": "BASE64_IMAGE_DATA"
}
```

Gemini AI phân tích hình ảnh và lấy thông tin:

```json
{
  "amount": 150000,
  "category": "Ăn uống",
  "note": "Tên cửa hàng"
}
```

Sau đó Backend tự động lưu giao dịch vào PostgreSQL.

Response:

```json
{
  "status": "success",
  "data": {
    "id": 2,
    "amount": 150000,
    "category": "Ăn uống",
    "note": "Tên cửa hàng"
  }
}
```

---

# 📂 12. Danh mục giao dịch

Backend hiện hỗ trợ các danh mục chính:

```text
Ăn uống
Di chuyển
Hóa đơn
Mua sắm
Khác
```

---

# 📜 13. Xem lịch sử giao dịch

## GET `/transactions/{user_id}`

Ví dụ:

```text
GET /transactions/1
```

Response:

```json
{
  "status": "success",
  "data": [
    {
      "id": 2,
      "type": "chi",
      "amount": 150000,
      "category": "Ăn uống",
      "note": "Quán ăn",
      "date": "2026-10-16T10:00:00"
    },
    {
      "id": 1,
      "type": "thu",
      "amount": 15000000,
      "category": "Khác",
      "note": "Nhận lương 15 triệu",
      "date": "2026-10-16T09:00:00"
    }
  ]
}
```

---

# 🔄 14. Luồng hoạt động

```text
┌─────────────────────┐
│      Frontend       │
│  Web / Mobile App   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│       FastAPI       │
│       Backend       │
└───────┬─────┬───────┘
        │     │
        │     └────────────────┐
        ▼                      ▼
┌───────────────┐       ┌───────────────┐
│  PostgreSQL   │       │  Gemini AI    │
│   Database    │       │  Scan Bill    │
└───────────────┘       └───────────────┘
```

---

# 🔐 15. Bảo mật

Hiện tại mật khẩu được mã hóa bằng:

```python
hashlib.sha256()
```

Đây là cách đơn giản phù hợp cho phiên bản thử nghiệm.

Khi triển khai production nên nâng cấp:

- Argon2 hoặc bcrypt
- JWT Authentication
- HTTPS
- CORS
- Rate Limiting
- Validate dữ liệu đầu vào
- Quản lý Secret bằng Environment Variables

---

# ⚠️ 16. Lưu ý về `user_id`

Hiện tại API nhận:

```json
{
  "user_id": 1
}
```

trực tiếp từ Frontend.

Đây **chưa phải cơ chế xác thực an toàn cho production**.

Phiên bản tiếp theo nên sử dụng:

```text
Đăng nhập
    ↓
JWT Token
    ↓
Authorization Header
    ↓
FastAPI kiểm tra Token
    ↓
Xác định user_id
    ↓
Truy cập dữ liệu
```

Thay vì để Frontend tự gửi `user_id`.

---

# 🧪 17. Quy trình test

Sau khi chạy Backend:

```bash
uvicorn main:app --reload
```

Mở:

```text
http://127.0.0.1:8000/docs
```

Test theo thứ tự:

```text
1. GET /
       ↓
2. POST /register
       ↓
3. POST /login
       ↓
4. POST /add-transaction-ai
       ↓
5. GET /transactions/{user_id}
       ↓
6. POST /scan-bill
```

---

# 🛠️ 18. Xử lý lỗi thường gặp

## Lỗi chưa cấu hình DATABASE_URL

```text
Chưa cấu hình DATABASE_URL trong Environment Variable!
```

Kiểm tra Environment Variable:

```text
DATABASE_URL
```

---

## Lỗi kết nối PostgreSQL

```text
Lỗi kết nối Postgres DB
```

Kiểm tra:

- DATABASE_URL
- Username
- Password
- Host
- Port
- Database
- PostgreSQL/Supabase đang hoạt động

---

## Lỗi Gemini API

```text
Chưa cấu hình GEMINI_API_KEY!
```

Kiểm tra:

```text
GEMINI_API_KEY
```

---

# 📌 19. API Summary

| Method | Endpoint | Chức năng |
|---|---|---|
| GET | `/` | Kiểm tra Backend |
| POST | `/register` | Đăng ký |
| POST | `/login` | Đăng nhập |
| POST | `/add-transaction-ai` | Thêm thu/chi |
| POST | `/scan-bill` | Quét hóa đơn AI |
| GET | `/transactions/{user_id}` | Lịch sử giao dịch |

---

# 📈 20. Hướng phát triển

Các chức năng có thể phát triển tiếp:

- [ ] JWT Authentication
- [ ] Refresh Token
- [ ] Quản lý người dùng
- [ ] Sửa giao dịch
- [ ] Xóa giao dịch
- [ ] Tìm kiếm giao dịch
- [ ] Lọc theo ngày/tháng
- [ ] Báo cáo thu chi
- [ ] Biểu đồ thống kê
- [ ] Ngân sách hàng tháng
- [ ] Cảnh báo chi tiêu
- [ ] AI phân tích thói quen chi tiêu
- [ ] AI tư vấn tiết kiệm
- [ ] OCR hóa đơn nâng cao
- [ ] Nhận diện QR
- [ ] Xuất Excel/PDF
- [ ] Deploy lên Cloud

---

# 📦 21. Version

```text
Project: Thu Chi AI Pro
Version: 1.0.0

Backend:
FastAPI

Database:
PostgreSQL

AI:
Google Gemini

Language:
Python
```

---

# 👨‍💻 22. Tác giả

**Thu Chi AI Pro**

Ứng dụng quản lý thu chi cá nhân tích hợp trí tuệ nhân tạo.
