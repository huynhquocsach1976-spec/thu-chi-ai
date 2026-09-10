import streamlit as st
import requests
import pandas as pd

# Cấu hình URL kết nối Backend
API_URL = "https://thu-chi-ai.onrender.com"

st.set_page_config(page_title="Thu Chi AI Pro", page_icon="💰", layout="wide")

# Khởi tạo trạng thái đăng nhập
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
if "username" not in st.session_state:
    st.session_state["username"] = None

st.title("💰 Thu Chi AI Pro - Quản Lý Tài Chính")

# ---------------------------------------------------------
# 1. MÀN HÌNH ĐĂNG NHẬP / ĐĂNG KÝ
# ---------------------------------------------------------
if not st.session_state["user_id"]:
    tab1, tab2 = st.tabs(["🔒 Đăng nhập", "📝 Đăng ký"])
    
    with tab1:
        st.subheader("Đăng nhập")
        login_user = st.text_input("Tên đăng nhập", key="login_user")
        login_pwd = st.text_input("Mật khẩu", type="password", key="login_pwd")
        if st.button("Đăng nhập", type="primary"):
            if login_user and login_pwd:
                try:
                    res = requests.post(f"{API_URL}/login", json={"username": login_user, "password": login_pwd})
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state["user_id"] = data["user_id"]
                        st.session_state["username"] = data["username"]
                        st.success("Đăng nhập thành công!")
                        st.rerun()
                    else:
                        st.error(res.json().get("detail", "Đăng nhập thất bại!"))
                except Exception as e:
                    st.error(f"Không thể kết nối Backend: {e}")
            else:
                st.warning("Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu!")

    with tab2:
        st.subheader("Đăng ký tài khoản")
        reg_user = st.text_input("Tên đăng nhập mới", key="reg_user")
        reg_pwd = st.text_input("Mật khẩu mới", type="password", key="reg_pwd")
        if st.button("Đăng ký"):
            if reg_user and reg_pwd:
                try:
                    res = requests.post(f"{API_URL}/register", json={"username": reg_user, "password": reg_pwd})
                    if res.status_code == 200:
                        st.success("Tạo tài khoản thành công! Hãy chuyển sang Tab Đăng nhập.")
                    else:
                        st.error(res.json().get("detail", "Đăng ký thất bại!"))
                except Exception as e:
                    st.error(f"Không thể kết nối Backend: {e}")
            else:
                st.warning("Vui lòng điền thông tin đăng ký!")

# ---------------------------------------------------------
# 2. MÀN HÌNH CHÍNH QUẢN LÝ THU CHI
# ---------------------------------------------------------
else:
    st.sidebar.write(f"👤 Tài khoản: **{st.session_state['username']}**")
    if st.sidebar.button("Đăng xuất"):
        st.session_state["user_id"] = None
        st.session_state["username"] = None
        st.rerun()

    # Form nhập thu chi nhanh
    st.subheader("💬 Ghi nhận thu chi nhanh")
    user_input = st.text_input(
        "Nhập nội dung (VD: `com 15k`, `ca phe 30k`, `luong 15m`):", 
        key="tx_input"
    )
    
    if st.button("Lưu giao dịch", type="primary"):
        if user_input:
            try:
                res = requests.post(
                    f"{API_URL}/add-transaction-ai",
                    json={"user_id": st.session_state["user_id"], "text": user_input}
                )
                if res.status_code == 200:
                    tx = res.json()["data"]
                    st.success(f"✅ Đã ghi nhận: **{tx['type']}** - {tx['amount']:,.0f} VNĐ ({tx['category']})")
                else:
                    st.error(f"Lỗi: {res.json().get('detail', res.text)}")
            except Exception as e:
                st.error(f"Lỗi gửi dữ liệu: {e}")
        else:
            st.warning("Vui lòng nhập thông tin chi tiêu!")

    st.divider()

    # Bảng thống kê & lịch sử
    st.subheader("📊 Thống kê & Lịch sử giao dịch")
    try:
        res = requests.get(f"{API_URL}/transactions/{st.session_state['user_id']}")
        if res.status_code == 200:
            tx_data = res.json()["data"]
            if tx_data:
                df = pd.DataFrame(tx_data)
                
                total_income = df[df['type'] == 'thu']['amount'].sum()
                total_expense = df[df['type'] == 'chi']['amount'].sum()
                balance = total_income - total_expense

                col1, col2, col3 = st.columns(3)
                col1.metric("💵 Tổng Thu", f"{total_income:,.0f} VNĐ")
                col2.metric("💸 Tổng Chi", f"{total_expense:,.0f} VNĐ")
                col3.metric("💳 Số Dư", f"{balance:,.0f} VNĐ")

                st.dataframe(df[['date', 'type', 'amount', 'category', 'note']], use_container_width=True)
            else:
                st.info("Chưa có giao dịch nào.")
        else:
            st.error("Không tải được danh sách giao dịch.")
    except Exception as e:
        st.error(f"Lỗi tải dữ liệu: {e}")
