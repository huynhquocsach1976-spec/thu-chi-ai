# 💰 Thu Chi AI Pro

Ứng dụng quản lý tài chính cá nhân thông minh tích hợp trí tuệ nhân tạo (**Google Gemini AI**), giúp bạn tự động phân tích giao dịch bằng ngôn ngữ tự nhiên, quét hóa đơn từ ảnh, thống kê chi tiêu trực quan theo danh mục và quản lý lịch sử thu chi dễ dàng.

---

## 🚀 Các tính năng nổi bật

- **🔐 Xác thực bảo mật:** Đăng nhập và đăng ký tài khoản với thuật toán mã hóa mật khẩu an toàn (`PBKDF2`).
- **🤖 Nhập giao dịch bằng AI:** Nhập câu lệnh tự nhiên (ví dụ: *"ăn cơm 40k"*, *"nhận lương 20 triệu"*, *"đổ xăng 2tr5"*), AI sẽ tự động bóc tách số tiền, phân loại danh mục và lưu trữ.
- **📷 Quét hóa đơn tự động:** Tải lên ảnh hóa đơn (JPG, PNG, WEBP), AI sẽ đọc và tự động điền thông tin thanh toán.
- **📊 Thống kê & Biểu đồ:** Xem tổng thu, tổng chi, số dư và biểu đồ cột trực quan chi tiêu theo từng danh mục.
- **📅 Lọc dữ liệu theo kỳ:** Dễ dàng lọc lịch sử giao dịch theo tháng/năm.
- **✏️ Quản lý linh hoạt:** Hỗ trợ tính năng Sửa hoặc Xóa trực tiếp từng giao dịch trong lịch sử.

---

## 🛠️ Công nghệ sử dụng

- **Backend:** FastAPI, Python, PostgreSQL (`psycopg2`), Pydantic, Uvicorn.
- **AI Engine:** Google GenAI SDK (`google-genai`, model `gemini-2.5-flash`).
- **Frontend:** Streamlit, Pandas, Requests.
- **Deployment:** Render (Backend), Streamlit Cloud (Frontend).

---

## ⚙️ Hướng dẫn cài đặt chạy thử (Local)

### 1. Clone repository về máy
```bash
git clone [https://github.com/TÊN_GITHUB_CỦA_BẠN/thu-chi-ai.git](https://github.com/TÊN_GITHUB_CỦA_BẠN/thu-chi-ai.git)
cd thu-chi-ai
2. Cấu hình và chạy Backend (FastAPI)
Cài đặt các thư viện cần thiết:

Bash
pip install fastapi uvicorn psycopg2-binary pydantic google-genai requests pandas streamlit
Thiết lập biến môi trường (tạo file .env hoặc cấu hình trực tiếp):

Đoạn mã
DATABASE_URL=postgresql://user:password@host:port/dbname
GEMINI_API_KEY=your_google_gemini_api_key
Chạy server backend:

Bash
uvicorn main:app --reload --port 8000
3. Cấu hình và chạy Frontend (Streamlit)
Mở một terminal mới và trỏ đến thư mục dự án.

Thiết lập biến môi trường trỏ tới backend (nếu chạy local):

Bash
# Trên Windows PowerShell
$env:BACKEND_URL="http://localhost:8000"

# Trên Mac/Linux
export BACKEND_URL="http://localhost:8000"
Chạy ứng dụng Streamlit:

Bash
streamlit run app.py
☁️ Hướng dẫn Deploy lên Cloud
Backend (Render): Tạo một Web Service trên Render, kết nối với kho lưu trữ GitHub, cài đặt Start Command là uvicorn main:app --host 0.0.0.0 --port $PORT, và thêm các biến môi trường (DATABASE_URL, GEMINI_API_KEY).

Frontend (Streamlit Cloud): Tạo ứng dụng mới trên Streamlit Cloud, trỏ tới file app.py, sau đó cấu hình biến môi trường BACKEND_URL trỏ tới URL dịch vụ Render của bạn.

👨‍💻 Tác giả
Phát triển bởi Nhóm 1 ( Huỳnh Quốc Sách, Trương Thị Hồng Đào, Đặng Hồng Sơn, Đổng Duy Khang).
