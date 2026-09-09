import streamlit as st
import requests

API_URL = "https://thu-chi-ai.onrender.com"

st.set_page_config(page_title="Thu Chi AI", page_icon="💰")

if "user" not in st.session_state:
    st.session_state["user"] = None

# --- MÀN HÌNH ĐĂNG NHẬP / ĐĂNG KÝ ---
if not st.session_state["user"]:
    st.title("🔐 Đăng nhập Thu Chi AI")
    tab_login, tab_reg = st.tabs(["Đăng nhập", "Đăng ký tài khoản"])

    with tab_login:
        u = st.text_input("Tên đăng nhập", key="login_u")
        p = st.text_input("Mật khẩu", type="password", key="login_p")
        if st.button("Đăng nhập", use_container_width=True):
            if u and p:
                try:
                    res = requests.post(f"{API_URL}/login", json={"username": u, "password": p})
                    if res.status_code == 200:
                        st.session_state["user"] = res.json()
                        st.success("Đăng nhập thành công!")
                        st.rerun()
                    else:
                        st.error("Lỗi: " + res.json().get("detail", "Đăng nhập thất bại"))
                except Exception as e:
                    st.error(f"Không thể kết nối Server: {e}")
            else:
                st.warning("Vui lòng điền đủ thông tin!")

    with tab_reg:
        reg_u = st.text_input("Tên đăng nhập mới", key="reg_u")
        reg_p = st.text_input("Mật khẩu mới", type="password", key="reg_p")
        if st.button("Tạo tài khoản mới", use_container_width=True):
            if reg_u and reg_p:
                try:
                    res = requests.post(f"{API_URL}/register", json={"username": reg_u, "password": reg_p})
                    if res.status_code == 200:
                        st.success("Đăng ký thành công! Hãy quay lại tab Đăng nhập.")
                    else:
                        st.error("Lỗi: " + res.json().get("detail", "Đăng ký thất bại"))
                except Exception as e:
                    st.error(f"Không thể kết nối Server: {e}")
            else:
                st.warning("Vui lòng điền đủ thông tin!")

# --- MÀN HÌNH QUẢN LÝ THU CHI ---
else:
    user = st.session_state["user"]
    
    st.sidebar.title("👤 Tài khoản")
    st.sidebar.write(f"Xin chào: **{user['username']}**")
    if st.sidebar.button("Đăng xuất", use_container_width=True):
        st.session_state["user"] = None
        st.rerun()

    st.title("💰 Quản Lý Thu Chi AI")

    tab_chat, tab_history = st.tabs(["💬 Nhập Thu Chi", "📜 Lịch sử"])

    with tab_chat:
        st.write("Nhập chi tiêu hoặc thu nhập của bạn (ví dụ: `Cơm 25k`, `Lương 15tr`):")
        msg = st.chat_input("Nhập ở đây...")
        if msg:
            st.chat_message("user").write(msg)
            try:
                res = requests.post(
                    f"{API_URL}/chat",
                    json={"message": msg, "user_id": user["user_id"]}
                )
                if res.status_code == 200:
                    st.chat_message("assistant").write(res.json()["reply"])
                else:
                    st.error("Lỗi xử lý!")
            except Exception as e:
                st.error(f"Lỗi kết nối: {e}")

    with tab_history:
        if st.button("Làm mới lịch sử"):
            try:
                res = requests.get(f"{API_URL}/history/{user['user_id']}")
                if res.status_code == 200:
                    data = res.json().get("data", [])
                    if data:
                        st.dataframe(data, use_container_width=True)
                    else:
                        st.info("Chưa có lịch sử giao dịch nào.")
            except Exception as e:
                st.error(f"Lỗi tải lịch sử: {e}")
    # --- CẬP NHẬT TRONG TAB GIAO DIỆN CỦA APP.PY ---

    # Thay đổi đoạn tạo Tab:
    tab_chat, tab_history, tab_budget = st.tabs(["💬 Nhập Thu Chi", "📜 Lịch sử", "🎯 Định mức & Cảnh báo"])

    # (Giữ nguyên nội dung tab_chat và tab_history cũ)

    # NỘI DUNG TAB ĐỊNH MỨC & CẢNH BÁO
    with tab_budget:
        st.subheader("⚙️ Cấu hình Định mức Tháng")
        col1, col2 = st.columns(2)
        
        with col1:
            exp_limit = st.number_input("Hạn mức Chi tiêu tháng (VNĐ)", min_value=0, value=10000000, step=500000)
        with col2:
            inc_target = st.number_input("Mục tiêu Thu nhập tháng (VNĐ)", min_value=0, value=20000000, step=1000000)

        if st.button("Phân tích & Kiểm tra Cảnh báo", use_container_width=True):
            try:
                res = requests.post(
                    f"{API_URL}/budget-status",
                    json={
                        "user_id": user["user_id"],
                        "monthly_expense_limit": float(exp_limit),
                        "monthly_income_target": float(inc_target)
                    }
                )
                if res.status_code == 200:
                    data = res.json()
                    
                    st.divider()
                    st.subheader("📊 Báo cáo Tổng quan")
                    
                    # Cột chỉ số
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Tổng Thu Nhập", f"{data['total_income']:,.0f} VNĐ")
                    c2.metric("Tổng Chi Tiêu", f"{data['total_expense']:,.0f} VNĐ")
                    c3.metric("Số Dư Thực Tế", f"{data['balance']:,.0f} VNĐ")

                    st.divider()
                    
                    # Cảnh báo chi tiêu
                    st.write("### 🔴 Cảnh báo Chi tiêu")
                    if data["expense_status"] == "danger":
                        st.error(data["expense_msg"])
                    elif data["expense_status"] == "warning":
                        st.warning(data["expense_msg"])
                    else:
                        st.success(data["expense_msg"])
                    
                    st.progress(min(data["expense_pct"] / 100, 1.0))

                    # Cảnh báo / Tiến độ thu nhập
                    st.write("### 🟢 Tiến độ Thu nhập Mục tiêu")
                    st.info(data["income_msg"])
                    st.progress(min(data["income_pct"] / 100, 1.0))

                else:
                    st.error("Không thể lấy dữ liệu phân tích!")
            except Exception as e:
                st.error(f"Lỗi kết nối: {e}")
