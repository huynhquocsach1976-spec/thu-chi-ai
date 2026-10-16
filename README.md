# 💰 Thu Chi AI Pro

Ứng dụng quản lý tài chính cá nhân thông minh tích hợp trí tuệ nhân tạo (**Google Gemini AI**). Giúp bạn tự động hóa quy trình ghi chép thu chi bằng ngôn ngữ tự nhiên, quét hóa đơn từ ảnh và theo dõi tài chính trực quan.

🔗 **Link trải nghiệm trực tiếp:** [https://thu-chi-ai.streamlit.app](ĐIỀN_LINK_STREAMLIT_CỦA_BẠN_VÀO_ĐÂY)

---

## ✨ Các tính năng nổi bật

- **🔐 Bảo mật tài khoản:** Đăng nhập an toàn với thuật toán mã hóa mật khẩu chuẩn quốc tế (`PBKDF2`).
- **🤖 Nhập liệu thông minh bằng AI:** Chỉ cần gõ văn bản tiếng Việt tự nhiên, AI sẽ tự bóc tách số tiền, phân loại và lưu trữ.
- **📷 Quét hóa đơn tự động (OCR):** Tải lên ảnh chụp hóa đơn, hệ thống sẽ tự động đọc tổng tiền và tên cửa hàng.
- **📊 Biểu đồ thống kê trực quan:** Theo dõi dòng tiền Thu – Chi và tỷ lệ phân bổ chi tiêu theo danh mục qua biểu đồ cột sinh động.
- **📅 Bộ lọc theo kỳ:** Dễ dàng tra cứu lại lịch sử tài chính theo từng tháng/năm cụ thể.
- **✏️ Tùy chỉnh linh hoạt:** Hỗ trợ tính năng Sửa hoặc Xóa nhanh chóng trực tiếp trên từng giao dịch.

---

## 🚀 Hướng dẫn sử dụng nhanh (Quick Guide)

1. **Đăng ký tài khoản:** Chuyển sang tab **Đăng ký**, tạo tên đăng nhập và mật khẩu riêng cho bạn.
2. **Nhập giao dịch:** 
   - Vào tab **Nhập giao dịch AI** và gõ ví dụ: `ăn sáng 35k`, `nhận lương 15 triệu`, `đổ xăng 100k`.
   - Hoặc vào tab **Quét hóa đơn** để tải ảnh hóa đơn thanh toán lên.
3. **Xem báo cáo:** Chuyển sang tab **Lịch sử & Thống kê** để xem tổng số dư, biểu đồ chi tiêu và quản lý lại các giao dịch cũ.

---

## 💡 Ví dụ câu lệnh AI hỗ trợ
Bạn có thể nhập bất kỳ câu giao dịch nào bằng tiếng Việt, ví dụ:
- *"Ăn trưa cơm tấm 50k"* ➔ Tự động lưu loại **Chi**, danh mục **Ăn uống**, số tiền **50,000 đ**.
- *"Nhận tiền bán laptop 8 triệu 5"* ➔ Tự động lưu loại **Thu**, danh mục **Khác**, số tiền **8,500,000 đ**.
- *"Tiền điện tháng này 450k"* ➔ Tự động lưu loại **Chi**, danh mục **Hóa đơn/Tiện ích**, số tiền **450,000 đ**.

---

## 🛠️ Công nghệ sử dụng
- **Backend:** FastAPI, Python, PostgreSQL (`psycopg2`), Pydantic.
- **AI Engine:** Google GenAI SDK (`google-genai`, mô hình `gemini-2.5-flash`).
- **Frontend:** Streamlit, Pandas, Requests.
- **Cloud Hosting:** Render (Backend API) & Streamlit Cloud (Frontend UI).

---

## 👨‍💻 Tác giả & Phát triển
Phát triển bởi **[Tên của bạn]**. Mọi đóng góp hoặc báo lỗi xin vui lòng liên hệ qua GitHub repository.
