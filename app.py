import os
import streamlit as st
import requests

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Thu Chi AI", page_icon="💰", layout="wide")
st.title("💰 Quản Lý Thu Chi AI")

st.sidebar.header("⚙️ Cài đặt Ngân sách")
monthly_limit = st.sidebar.number_input(
    "Hạn mức chi tiêu tháng (VNĐ):", 
    min_value=1000000, 
    value=10000000, 
    step=1000000,
    format="%d"
)

try:
    res = requests.post(f"{API_URL}/budget-status", json={"monthly_limit": monthly_limit}, timeout=10)
    if res.status_code == 200:
        budget_data = res.json()
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💵 Tổng Thu", f"{budget_data['total_income']:,.0f} VNĐ")
        col2.metric("💸 Tổng Chi", f"{budget_data['total_expense']:,.0f} VNĐ")
        col3.metric("🏦 Số Dư", f"{budget_data['balance']:,.0f} VNĐ")
        col4.metric("📊 Đã Dùng", f"{budget_data['usage_percent']}%")

        if budget_data["status"] == "danger":
            st.error(budget_data["message"])
        elif budget_data["status"] == "warning":
            st.warning(budget_data["message"])
        else:
            st.success(f"✅ {budget_data['message']}")
            
        st.progress(min(budget_data["usage_percent"] / 100.0, 1.0))
except Exception:
    st.info("⚡ Hệ thống đang kết nối đến Backend...")

st.divider()

tab_chat, tab_ocr, tab_history = st.tabs(["💬 Chatbot", "🧾 Quét Bill", "📜 Lịch Sử"])

with tab_chat:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input("Nhập 'Ăn phở 45k' hoặc 'Lương 15tr'...")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        try:
            response = requests.post(f"{API_URL}/chat", json={"message": user_input}, timeout=10)
            reply = response.json()["reply"] if response.status_code == 200 else "⚠️ Lỗi xử lý."
        except Exception as err:
            reply = f"❌ Không thể kết nối Backend: {err}"

        st.session_state.messages.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.write(reply)
        st.rerun()

with tab_ocr:
    st.subheader("Upload hóa đơn/ảnh chuyển khoản")
    uploaded_file = st.file_uploader("Chọn ảnh PNG/JPG:", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Ảnh đã chọn", use_container_width=True)
        if st.button("🔍 Quét & Ghi Nhận", type="primary"):
            with st.spinner("Đang phân tích ảnh..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    res_ocr = requests.post(f"{API_URL}/scan-bill", files=files, timeout=20)
                    if res_ocr.status_code == 200:
                        st.success(res_ocr.json().get("reply"))
                        st.rerun()
                    else:
                        st.error("Lỗi xử lý ảnh.")
                except Exception as ex:
                    st.error(f"Lỗi OCR: {ex}")

with tab_history:
    st.subheader("Lịch sử giao dịch")
    try:
        res_hist = requests.get(f"{API_URL}/history", timeout=10)
        if res_hist.status_code == 200:
            history_data = res_hist.json().get("data", [])
            if history_data:
                formatted_history = [
                    {
                        "ID": item["id"],
                        "Thời gian": item["date"],
                        "Loại": "🟢 Thu" if item["type"] == "income" else "🔴 Chi",
                        "Số tiền (VNĐ)": f"{item['amount']:,.0f}",
                        "Danh mục": item["category"],
                        "Ghi chú": item["note"]
                    } for item in history_data
                ]
                st.dataframe(formatted_history, use_container_width=True)
            else:
                st.info("Chưa có dữ liệu.")
    except Exception:
        st.info("Không thể tải lịch sử.")