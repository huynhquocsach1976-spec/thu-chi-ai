
---

## 📄 Phần Hướng dẫn người dùng trong `app.py`

Thay thế hàm `DEFAULT_INTRO` trong file `app.py` bằng nội dung sau:

```python
DEFAULT_INTRO = """
# 💰 Thu Chi AI Pro

**Ứng dụng quản lý thu chi cá nhân thông minh**: nhập giao dịch bằng câu nói tự nhiên, quét hóa đơn bằng ảnh, đặt ngân sách theo tháng và xuất báo cáo Excel / PDF. Toàn bộ phần "hiểu" nội dung do AI (Google Gemini) đảm nhận.

---

## ✨ Điểm nổi bật
- 🧠 AI hiểu ngôn ngữ tự nhiên: chỉ cần nói "ăn cơm 40k" là xong
- 📷 Quét hóa đơn tự động: chụp ảnh → AI đọc hết → tự lưu
- 📊 Thống kê trực quan: biểu đồ rõ ràng, theo tháng/danh mục
- 🎯 Ngân sách thông minh: cảnh báo sớm khi sắp/vượt hạn mức
- 📑 Xuất báo cáo: Excel, PDF đầy đủ
- 🔒 An toàn & riêng tư: dữ liệu của bạn được bảo vệ

---

## 📌 Hướng dẫn nhanh
- Vào **🤖 Nhập giao dịch** để ghi nhận thu/chi
- Vào **📷 Quét hóa đơn** để nhập nhanh bằng ảnh
- Vào **📊 Lịch sử** để xem, tìm, sửa, xóa
- Vào **🎯 Ngân sách** để đặt hạn mức chi tiêu
- Vào **📑 Báo cáo** để tải file về

---

### 🤖 Nhập bằng AI — Ví dụ
| Bạn nhập | Kết quả |
|---|---|
| `ăn cơm 40k` | Chi · 40.000 đ · Ăn uống |
| `nhận lương 20 triệu` | Thu · 20.000.000 đ · Lương |
| `đổ xăng 2tr5` | Chi · 2.500.000 đ · Di chuyển |
"""

def show_intro():
    st.markdown(DEFAULT_INTRO)
