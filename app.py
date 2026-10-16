python
import streamlit as st
import requests
import pandas as pd
import base64
import os

# =========================================================
# CẤU HÌNH
# =========================================================

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://127.0.0.1:8000"
)

st.set_page_config(
    page_title="Thu Chi AI Pro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# CSS GIAO DIỆN
# =========================================================

st.markdown("""
<style>

.main {
    background-color: #f5f7fb;
}

.block-container {
    padding-top: 2rem;
}

.title {
    font-size: 36px;
    font-weight: 700;
}

.subtitle {
    color: #666;
    font-size: 16px;
}

.card {
    background: white;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    margin-bottom: 15px;
}

.money {
    font-size: 28px;
    font-weight: 700;
}

.small {
    color: #777;
}

</style>
""", unsafe_allow_html=True)


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
# HÀM GỌI API
# =========================================================

def api_post(endpoint, data):

    try:
        response = requests.post(
            f"{BACKEND_URL}{endpoint}",
            json=data,
            timeout=60
        )

        try:
            result = response.json()
        except:
            result = {
                "detail": response.text
            }

        return response.status_code, result

    except requests.exceptions.ConnectionError:
        return 0, {
            "detail": "Không thể kết nối Backend FastAPI!"
        }

    except Exception as e:
        return 0, {
            "detail": str(e)
        }


def api_get(endpoint):

    try:
        response = requests.get(
            f"{BACKEND_URL}{endpoint}",
            timeout=60
        )

        try:
            result = response.json()
        except:
            result = {
                "detail": response.text
            }

        return response.status_code, result

    except requests.exceptions.ConnectionError:
        return 0, {
            "detail": "Không thể kết nối Backend FastAPI!"
        }

    except Exception as e:
        return 0, {
            "detail": str(e)
        }


# =========================================================
# TRANG ĐĂNG NHẬP / ĐĂNG KÝ
# =========================================================

def login_page():

    st.markdown(
        '<div class="title">💰 Thu Chi AI Pro</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Quản lý tài chính cá nhân bằng AI</div>',
        unsafe_allow_html=True
    )

    st.write("")

    tab_login, tab_register = st.tabs(
        ["🔐 Đăng nhập", "📝 Đăng ký"]
    )

    # -----------------------------------------------------
    # LOGIN
    # -----------------------------------------------------

    with tab_login:

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

            if not username or not password:

                st.warning(
                    "Vui lòng nhập đầy đủ tài khoản và mật khẩu."
                )

            else:

                status, result = api_post(
                    "/login",
                    {
                        "username": username,
                        "password": password
                    }
                )

                if status == 200:

                    st.session_state.logged_in = True
                    st.session_state.user_id = result["user_id"]
                    st.session_state.username = result["username"]

                    st.success("Đăng nhập thành công!")

                    st.rerun()

                else:

                    st.error(
                        result.get(
                            "detail",
                            "Đăng nhập thất bại!"
                        )
                    )

    # -----------------------------------------------------
    # REGISTER
    # -----------------------------------------------------

    with tab_register:

        st.subheader("Tạo tài khoản")

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
            key="confirm_password"
        )

        if st.button(
            "📝 Đăng ký",
            use_container_width=True
        ):

            if not new_username or not new_password:

                st.warning(
                    "Vui lòng nhập đầy đủ thông tin."
                )

            elif new_password != confirm_password:

                st.error(
                    "Mật khẩu nhập lại không khớp!"
                )

            else:

                status, result = api_post(
                    "/register",
                    {
                        "username": new_username,
                        "password": new_password
                    }
                )

                if status == 200:

                    st.success(
                        "Đăng ký thành công! "
                        "Bây giờ anh có thể đăng nhập."
                    )

                else:

                    st.error(
                        result.get(
                            "detail",
                            "Đăng ký thất bại!"
                        )
                    )


# =========================================================
# SIDEBAR
# =========================================================

def sidebar():

    with st.sidebar:

        st.markdown("# 💰 Thu Chi AI")

        st.write(
            f"👤 **{st.session_state.username}**"
        )

        st.divider()

        menu = st.radio(
            "MENU",
            [
                "🏠 Tổng quan",
                "💸 Thêm giao dịch",
                "📷 Quét hóa đơn",
                "📋 Lịch sử",
                "📊 Thống kê"
            ]
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

    return menu


# =========================================================
# LẤY GIAO DỊCH
# =========================================================

def get_transactions():

    status, result = api_get(
        f"/transactions/{st.session_state.user_id}"
    )

    if status == 200:

        return result.get("data", [])

    st.error(
        result.get(
            "detail",
            "Không lấy được dữ liệu."
        )
    )

    return []


# =========================================================
# TỔNG QUAN
# =========================================================

def dashboard():

    st.markdown(
        '<div class="title">🏠 Tổng quan</div>',
        unsafe_allow_html=True
    )

    st.write(
        f"Xin chào **{st.session_state.username}** 👋"
    )

    transactions = get_transactions()

    total_income = 0
    total_expense = 0

    for tx in transactions:

        amount = float(tx.get("amount", 0))

        if tx.get("type") == "thu":
            total_income += amount

        else:
            total_expense += amount

    balance = total_income - total_expense

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "💰 Tổng thu",
            f"{total_income:,.0f} đ"
        )

    with col2:

        st.metric(
            "💸 Tổng chi",
            f"{total_expense:,.0f} đ"
        )

    with col3:

        st.metric(
            "💵 Số dư",
            f"{balance:,.0f} đ"
        )

    st.write("")

    # -----------------------------------------------------
    # NHẬP NHANH
    # -----------------------------------------------------

    st.subheader("🤖 Nhập giao dịch nhanh")

    quick_text = st.text_input(
        "Ví dụ: Ăn cơm 50k, đổ xăng 100k, nhận lương 15 triệu",
        key="quick_transaction"
    )

    if st.button(
        "➕ Ghi nhận giao dịch",
        use_container_width=True
    ):

        if not quick_text:

            st.warning(
                "Anh hãy nhập nội dung giao dịch."
            )

        else:

            status, result = api_post(
                "/add-transaction-ai",
                {
                    "user_id": st.session_state.user_id,
                    "text": quick_text
                }
            )

            if status == 200:

                data = result.get("data", {})

                st.success(
                    f"Đã ghi nhận "
                    f"{data.get('amount', 0):,.0f} đ - "
                    f"{data.get('category', 'Khác')}"
                )

                st.rerun()

            else:

                st.error(
                    result.get(
                        "detail",
                        "Không thể ghi nhận giao dịch."
                    )
                )

    # -----------------------------------------------------
    # GIAO DỊCH GẦN ĐÂY
    # -----------------------------------------------------

    st.subheader("📋 Giao dịch gần đây")

    if transactions:

        recent = transactions[:10]

        for tx in recent:

            amount = float(tx.get("amount", 0))

            icon = (
                "🟢"
                if tx.get("type") == "thu"
                else "🔴"
            )

            sign = (
                "+"
                if tx.get("type") == "thu"
                else "-"
            )

            st.write(
                f"{icon} **{tx.get('category', 'Khác')}**  "
                f"{sign}{amount:,.0f} đ  —  "
                f"{tx.get('note', '')}"
            )

    else:

        st.info(
            "Chưa có giao dịch nào."
        )


# =========================================================
# THÊM GIAO DỊCH
# =========================================================

def add_transaction():

    st.markdown(
        '<div class="title">💸 Thêm giao dịch</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Anh có thể nhập bằng câu nói tự nhiên."
    )

    text = st.text_area(
        "Nội dung giao dịch",
        placeholder=(
            "Ví dụ:\n"
            "Ăn cơm 50k\n"
            "Đổ xăng 100k\n"
            "Nhận lương 15 triệu"
        ),
        height=150
    )

    if st.button(
        "🤖 AI phân tích & lưu",
        use_container_width=True
    ):

        if not text:

            st.warning(
                "Vui lòng nhập nội dung giao dịch."
            )

            return

        status, result = api_post(
            "/add-transaction-ai",
            {
                "user_id": st.session_state.user_id,
                "text": text
            }
        )

        if status == 200:

            data = result.get("data", {})

            st.success(
                "Giao dịch đã được lưu!"
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Số tiền",
                    f"{data.get('amount', 0):,.0f} đ"
                )

            with col2:
                st.metric(
                    "Loại",
                    data.get("type", "")
                )

            with col3:
                st.metric(
                    "Danh mục",
                    data.get("category", "")
                )

        else:

            st.error(
                result.get(
                    "detail",
                    "Có lỗi xảy ra."
                )
            )


# =========================================================
# QUÉT HÓA ĐƠN
# =========================================================

def scan_bill():

    st.markdown(
        '<div class="title">📷 Quét hóa đơn AI</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Tải ảnh hóa đơn lên để Gemini AI phân tích."
    )

    uploaded_file = st.file_uploader(
        "Chọn ảnh hóa đơn",
        type=["jpg", "jpeg", "png", "webp"]
    )

    if uploaded_file:

        st.image(
            uploaded_file,
            caption="Hóa đơn đã chọn",
            use_container_width=True
        )

        if st.button(
            "🤖 Phân tích hóa đơn",
            use_container_width=True
        ):

            try:

                image_bytes = uploaded_file.read()

                image_base64 = base64.b64encode(
                    image_bytes
                ).decode("utf-8")

                status, result = api_post(
                    "/scan-bill",
                    {
                        "user_id": st.session_state.user_id,
                        "image_base64": image_base64
                    }
                )

                if status == 200:

                    data = result.get(
                        "data",
                        {}
                    )

                    st.success(
                        "Quét hóa đơn thành công!"
                    )

                    st.metric(
                        "💰 Số tiền",
                        f"{data.get('amount', 0):,.0f} đ"
                    )

                    st.write(
                        f"**Danh mục:** "
                        f"{data.get('category', 'Khác')}"
                    )

                    st.write(
                        f"**Nội dung:** "
                        f"{data.get('note', '')}"
                    )

                else:

                    st.error(
                        result.get(
                            "detail",
                            "Không thể xử lý hóa đơn."
                        )
                    )

            except Exception as e:

                st.error(
                    f"Lỗi xử lý ảnh: {str(e)}"
                )


# =========================================================
# LỊCH SỬ
# =========================================================

def history():

    st.markdown(
        '<div class="title">📋 Lịch sử giao dịch</div>',
        unsafe_allow_html=True
    )

    transactions = get_transactions()

    if not transactions:

        st.info(
            "Chưa có giao dịch."
        )

        return

    df = pd.DataFrame(transactions)

    if "amount" in df.columns:

        df["amount"] = pd.to_numeric(
            df["amount"],
            errors="coerce"
        )

    columns = [
        "id",
        "type",
        "amount",
        "category",
        "note",
        "date"
    ]

    columns = [
        c for c in columns
        if c in df.columns
    ]

    df = df[columns]

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# THỐNG KÊ
# =========================================================

def statistics():

    st.markdown(
        '<div class="title">📊 Thống kê</div>',
        unsafe_allow_html=True
    )

    transactions = get_transactions()

    if not transactions:

        st.info(
            "Chưa có dữ liệu để thống kê."
        )

        return

    df = pd.DataFrame(transactions)

    df["amount"] = pd.to_numeric(
        df["amount"],
        errors="coerce"
    )

    # -----------------------------------------------------
    # THU / CHI
    # -----------------------------------------------------

    income = df[
        df["type"] == "thu"
    ]["amount"].sum()

    expense = df[
        df["type"] == "chi"
    ]["amount"].sum()

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "💰 Tổng thu",
            f"{income:,.0f} đ"
        )

    with col2:

        st.metric(
            "💸 Tổng chi",
            f"{expense:,.0f} đ"
        )

    st.divider()

    # -----------------------------------------------------
    # CHI THEO DANH MỤC
    # -----------------------------------------------------

    expense_df = df[
        df["type"] == "chi"
    ]

    if not expense_df.empty:

        category_data = (
            expense_df
            .groupby("category")["amount"]
            .sum()
            .sort_values(ascending=False)
        )

        st.subheader(
            "💸 Chi tiêu theo danh mục"
        )

        st.bar_chart(
            category_data
        )

    # -----------------------------------------------------
    # THU / CHI
    # -----------------------------------------------------

    chart_data = pd.DataFrame(
        {
            "Loại": ["Thu", "Chi"],
            "Số tiền": [income, expense]
        }
    )

    st.subheader(
        "📊 Tổng quan thu chi"
    )

    st.bar_chart(
        chart_data.set_index("Loại")
    )


# =========================================================
# MAIN
# =========================================================

if not st.session_state.logged_in:

    login_page()

else:

    menu = sidebar()

    if menu == "🏠 Tổng quan":

        dashboard()

    elif menu == "💸 Thêm giao dịch":

        add_transaction()

    elif menu == "📷 Quét hóa đơn":

        scan_bill()

    elif menu == "📋 Lịch sử":

        history()

    elif menu == "📊 Thống kê":

        statistics()
```
