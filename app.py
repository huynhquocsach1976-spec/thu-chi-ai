import streamlit as st
import requests
import pandas as pd
import base64

# Đảm bảo đường dẫn này trỏ chính xác về Render backend của bạn
API_URL = "https://thu-chi-ai.onrender.com"

st.set_page_config(page_title="Thu Chi AI Pro", page_icon="💰", layout="wide")

if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
if "username" not in st.session_state:
    st.session_state["username"] = None

st.title("💰 Thu Chi AI Pro - Quản Lý Tài Chính")

# --- ĐĂNG NHẬP / ĐĂNG KÝ ---
if not st.session_state["user_id"]:
    tab1, tab2 = st.tabs(["🔒 Đăng nhập", "📝 Đăng ký"])
    
    with tab1:
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
                        st.error(res.json().get("detail", "Sai tên đăng nhập hoặc mật khẩu!"))
                except Exception as e:
                    st.error(f"Không thể kết nối Backend: {e}")

    with tab2:
        reg_user = st.text_input("Tên đăng nhập mới", key="reg_user")
        reg_pwd = st.text_input("Mật khẩu mới", type="password", key="reg_pwd")
        if st.button("Đăng ký"):
            if reg_user and reg_pwd:
                try:
                    res = requests.post(f"{API_URL}/register", json={"username": reg_user, "password": reg_pwd})
                    if res.status_code == 200:
                        st.success("Đăng ký thành công! Hãy chuyển sang tab Đăng nhập.")
                    else:
                        st.error(res.json().get("detail", "Đăng ký thất bại!"))
                except Exception as e:
                    st.error(f"Lỗi kết nối Backend: {e}")

# --- GIAO DIỆN CHÍNH ---
else:
    st.sidebar.write(f"👤 Xin chào: **{st.session_state['username']}**")
    if st.sidebar.button("Đăng xuất"):
        st.session_state["user_id"] = None
        st.session_state["username"] = None
        st.rerun()

    tab_chat, tab_scan = st.tabs(["💬 Nhập thu chi nhanh", "📷 Quét hóa đơn / Bill AI"])

    # TAB 1: NHẬP VĂN BẢN
    with tab_chat:
        user_input = st.text_input("Nhập nội dung (VD: `com 15k`, `ca phe 30k`, `luong 15m`):", key="tx_input")
        if st.button("Lưu giao dịch", type="primary"):
            if user_input:
                try:
                    res = requests.post(
                        f"{API_URL}/add-transaction-ai",
                        json={"user_id": st.session_state["user_id"], "text": user_input}
                    )
                    if res.status_code == 200:
                        st.success(res.json().get("message", "Đã ghi nhận!"))
                        st.rerun()
                    else:
                        st.error(f"Lỗi: {res.json().get('detail', res.text)}")
                except Exception as e:
                    st.error(f"Lỗi kết nối: {e}")

    # TAB 2: QUÉT BILL / QR
    with tab_scan:
        st.subheader("Tải lên ảnh Hóa đơn / Mã QR thanh toán")
        uploaded_file = st.file_uploader("Chọn tệp hình ảnh", type=["jpg", "jpeg", "png"])
        
        if uploaded_file is not None:
            st.image(uploaded_file, caption="Ảnh hóa đơn đã chọn", width=280)
            if st.button("Phân tích & Tự động lưu"):
                with st.spinner("Gemini AI đang trích xuất dữ liệu hóa đơn..."):
                    try:
                        bytes_data = uploaded_file.getvalue()
                        base64_img = base64.b64encode(bytes_data).decode('utf-8')
                        
                        res = requests.post(
                            f"{API_URL}/scan-bill",
                            json={"user_id": st.session_state["user_id"], "image_base64": base64_img}
                        )
                        if res.status_code == 200:
                            data = res.json()["data"]
                            st.success(f"✅ Đã quét thành công: **{data['note']}** - Số tiền: **{data['amount']:,.0f} VNĐ** ({data['category']})")
                            st.rerun()
                        else:
                            st.error(f"Lỗi: {res.json().get('detail', res.text)}")
                    except Exception as e:
                        st.error(f"Lỗi xử lý ảnh: {e}")

    st.divider()

    # --- BẢNG THỐNG KÊ VÀ LỊCH SỬ GIAO DỊCH ---
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
                st.info("Chưa có giao dịch nào được lưu.")
        else:
            st.error("Không tải được danh sách giao dịch từ Server.")
    except Exception as e:
        st.error(f"Lỗi kết nối Server: {e}")
