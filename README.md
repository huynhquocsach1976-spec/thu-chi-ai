# 💰 Thu Chi AI Pro

**Ứng dụng quản lý thu chi cá nhân thông minh**: nhập giao dịch bằng câu nói tự nhiên, quét hóa đơn bằng ảnh, đặt ngân sách theo tháng và xuất báo cáo Excel / PDF. Toàn bộ phần "hiểu" nội dung do AI (Google Gemini) đảm nhận.

![Python](https://img.shields.io/badge/Python-3.10-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-8E75B2?logo=googlegemini&logoColor=white)

---

## 📌 Mục lục

1. [Tính năng](#-tính-năng)
2. [Công nghệ sử dụng](#-công-nghệ-sử-dụng)
3. [Kiến trúc hệ thống](#-kiến-trúc-hệ-thống)
4. [Cấu trúc dự án](#-cấu-trúc-dự-án)
5. [Chạy thử trên máy](#-chạy-thử-trên-máy)
6. [Cấu hình (biến môi trường)](#-cấu-hình-biến-môi-trường)
7. [Triển khai lên cloud](#-triển-khai-lên-cloud)
8. [Tài liệu API](#-tài-liệu-api)
9. [Cơ sở dữ liệu](#-cơ-sở-dữ-liệu)
10. [Bảo mật](#-bảo-mật)
11. [Lưu ý khi vận hành](#-lưu-ý-khi-vận-hành)
12. [Hướng phát triển](#-hướng-phát-triển)

---

## ✨ Tính năng

### 🤖 Nhập giao dịch bằng AI
Gõ một câu tự nhiên, AI tự tách **số tiền, loại (Thu/Chi), danh mục và mô tả**.

| Bạn nhập | Kết quả |
|---|---|
| `ăn cơm 40k` | Chi · 40.000 đ · Ăn uống |
| `nhận lương 20 triệu` | Thu · 20.000.000 đ · Lương |
| `đổ xăng 2tr5` | Chi · 2.500.000 đ · Di chuyển |

Ngoài ra có thể **nhập thủ công** khi không muốn dùng AI.

### 📷 Quét hóa đơn
Tải ảnh hóa đơn (JPG, PNG, WEBP, tối đa 10 MB). AI đọc tổng tiền và tên cửa hàng rồi lưu thành giao dịch.

### 📊 Lịch sử & thống kê
- Lọc theo **tháng, loại, danh mục** và tìm theo mô tả
- Tổng thu, tổng chi, số dư, số giao dịch
- Biểu đồ chi tiêu theo danh mục và thu/chi theo tháng hoặc ngày
- **Sửa / xóa** giao dịch (có ô xác nhận trước khi xóa)
- Tải dữ liệu dạng **CSV**

### 🎯 Ngân sách theo tháng
- Đặt hạn mức cho từng danh mục hoặc cho **tổng chi tiêu**
- Thanh tiến độ, số tiền còn lại hoặc vượt
- **Cảnh báo tự động** ngay khi thêm khoản chi: 🟠 từ 80% ngân sách, 🔴 khi vượt

### 📑 Báo cáo tháng
Xuất báo cáo một tháng gồm tổng quan, chi tiêu theo danh mục, tình hình ngân sách và toàn bộ giao dịch:
- **Excel (.xlsx)**: 2 sheet, có biểu đồ, bộ lọc và định dạng màu
- **PDF**: tiếng Việt có dấu, trình bày sẵn để in hoặc gửi

### 🔐 Tài khoản & bảo mật
- Đăng ký, đăng nhập; dữ liệu của mỗi người được tách biệt hoàn toàn
- **Giữ đăng nhập** khi tải lại trang
- Báo **số lần nhập sai** và tạm khóa khi sai quá nhiều lần

---

## 🛠️ Công nghệ sử dụng

| Lớp | Công nghệ | Vai trò |
|---|---|---|
| Backend | **FastAPI**, Python 3.10 | Xây dựng REST API, tự sinh tài liệu `/docs` |
| Cơ sở dữ liệu | **PostgreSQL** + `psycopg2` | Lưu người dùng, giao dịch, ngân sách (có connection pool) |
| Kiểm tra dữ liệu | **Pydantic** | Xác thực dữ liệu đầu vào và schema đầu ra của AI |
| Xác thực | **PyJWT** | Token đăng nhập (JWT, HS256) |
| AI | **Google GenAI SDK** (`google-genai`), mô hình `gemini-2.5-flash` | Hiểu câu nhập và đọc ảnh hóa đơn |
| Báo cáo | **openpyxl**, **ReportLab**, font Roboto | Tạo file Excel và PDF tiếng Việt |
| Frontend | **Streamlit**, **Pandas**, **Requests** | Giao diện web, xử lý bảng, gọi API |
| Hosting | **Render** (Backend, Docker), **Streamlit Cloud** (Frontend), **Supabase** (PostgreSQL) | Triển khai trên cloud |

---

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────────┐   HTTPS + Bearer token   ┌──────────────────────┐
│  Streamlit (app.py) │ ───────────────────────► │   FastAPI (main.py)  │
│  Streamlit Cloud    │ ◄─────────────────────── │   Render (Docker)    │
└─────────────────────┘          JSON            └──────────┬───────────┘
                                                            │
                                  ┌─────────────────────────┼────────────────────────┐
                                  ▼                                                  ▼
                       ┌──────────────────────┐                          ┌──────────────────────┐
                       │ PostgreSQL (Supabase)│                          │ Google Gemini 2.5    │
                       │ users · transactions │                          │ Flash (google-genai) │
                       │ budgets              │                          └──────────────────────┘
                       └──────────────────────┘
```

**Luồng xử lý một giao dịch bằng AI**

1. Người dùng nhập `ăn cơm 40k` trên giao diện Streamlit.
2. Streamlit gọi `POST /add-transaction-ai` kèm token đăng nhập.
3. FastAPI xác thực token, gửi câu nhập cho Gemini và nhận về JSON đúng schema (số tiền, loại, danh mục, mô tả).
4. Backend kiểm tra lại dữ liệu, lưu vào PostgreSQL và tính cảnh báo ngân sách.
5. Kết quả trả về giao diện để hiển thị.

---

## 📁 Cấu trúc dự án

```
thu-chi-ai/
├── main.py            # Backend FastAPI: API, xác thực, AI, ngân sách, báo cáo
├── app.py             # Frontend Streamlit: giao diện người dùng
├── requirements.txt   # Thư viện Python (dùng chung backend và frontend)
├── Dockerfile         # Đóng gói backend để chạy trên Render
└── README.md          # Tài liệu này (cũng hiển thị trong mục "Giới thiệu" của app)
```

---

## 🚀 Chạy thử trên máy

### Yêu cầu
- Python **3.10** trở lên
- Một database PostgreSQL (cài sẵn trên máy hoặc dùng Supabase / Neon miễn phí)
- Khóa API Gemini, tạo miễn phí tại [Google AI Studio](https://aistudio.google.com/apikey)

### Các bước

```bash
# 1. Lấy mã nguồn
git clone https://github.com/huynhquocsach1976-spec/thu-chi-ai.git
cd thu-chi-ai

# 2. Tạo môi trường ảo và cài thư viện
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Khai báo biến môi trường cho backend (Windows dùng `set` thay cho `export`)
export DATABASE_URL="postgresql://user:matkhau@localhost:5432/thuchi"
export GEMINI_API_KEY="khoa-gemini-cua-ban"
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
export DB_SSLMODE="disable"      # chỉ khi database chạy trên máy; cloud thì giữ mặc định (require)

# 4. Chạy backend (http://localhost:8000, tài liệu API tại /docs)
uvicorn main:app --reload --port 8000

# 5. Mở terminal khác, chạy giao diện
export BACKEND_URL="http://localhost:8000"
streamlit run app.py
```

Các bảng dữ liệu được **tự tạo** khi backend khởi động lần đầu, không cần chạy SQL thủ công.

---

## ⚙️ Cấu hình (biến môi trường)

### Backend (`main.py`)

| Biến | Bắt buộc | Mặc định | Ý nghĩa |
|---|:---:|---|---|
| `DATABASE_URL` | ✅ | | Chuỗi kết nối PostgreSQL |
| `GEMINI_API_KEY` | ✅ | | Khóa API của Google Gemini |
| `SECRET_KEY` | ✅ | | Chuỗi bí mật dài, ngẫu nhiên, dùng ký token đăng nhập |
| `GEMINI_MODEL` | | `gemini-2.5-flash` | Mô hình AI sử dụng |
| `DB_SSLMODE` | | `require` | Chế độ SSL khi kết nối database |
| `DB_POOL_MAX` | | `10` | Số kết nối tối đa trong pool |
| `TOKEN_TTL_HOURS` | | `24` | Thời hạn một phiên đăng nhập (giờ) |
| `CORS_ORIGINS` | | `*` | Các domain được gọi API, ngăn cách bằng dấu phẩy. Nên đặt thành link app Streamlit |
| `APP_TIMEZONE` | | `Asia/Ho_Chi_Minh` | Múi giờ để tính "tháng" cho ngân sách và báo cáo |
| `BUDGET_WARN_PERCENT` | | `80` | Mức % ngân sách bắt đầu cảnh báo |
| `LOGIN_MAX_ATTEMPTS` | | `5` | Số lần đăng nhập sai tối đa |
| `LOGIN_WINDOW_SECONDS` | | `900` | Khoảng thời gian tính số lần sai (và thời gian khóa tạm) |

### Frontend (`app.py`)

Đặt trong biến môi trường hoặc trong **Secrets** của Streamlit Cloud.

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `BACKEND_URL` | `https://thu-chi-ai.onrender.com` | Địa chỉ backend |
| `APP_TIMEZONE` | `Asia/Ho_Chi_Minh` | Múi giờ hiển thị thời gian giao dịch |
| `REMEMBER_LOGIN` | `1` | Đặt `0` để tắt tính năng giữ đăng nhập khi tải lại trang |

---

## ☁️ Triển khai lên cloud

### 1. Database trên Supabase
1. Tạo project tại [supabase.com](https://supabase.com), chọn region **Singapore**.
2. Vào **Connect → Connection string → URI → Session pooler**.
3. Thay `[YOUR-PASSWORD]` bằng mật khẩu database và dùng làm `DATABASE_URL`.

> ⚠️ Render chỉ có IPv4, nên phải dùng **Session pooler** (host dạng `aws-0-...pooler.supabase.com`, tên người dùng dạng `postgres.<mã-project>`). Link "Direct connection" sẽ báo `Network is unreachable`.

### 2. Backend trên Render
1. Tạo **Web Service** từ repo GitHub, chọn môi trường **Docker**.
2. Trong tab **Environment**, thêm tối thiểu `DATABASE_URL`, `GEMINI_API_KEY`, `SECRET_KEY` (khuyến nghị thêm `CORS_ORIGINS`).
3. Deploy, rồi mở `https://<ten-service>.onrender.com/health`. Kết quả `"database":"connected"` là thành công.

### 3. Frontend trên Streamlit Cloud
1. Vào [share.streamlit.io](https://share.streamlit.io), tạo app từ cùng repo.
2. Chọn **Main file path** là `app.py`.
3. Trong **Settings → Secrets**, thêm:
   ```toml
   BACKEND_URL = "https://<ten-service>.onrender.com"
   ```

> Cập nhật code: chỉ cần `git push`. Render và Streamlit Cloud tự triển khai lại. Hãy chờ **backend deploy xong trước**, rồi mới tới frontend.

---

## 📡 Tài liệu API

Sau khi chạy backend, xem tài liệu tương tác tại `/docs` (Swagger). Các endpoint đánh dấu 🔒 cần header `Authorization: Bearer <token>`.

| Phương thức | Đường dẫn | Mô tả |
|---|---|---|
| GET | `/` , `/health` | Kiểm tra backend và kết nối database |
| POST | `/register` | Đăng ký, trả về token |
| POST | `/login` | Đăng nhập, trả về token (giới hạn số lần sai) |
| GET | `/me` 🔒 | Kiểm tra phiên và cấp token mới |
| POST | `/add-transaction-ai` 🔒 | Thêm giao dịch từ câu nhập tự nhiên |
| POST | `/scan-bill` 🔒 | Thêm giao dịch từ ảnh hóa đơn |
| POST | `/transactions` 🔒 | Thêm giao dịch thủ công |
| GET | `/transactions` 🔒 | Danh sách giao dịch (`limit`, `offset`) |
| PUT | `/transactions/{id}` 🔒 | Sửa giao dịch |
| DELETE | `/transactions/{id}` 🔒 | Xóa giao dịch |
| GET | `/budgets?month=YYYY-MM` 🔒 | Ngân sách kèm mức đã chi trong tháng |
| PUT | `/budgets` 🔒 | Tạo hoặc cập nhật ngân sách |
| DELETE | `/budgets/{id}` 🔒 | Xóa ngân sách |
| GET | `/reports/monthly?month=YYYY-MM&format=xlsx\|pdf` 🔒 | Xuất báo cáo tháng |

**Ví dụ**

```bash
# Đăng nhập
curl -X POST https://<backend>/login \
  -H "Content-Type: application/json" \
  -d '{"username":"ten_dang_nhap","password":"mat_khau"}'

# Thêm giao dịch bằng AI
curl -X POST https://<backend>/add-transaction-ai \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"text":"ăn cơm 40k"}'
```

---

## 🗄️ Cơ sở dữ liệu

| Bảng | Cột chính |
|---|---|
| `users` | `id`, `username` (không phân biệt hoa thường), `password_hash`, `created_at` |
| `transactions` | `id`, `user_id`, `transaction_type` (Thu / Chi), `amount`, `category`, `description`, `created_at` (UTC) |
| `budgets` | `id`, `user_id`, `category`, `monthly_limit` (mỗi người một ngân sách cho mỗi danh mục) |

Backend tự tạo bảng và tự nâng cấp cấu trúc cũ khi khởi động, nên dữ liệu hiện có được giữ nguyên.

---

## 🔒 Bảo mật

- **Mật khẩu** được băm bằng PBKDF2-SHA256 (200.000 vòng lặp, salt riêng). Tài khoản cũ dùng cách băm yếu hơn sẽ tự nâng cấp ở lần đăng nhập kế tiếp.
- **Xác thực bằng JWT**: danh tính luôn lấy từ token, không tin `user_id` do client gửi. Người dùng chỉ truy cập được dữ liệu của chính mình.
- **Chống dò mật khẩu**: giới hạn số lần sai theo từng cặp IP và tài khoản, có thông báo số lần còn lại. Thông báo lỗi giống nhau dù tài khoản có tồn tại hay không.
- **Kiểm tra đầu vào** bằng Pydantic; ảnh tải lên chỉ nhận JPG, PNG, WEBP và tối đa 10 MB.
- **Chống prompt injection** cơ bản: nội dung người dùng chỉ được coi là dữ liệu cần phân tích.
- Lỗi nội bộ được ghi log, không trả chi tiết kỹ thuật ra ngoài.
- Khóa API và mật khẩu chỉ lưu trong biến môi trường, **không đưa vào mã nguồn**.

---

## 📝 Lưu ý khi vận hành

- **Render gói Free** sẽ "ngủ" khi lâu không dùng, lần mở đầu có thể chờ 30 đến 60 giây.
- **Supabase gói Free** tạm dừng project sau khoảng một tuần không hoạt động; vào dashboard bấm **Restore** nếu app báo lỗi database.
- **Giữ đăng nhập khi tải lại trang** hoạt động bằng cách lưu token trong đường link (`?s=...`). Vì vậy **đừng chia sẻ link trang khi đang đăng nhập**. Có thể tắt bằng `REMEMBER_LOGIN=0`.
- Bộ đếm đăng nhập sai nằm trong bộ nhớ, nên được đặt lại khi backend khởi động lại.
- Nếu đổi `SECRET_KEY`, mọi người dùng sẽ phải đăng nhập lại (dữ liệu không bị mất).

---

## 🧭 Hướng phát triển

- Lưu phiên đăng nhập bằng cookie bảo mật thay cho đường link
- Giao dịch định kỳ (tiền nhà, hóa đơn hằng tháng) và mục tiêu tiết kiệm
- Nhập giao dịch bằng giọng nói
- Thêm kiểm thử tự động (pytest) và cấu hình CI
- Quản lý thay đổi cấu trúc database bằng Alembic

---

## 👤 Tác giả

Phát triển bởi **huynhquocsach1976-spec** · [GitHub](https://github.com/huynhquocsach1976-spec/thu-chi-ai)

Nếu thấy dự án hữu ích, hãy tặng một ⭐ cho repo nhé!
