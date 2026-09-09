import streamlit as st
import requests

API_URL = "https://thu-chi-ai.onrender.com"

st.set_page_config(page_title="Thu Chi AI Pro", page_icon="📷", layout="wide")

if "user" not in st.session_state:
    st.session_state["user"] = None

# --- MÀN HÌNH ĐĂNG NHẬP / ĐĂNG KÝ ---
if not st.session_state["user"]:
    st.title("🔐 Đăng nhập Thu Chi AI Pro")
    tab_login, tab_reg = st.tabs(["🔑 Đăng nhập", "📝 Đăng ký tài khoản"])

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
                        st.success("Đăng ký thành công! Hãy chuyển sang tab Đăng nhập.")
                    else:
                        st.error("Lỗi: " + res.json().get("detail", "Đăng ký thất bại"))
                except Exception as e:
                    st.error(f"Không thể kết nối Server: {e}")
            else:
                st.warning("Vui lòng điền đủ thông tin!")

# --- MÀN HÌNH CHÍNH APP ---
else:
    user = st.session_state["user"]
    
    st.sidebar.title("👤 Tài khoản Pro")
    st.sidebar.info(f"Xin chào: **{user['username']}**")
    if st.sidebar.button("🚪 Đăng xuất", use_container_width=True):
        st.session_state["user"] = None
        st.rerun()

    st.title("💎 Quản Lý Thu Chi AI Pro")

    tab_chat, tab_camera, tab_history, tab_budget = st.tabs([
        "💬 Nhập Thu Chi", 
        "📷 Quét Bill Camera",
        "📜 Lịch sử Giao dịch", 
        "🎯 Định mức & Cảnh báo Pro"
    ])

    # --- TAB 1: NHẬP THU CHI ---
    with tab_chat:
        st.subheader("Trợ lý AI Nhận diện Thu Chi")
        st.caption("Ví dụ: `Cơm trưa 35k`, `Xăng xe 50k`, `Lương tháng 15tr`")
        msg = st.chat_input("Nhập thông tin thu chi...")
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
                    st.error("Lỗi xử lý giao dịch!")
            except Exception as e:
                st.error(f"Lỗi kết nối: {e}")

    # --- TAB 2: QUÉT BILL BẰNG CAMERA TRỰC TIẾP ---
    with tab_camera:
        st.subheader("📸 Quét Hóa Đơn Trực Tiếp Bằng Camera / Tải Ảnh")
        
        mode = st.radio("Chọn phương thức nhập ảnh:", ["📷 Chụp trực tiếp từ Camera", "📁 Tải ảnh Bill từ máy"], horizontal=True)
        
        img_file = None
        if "Camera" in mode:
            img_file = st.camera_input("Chụp ảnh hóa đơn của bạn")
        else:
            img_file = st.file_uploader("Chọn ảnh Hóa đơn (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])

        if img_file is not None:
            st.image(img_file, caption="Ảnh Bill đã chọn", use_column_width=True)
            if st.button("🚀 Quét & Tự Động Lưu Giao Dịch", type="primary", use_container_width=True):
                with st.spinner("Đang phân tích hóa đơn..."):
                    try:
                        files = {"file": (img_file.name, img_file.getvalue(), img_file.type)}
                        data = {"user_id": user["user_id"]}
                        res = requests.post(f"{API_URL}/scan-bill", data=data, files=files)
                        
                        if res.status_code == 200:
                            st.success(res.json()["reply"])
                        else:
                            st.error("Lỗi xử lý hình ảnh!")
                    except Exception as e:
                        st.error(f"Lỗi kết nối: {e}")

    # --- TAB 3: LỊCH SỬ ---
    with tab_history:
        st.subheader("Lịch sử giao dịch gần đây")
        if st.button("🔄 Tải lại lịch sử"):
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

    # --- TAB 4: ĐỊNH MỨC & CẢNH BÁO PRO ---
    with tab_budget:
        st.subheader("🎯 Cấu hình Hạn mức & Mục tiêu Tài chính")
        
        c_exp, c_inc = st.columns(2)
        with c_exp:
            exp_limit = st.number_input(
                "🔴 Hạn mức Chi tiêu Tối đa (VNĐ)", 
                min_value=100000, 
                value=10000000, 
                step=500000
            )
        with c_inc:
            inc_target = st.number_input(
                "🟢 Mục tiêu Thu nhập Tháng (VNĐ)", 
                min_value=100000, 
                value=20000000, 
                step=1000000
            )

        if st.button("📊 Phân tích & Phản hồi Cảnh báo Pro", use_container_width=True, type="primary"):
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
                    
                    st.markdown("---")
                    st.subheader("📈 Báo cáo Tài chính Tháng")
                    
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Tổng Thu Nhập", f"{data['total_income']:,.0f} VNĐ")
                    m2.metric("Tổng Chi Tiêu", f"{data['total_expense']:,.0f} VNĐ")
                    m3.metric("Số Dư Ròng", f"{data['balance']:,.0f} VNĐ")

                    st.markdown("---")
                    
                    st.write("### 🔴 Hạn mức Chi tiêu")
                    if data["expense_status"] == "danger":
                        st.error(data["expense_msg"])
                    elif data["expense_status"] == "warning":
                        st.warning(data["expense_msg"])
                    else:
                        st.success(data["expense_msg"])
                    
                    st.progress(min(data["expense_pct"] / 100.0, 1.0))
                    st.caption(f"Đã dùng: **{data['expense_pct']}%** hạn mức cho phép.")

                    st.write("### 🟢 Mục tiêu Thu nhập")
                    st.info(data["income_msg"])
                    st.progress(min(data["income_pct"] / 100.0, 1.0))
                    st.caption(f"Tỷ lệ hoàn thành: **{data['income_pct']}%** mục tiêu.")

                else:
                    st.error("Không thể lấy dữ liệu phân tích!")
            except Exception as e:
                st.error(f"Lỗi kết nối: {e}")
