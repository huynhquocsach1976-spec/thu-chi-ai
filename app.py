import streamlit as st
import requests

API_URL = "https://thu-chi-ai.onrender.com"

st.set_page_config(page_title="Thu Chi AI Pro", page_icon="💰")

if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
if "username" not in st.session_state:
    st.session_state["username"] = None

st.title("💰 Thu Chi AI Pro")

# --- ĐĂNG NHẬP / ĐĂNG KÝ (GIỮ NGUYÊN CODE CŨ) ---
if not st.session_state["user_id"]:
    tab1, tab2 = st.tabs(["🔒 Đăng nhập", "📝 Đăng ký"])
    
    with tab1:
        login_user = st.text_input("Tên đăng nhập", key="login_user")
        login_pwd = st.text_input("Mật khẩu", type="password", key="login_pwd")
        if st.button("Đăng nhập"):
            res = requests.post(f"{API_URL}/login", json={"username": login_user, "password": login_pwd})
            if res.status_code == 200:
                data = res.json()
                st.session_state["user_id"] = data["user_id"]
                st.session_state["username"] = data["username"]
                st.success("Đăng nhập thành công!")
                st.rerun()
            else:
                st.error("Sai thông tin đăng nhập!")

    with tab2:
        reg_user = st.text_input("Tên đăng nhập mới", key="reg_user")
        reg_pwd = st.text_input("Mật khẩu mới", type="password", key="reg_pwd")
        if st.button("Đăng ký"):
            res = requests.post(f"{API_URL}/register", json={"username": reg_user, "password": reg_pwd})
            if res.status_code == 200:
                st.success("Tạo tài khoản thành công! Hãy đăng nhập.")
            else:
                st.error("Tài khoản đã tồn tại!")

# --- MÀN HÌNH CHÍNH (BỔ SUNG KHẮC PHỤC LỖI NOT FOUND) ---
else:
    st.sidebar.write(f"Xin chào, **{st.session_state['username']}**")
    if st.sidebar.button("Đăng xuất"):
        st.session_state["user_id"] = None
        st.session_state["username"] = None
        st.rerun()

    st.subheader("Ghi nhận chi tiêu")
    user_input = st.text_input("Nhập câu chi tiêu (VD: com 15k, ca phe 30k):")
    
    if st.button("Lưu giao dịch", type="primary"):
        if user_input:
            # Gửi chính xác tới /add-transaction-ai
            res = requests.post(
                f"{API_URL}/add-transaction-ai",
                json={"user_id": st.session_state["user_id"], "text": user_input}
            )
            if res.status_code == 200:
                st.success(res.json().get("message", "Đã lưu thành công!"))
            else:
                st.error(f"Lỗi: {res.text}")
        else:
            st.warning("Vui lòng nhập nội dung!")
