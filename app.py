import os
import requests
import streamlit as st


# =========================================================
# CẤU HÌNH
# =========================================================

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "https://thu-chi-ai.onrender.com"
).rstrip("/")


st.set_page_config(
    page_title="Thu Chi AI Pro",
    page_icon="💰",
    layout="wide"
)


# =========================================================
# SESSION
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "username" not in st.session_state:
    st.session_state.username = ""


# =========================================================
# HÀM XỬ LÝ LỖI
# =========================================================

def get_error(response):

    try:
        data = response.json()

        error = data.get(
            "detail",
            "Có lỗi xảy ra"
        )

        if isinstance(error, list):
            messages = []

            for item in error:
                if isinstance(item, dict):
                    messages.append(
                        item.get(
                            "msg",
                            str(item)
                        )
                    )
                else:
                    messages.append(str(item))

            return "; ".join(messages)

        return str(error)

    except Exception:

        if response.text:
            return response.text

        return "Có lỗi xảy ra"


# =========================================================
# KIỂM TRA BACKEND
# =========================================================

def check_backend():

    try:

        response = requests.get(
            BACKEND_URL + "/",
            timeout=30
        )

        return response.status_code == 200

    except Exception:

        return False


# =========================================================
# ĐĂNG KÝ
# =========================================================

def register_user(username, password):

    try:

        response = requests.post(
            BACKEND_URL + "/register",
            json={
                "username": username,
                "password": password
            },
            timeout=60
        )

        if response.status_code != 200:
            return False, get_error(response)

        return True, response.json()

    except requests.exceptions.Timeout:

        return False, "Backend phản hồi quá lâu."

    except requests.exceptions.ConnectionError:

        return False, "Không kết nối được Backend."

    except Exception as e:

        return False, str(e)


# =========================================================
# ĐĂNG NHẬP
# =========================================================

def login_user(username, password):

    try:

        response = requests.post(
            BACKEND_URL + "/login",
            json={
                "username": username,
                "password": password
            },
            timeout=60
        )

        if response.status_code != 200:
            return False, get_error(response)

        return True, response.json()

    except requests.exceptions.Timeout:

        return False, "Backend phản hồi quá lâu."

    except requests.exceptions.ConnectionError:

        return False, "Không kết nối được Backend."

    except Exception as e:

        return False, str(e)


# =========================================================
# THÊM GIAO DỊCH BẰNG AI
# =========================================================

def add_transaction_ai(text):

    try:

        response = requests.post(
            BACKEND_URL + "/add-transaction-ai",
            json={
                "user_id": st.session_state.user_id,
                "text": text
            },
            timeout=180
        )

        if response.status_code != 200:
            return False, get_error(response)

        return True, response.json()

    except requests.exceptions.Timeout:

        return False, "AI xử lý quá lâu. Vui lòng thử lại."

    except requests.exceptions.ConnectionError:

        return False, "Không kết nối được Backend."

    except Exception as e:

        return False, str(e)


# =========================================================
# LẤY DANH SÁCH GIAO DỊCH
# =========================================================

def get_transactions():

    try:

        response = requests.get(
            BACKEND_URL
            + f"/transactions/{st.session_state.user_id}",
            timeout=60
        )

        if response.status_code != 200:
            return False, get_error(response)

        return True, response.json()

    except requests.exceptions.Timeout:

        return False, "Backend phản hồi quá lâu."

    except requests.exceptions.ConnectionError:

        return False, "Không kết nối được Backend."

    except Exception as e:

        return False, str(e)


# =========================================================
# QUÉT HÓA ĐƠN
# =========================================================

def scan_bill(uploaded_file):

    try:

        file_bytes = uploaded_file.getvalue()

        if not file_bytes:
            return False, "File ảnh rỗng."

        files = {
            "file": (
                uploaded_file.name,
                file_bytes,
                uploaded_file.type or "image/jpeg"
            )
        }

        response = requests.post(
            BACKEND_URL + "/scan-bill",
            params={
                "user_id": st.session_state.user_id
            },
            files=files,
            timeout=180
        )

        if response.status_code != 200:
            return False, get_error(response)

        return True, response.json()

    except requests.exceptions.Timeout:

        return False, "Quét hóa đơn quá lâu. Vui lòng thử lại."

    except requests.exceptions.ConnectionError:

        return False, "Không kết nối được Backend."

    except Exception as e:

        return False, str(e)


# =========================================================
# TRANG ĐĂNG NHẬP
# =========================================================

if not st.session_state.logged_in:

    st.title("💰 Thu Chi AI Pro")

    st.write(
        "Quản lý thu chi thông minh bằng AI"
    )

    st.divider()

    login_tab, register_tab = st.tabs(
        [
            "🔐 Đăng nhập",
            "📝 Đăng ký"
        ]
    )

    # =====================================================
    # ĐĂNG NHẬP
    # =====================================================

    with login_tab:

        st.subheader("Đăng nhập")

        username = st.text_input(
            "Tên đăng nhập",
            key="login_username"
        )

        password = st.text_input(
            "Mật khẩu",
            type="password",
            key="login_password"
        )

        if st.button(
            "🔐 Đăng nhập",
            use_container_width=True
        ):

            if not username.strip():

                st.warning(
                    "Vui lòng nhập tên đăng nhập."
                )

            elif not password:

                st.warning(
                    "Vui lòng nhập mật khẩu."
                )

            else:

                with st.spinner(
                    "Đang đăng nhập..."
                ):

                    success, result = login_user(
                        username.strip(),
                        password
                    )

                if success:

                    st.session_state.logged_in = True

                    st.session_state.user_id = (
                        result["user_id"]
                    )

                    st.session_state.username = (
                        result["username"]
                    )

                    st.success(
                        "Đăng nhập thành công!"
                    )

                    st.rerun()

                else:

                    st.error(
                        "❌ " + str(result)
                    )

    # =====================================================
    # ĐĂNG KÝ
    # =====================================================

    with register_tab:

        st.subheader("Đăng ký tài khoản")

        new_username = st.text_input(
            "Tên đăng nhập",
            key="register_username"
        )

        new_password = st.text_input(
            "Mật khẩu",
            type="password",
            key="register_password"
        )

        confirm_password = st.text_input(
            "Nhập lại mật khẩu",
            type="password",
            key="register_confirm_password"
        )

        if st.button(
            "📝 Đăng ký",
            use_container_width=True
        ):

            if not new_username.strip():

                st.warning(
                    "Vui lòng nhập tên đăng nhập."
                )

            elif len(new_username.strip()) < 3:

                st.warning(
                    "Tên đăng nhập phải có ít nhất 3 ký tự."
                )

            elif not new_password:

                st.warning(
                    "Vui lòng nhập mật khẩu."
                )

            elif len(new_password) < 4:

                st.warning(
                    "Mật khẩu phải có ít nhất 4 ký tự."
                )

            elif new_password != confirm_password:

                st.error(
                    "❌ Hai mật khẩu không giống nhau."
                )

            else:

                with st.spinner(
                    "Đang tạo tài khoản..."
                ):

                    success, result = register_user(
                        new_username.strip(),
                        new_password
                    )

                if success:

                    st.success(
                        "✅ Đăng ký thành công!"
                    )

                    st.info(
                        "Bây giờ anh chuyển sang tab Đăng nhập."
                    )

                else:

                    st.error(
                        "❌ " + str(result)
                    )

    st.stop()


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.title("💰 Thu Chi AI Pro")

    st.write(
        f"👤 **{st.session_state.username}**"
    )

    st.divider()

    backend_ok = check_backend()

    if backend_ok:

        st.success(
            "🟢 Backend Online"
        )

    else:

        st.error(
            "🔴 Backend Offline"
        )

    st.divider()

    if st.button(
        "🚪 Đăng xuất",
        use_container_width=True
    ):

        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = ""

        st.rerun()


# =========================================================
# TRANG CHÍNH
# =========================================================

st.title("💰 Thu Chi AI Pro")

st.write(
    f"Xin chào **{st.session_state.username}** 👋"
)

st.caption(
    "Quản lý thu chi bằng trí tuệ nhân tạo"
)


# =========================================================
# CÁC TAB
# =========================================================

tab_ai, tab_bill, tab_history = st.tabs(
    [
        "🤖 Nhập giao dịch AI",
        "📷 Quét hóa đơn",
        "📊 Lịch sử giao dịch"
    ]
)


# =========================================================
# TAB AI
# =========================================================

with tab_ai:

    st.subheader(
        "🤖 Nhập giao dịch bằng AI"
    )

    st.info(
        "Ví dụ: ăn cơm 40k"
    )

    transaction_text = st.text_input(
        "Nội dung giao dịch",
        placeholder="Ví dụ: mua cơm 40k"
    )

    if st.button(
        "✨ Phân tích và lưu",
        use_container_width=True
    ):

        if not transaction_text.strip():

            st.warning(
                "Vui lòng nhập nội dung giao dịch."
            )

        else:

            with st.spinner(
                "🤖 AI đang phân tích..."
            ):

                success, result = add_transaction_ai(
                    transaction_text.strip()
                )

            if success:

                st.success(
                    "✅ Đã thêm giao dịch thành công!"
                )

                amount = float(
                    result.get(
                        "amount",
                        0
                    )
                )

                transaction_type = result.get(
                    "transaction_type",
                    "expense"
                )

                description = result.get(
                    "description",
                    ""
                )

                category = result.get(
                    "category",
                    "Khác"
                )

                col1, col2, col3 = st.columns(3)

                with col1:

                    st.metric(
                        "💰 Số tiền",
                        f"{amount:,.0f} đ"
                    )

                with col2:

                    if transaction_type == "income":

                        st.metric(
                            "📈 Loại",
                            "Thu"
                        )

                    else:

                        st.metric(
                            "📉 Loại",
                            "Chi"
                        )

                with col3:

                    st.metric(
                        "📁 Danh mục",
                        category
                    )

                st.write(
                    "**Mô tả:**",
                    description
                )

            else:

                st.error(
                    "❌ Lỗi xử lý giao dịch AI: "
                    + str(result)
                )


# =========================================================
# TAB QUÉT HÓA ĐƠN
# =========================================================

with tab_bill:

    st.subheader(
        "📷 Quét hóa đơn bằng AI"
    )

    uploaded_file = st.file_uploader(
        "Chọn ảnh hóa đơn",
        type=[
            "jpg",
            "jpeg",
            "png",
            "webp"
        ]
    )

    if uploaded_file:

        st.image(
            uploaded_file,
            caption="Hóa đơn",
            use_container_width=True
        )

        if st.button(
            "🔍 Quét và lưu hóa đơn",
            use_container_width=True
        ):

            with st.spinner(
                "🤖 AI đang đọc hóa đơn..."
            ):

                success, result = scan_bill(
                    uploaded_file
                )

            if success:

                st.success(
                    "✅ Đã quét và lưu hóa đơn!"
                )

                amount = float(
                    result.get(
                        "amount",
                        0
                    )
                )

                st.metric(
                    "💰 Tổng tiền",
                    f"{amount:,.0f} đ"
                )

                st.write(
                    "**Mô tả:**",
                    result.get(
                        "description",
                        ""
                    )
                )

                st.write(
                    "**Danh mục:**",
                    result.get(
                        "category",
                        "Khác"
                    )
                )

            else:

                st.error(
                    "❌ Lỗi xử lý ảnh: "
                    + str(result)
                )


# =========================================================
# TAB LỊCH SỬ
# =========================================================

with tab_history:

    st.subheader(
        "📊 Lịch sử giao dịch"
    )

    if st.button(
        "🔄 Tải lại dữ liệu",
        use_container_width=True
    ):

        st.rerun()

    success, transactions = get_transactions()

    if not success:

        st.error(
            "❌ " + str(transactions)
        )

    elif not transactions:

        st.info(
            "Chưa có giao dịch nào."
        )

    else:

        total_income = 0
        total_expense = 0

        for item in transactions:

            amount = float(
                item.get(
                    "amount",
                    0
                )
            )

            transaction_type = item.get(
                "transaction_type",
                "expense"
            )

            if transaction_type == "income":

                total_income += amount

            else:

                total_expense += amount

        balance = (
            total_income
            - total_expense
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "💵 Tổng thu",
                f"{total_income:,.0f} đ"
            )

        with col2:

            st.metric(
                "💸 Tổng chi",
                f"{total_expense:,.0f} đ"
            )

        with col3:

            st.metric(
                "💰 Số dư",
                f"{balance:,.0f} đ"
            )

        st.divider()

        for item in transactions:

            amount = float(
                item.get(
                    "amount",
                    0
                )
            )

            transaction_type = item.get(
                "transaction_type",
                "expense"
            )

            description = item.get(
                "description",
                "Không có mô tả"
            )

            category = item.get(
                "category",
                "Khác"
            )

            created_at = item.get(
                "created_at",
                ""
            )

            if transaction_type == "income":

                icon = "🟢"
                type_text = "THU"
                sign = "+"

            else:

                icon = "🔴"
                type_text = "CHI"
                sign = "-"

            with st.container():

                col1, col2 = st.columns(
                    [3, 1]
                )

                with col1:

                    st.markdown(
                        f"### {icon} {description}"
                    )

                    st.write(
                        f"**Danh mục:** {category}"
                    )

                    st.caption(
                        f"{type_text} • {created_at}"
                    )

                with col2:

                    st.markdown(
                        f"### {sign}{amount:,.0f} đ"
                    )

                st.divider()
