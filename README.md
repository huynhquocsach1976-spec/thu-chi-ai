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
