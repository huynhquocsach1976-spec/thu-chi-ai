import os
import requests
import pandas as pd
import streamlit as st


# =========================================================
# CẤU HÌNH
# =========================================================

st.set_page_config(
    page_title="Thu Chi AI Pro",
    page_icon="💰",
    layout="wide"
)

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "https://thu-chi-ai.onrender.com"
).rstrip("/")


# =========================================================
# SESSION STATE
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "username" not in st.session_state:
    st.session_state.username = ""

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"


# =========================================================
# HÀM GỌI API
# =========================================================

def api_post(endpoint, data=None, files=None):

    try:

        url = BACKEND_URL + endpoint

        response = requests.post(
            url,
            json=data,
            files=files,
            timeout=120
        )

        try:
            result = response.json()
        except Exception:
            result = response.text

        if response.ok:
            return result, None

        # Lấy detail của FastAPI
        if isinstance(result, dict):
            error = result.get("detail")

            if error:
                if isinstance(error, list):
                    error = "; ".join(
                        str(x)
                        for x in error
                    )

                return None, str(error)

        return None, str(result)

    except requests.exceptions.Timeout:
        return None, "Backend phản hồi quá lâu. Vui lòng thử lại."

    except requests.exceptions.ConnectionError:
        return None, "Không kết nối được Backend."

    except Exception as e:
        return None, str(e)


def api_get(endpoint):

    try:

        url = BACKEND_URL + endpoint

        response = requests.get(
            url,
            timeout=120
        )

        try:
            result = response.json()
        except Exception:
            result = response.text

        if response.ok:
            return result, None

        if isinstance(result, dict):

            error = result.get("detail")

            if error:

                if isinstance(error, list):
                    error = "; ".join(
                        str(x)
                        for x in error
                    )

                return None, str(error)

        return None, str(result)

    except requests.exceptions.Timeout:
        return None, "Backend phản hồi quá lâu."

    except requests.exceptions.ConnectionError:
        return None, "Không kết nối được Backend."

    except Exception as e:
        return None, str(e)


# =========================================================
# HÀM FORMAT TIỀN
# =========================================================

def format_money(value):

    try:
        value = float(value)

        return f"{value:,.0f} ₫".replace(
            ",",
            "."
        )

    except Exception:
        return "0 ₫"


# =========================================================
# LẤY DATA GIAO DỊCH
# =========================================================

def get_transactions():

    user_id = st.session_state.user_id

    if not user_id:
        return []

    result, error = api_get(
        f"/transactions/{user_id}"
    )

    if error:
        st.error(error)
        return []

    if not isinstance(result, dict):
        return []

    data = result.get("data", [])

    if isinstance(data, list):
        return data

    return []


# =========================================================
# ĐĂNG NHẬP / ĐĂNG KÝ
# =========================================================

def login_page():

    st.title("💰 Thu Chi AI Pro")

    st.subheader("🔐 Đăng nhập")

    username = st.text_input(
        "Tên đăng nhập",
        key="login_username"
    )

    password = st.text_input(
        "Mật khẩu",
        type="password",
        key="login_password"
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "🔐 Đăng nhập",
            use_container_width=True
        ):

            if not username or not password:

                st.warning(
                    "Vui lòng nhập đầy đủ thông tin."
                )

            else:

                result, error = api_post(
                    "/login",
                    {
                        "username": username,
                        "password": password
                    }
                )

                if error:

                    st.error(error)

                else:

                    st.session_state.logged_in = True

                    st.session_state.user_id = result.get(
                        "user_id"
                    )

                    st.session_state.username = result.get(
                        "username",
                        username
                    )

                    st.session_state.page = "Dashboard"

                    st.success(
                        "Đăng nhập thành công!"
                    )

                    st.rerun()

    with col2:

        if st.button(
            "📝 Đăng ký",
            use_container_width=True
        ):
            st.session_state.page = "Đăng ký"
            st.rerun()


def register_page():

    st.title("📝 Đăng ký tài khoản")

    username = st.text_input(
        "Tên đăng nhập",
        key="register_username"
    )

    password = st.text_input(
        "Mật khẩu",
        type="password",
        key="register_password"
    )

    password2 = st.text_input(
        "Nhập lại mật khẩu",
        type="password",
        key="register_password2"
    )

    if st.button(
        "📝 Tạo tài khoản",
        use_container_width=True
    ):

        if not username or not password:

            st.warning(
                "Vui lòng nhập đầy đủ thông tin."
            )

        elif password != password2:

            st.error(
                "Mật khẩu nhập lại không giống nhau."
            )

        else:

            result, error = api_post(
                "/register",
                {
                    "username": username,
                    "password": password
                }
            )

            if error:

                st.error(error)

            else:

                st.success(
                    "Đăng ký thành công! Hãy đăng nhập."
                )

                st.session_state.page = "Đăng nhập"

                st.rerun()

    if st.button("⬅️ Quay lại đăng nhập"):

        st.session_state.page = "Đăng nhập"

        st.rerun()


# =========================================================
# SIDEBAR
# =========================================================

def sidebar():

    with st.sidebar:

        st.title("💰 Thu Chi AI Pro")

        st.write(
            f"Xin chào **{st.session_state.username}** 👋"
        )

        st.divider()

        if st.button(
            "🏠 Dashboard",
            use_container_width=True
        ):
            st.session_state.page = "Dashboard"
            st.rerun()

        if st.button(
            "🤖 Nhập giao dịch AI",
            use_container_width=True
        ):
            st.session_state.page = "AI"
            st.rerun()

        if st.button(
            "📷 Quét hóa đơn",
            use_container_width=True
        ):
            st.session_state.page = "Scan"
            st.rerun()

        if st.button(
            "📋 Lịch sử giao dịch",
            use_container_width=True
        ):
            st.session_state.page = "History"
            st.rerun()

        st.divider()

        if st.button(
            "🚪 Đăng xuất",
            use_container_width=True
        ):

            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.username = ""
            st.session_state.page = "Đăng nhập"

            st.rerun()


# =========================================================
# DASHBOARD
# =========================================================

def dashboard_page():

    st.title("🏠 Dashboard")

    st.write(
        f"Xin chào **{st.session_state.username}** 👋"
    )

    transactions = get_transactions()

    if not transactions:

        st.info(
            "Chưa có giao dịch nào."
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "💰 Tổng thu",
                "0 ₫"
            )

        with col2:
            st.metric(
                "💸 Tổng chi",
                "0 ₫"
            )

        with col3:
            st.metric(
                "📋 Giao dịch",
                0
            )

        return

    df = pd.DataFrame(
        transactions
    )

    if "transaction_type" not in df.columns:
        df["transaction_type"] = "chi"

    if "amount" not in df.columns:
        df["amount"] = 0

    df["amount"] = pd.to_numeric(
        df["amount"],
        errors="coerce"
    ).fillna(0)

    total_income = df.loc[
        df["transaction_type"] == "thu",
        "amount"
    ].sum()

    total_expense = df.loc[
        df["transaction_type"] == "chi",
        "amount"
    ].sum()

    balance = total_income - total_expense

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "💰 Tổng thu",
            format_money(total_income)
        )

    with col2:

        st.metric(
            "💸 Tổng chi",
            format_money(total_expense)
        )

    with col3:

        st.metric(
            "💵 Số dư",
            format_money(balance)
        )

    with col4:

        st.metric(
            "📋 Giao dịch",
            len(df)
        )

    st.divider()

    st.subheader(
        "📊 Thống kê thu chi"
    )

    chart_data = pd.DataFrame(
        {
            "Loại": [
                "Thu",
                "Chi"
            ],
            "Số tiền": [
                total_income,
                total_expense
            ]
        }
    )

    st.bar_chart(
        chart_data.set_index("Loại")
    )

    st.subheader(
        "📋 Giao dịch gần đây"
    )

    display_transactions(
        transactions[:10]
    )


# =========================================================
# HIỂN THỊ GIAO DỊCH
# =========================================================

def display_transactions(transactions):

    if not transactions:

        st.info(
            "Chưa có giao dịch nào."
        )

        return

    rows = []

    for item in transactions:

        transaction_type = item.get(
            "transaction_type",
            ""
        )

        if transaction_type == "thu":
            type_display = "💰 Thu"
        else:
            type_display = "💸 Chi"

        rows.append(
            {
                "Loại": type_display,
                "Số tiền": format_money(
                    item.get("amount", 0)
                ),
                "Nội dung": item.get(
                    "description",
                    ""
                ),
                "Danh mục": item.get(
                    "category",
                    ""
                ),
                "Ngày": item.get(
                    "transaction_date",
                    ""
                )
            }
        )

    df = pd.DataFrame(rows)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# NHẬP GIAO DỊCH BẰNG AI
# =========================================================

def ai_transaction_page():

    st.title("🤖 Nhập giao dịch bằng AI")

    st.write(
        "Bạn chỉ cần nhập câu tự nhiên, AI sẽ tự phân tích."
    )

    st.info(
        "Ví dụ: Ăn cơm 50 nghìn"
    )

    st.info(
        "Ví dụ: Mua xăng 100 nghìn"
    )

    st.info(
        "Ví dụ: Nhận lương 15 triệu"
    )

    text = st.text_area(
        "Nội dung giao dịch",
        placeholder="Ví dụ: Ăn cơm 50 nghìn"
    )

    if st.button(
        "🤖 Phân tích và lưu",
        use_container_width=True
    ):

        if not text.strip():

            st.warning(
                "Vui lòng nhập nội dung giao dịch."
            )

            return

        with st.spinner(
            "AI đang phân tích..."
        ):

            result, error = api_post(
                "/add-transaction-ai",
                {
                    "user_id": st.session_state.user_id,
                    "text": text
                }
            )

        if error:

            st.error(
                "❌ Lỗi xử lý giao dịch AI: "
                + str(error)
            )

        else:

            st.success(
                "✅ Đã thêm giao dịch thành công!"
            )

            data = result.get(
                "data",
                {}
            )

            if isinstance(data, dict):

                col1, col2 = st.columns(2)

                with col1:

                    st.write(
                        "**Loại:** "
                        + str(
                            data.get(
                                "transaction_type",
                                ""
                            )
                        )
                    )

                    st.write(
                        "**Số tiền:** "
                        + format_money(
                            data.get(
                                "amount",
                                0
                            )
                        )
                    )

                with col2:

                    st.write(
                        "**Nội dung:** "
                        + str(
                            data.get(
                                "description",
                                ""
                            )
                        )
                    )

                    st.write(
                        "**Danh mục:** "
                        + str(
                            data.get(
                                "category",
                                ""
                            )
                        )
                    )


# =========================================================
# QUÉT HÓA ĐƠN
# =========================================================

def scan_bill_page():

    st.title("📷 Quét hóa đơn bằng AI")

    st.write(
        "Tải ảnh hóa đơn lên, AI sẽ đọc thông tin và lưu giao dịch."
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

    if uploaded_file is not None:

        st.image(
            uploaded_file,
            caption="Hóa đơn đã chọn",
            use_container_width=True
        )

        if st.button(
            "🔍 Quét hóa đơn",
            use_container_width=True
        ):

            with st.spinner(
                "AI đang đọc hóa đơn..."
            ):

                try:

                    # Quan trọng:
                    # Đưa file về bytes trước khi gửi.
                    file_bytes = uploaded_file.getvalue()

                    files = {
                        "file": (
                            uploaded_file.name,
                            file_bytes,
                            uploaded_file.type
                            or "image/jpeg"
                        )
                    }

                    url = BACKEND_URL + "/scan-bill"

                    response = requests.post(
                        url,
                        params={
                            "user_id": st.session_state.user_id
                        },
                        files=files,
                        timeout=180
                    )

                    try:
                        result = response.json()
                    except Exception:
                        result = {
                            "detail": response.text
                        }

                    if not response.ok:

                        error = result.get(
                            "detail",
                            "Không xác định được lỗi."
                        )

                        # FIX lỗi list + string
                        if isinstance(error, list):

                            error = "; ".join(
                                str(x)
                                for x in error
                            )

                        st.error(
                            "❌ Lỗi xử lý ảnh: "
                            + str(error)
                        )

                    else:

                        st.success(
                            "✅ Đã quét hóa đơn thành công!"
                        )

                        data = result.get(
                            "data",
                            {}
                        )

                        # Đảm bảo data luôn là dictionary
                        if not isinstance(
                            data,
                            dict
                        ):
                            data = {}

                        col1, col2 = st.columns(2)

                        with col1:

                            st.write(
                                "### 📄 Thông tin hóa đơn"
                            )

                            st.write(
                                "**Cửa hàng:** "
                                + str(
                                    data.get(
                                        "merchant",
                                        ""
                                    )
                                )
                            )

                            st.write(
                                "**Ngày:** "
                                + str(
                                    data.get(
                                        "date",
                                        ""
                                    )
                                )
                            )

                            st.write(
                                "**Danh mục:** "
                                + str(
                                    data.get(
                                        "category",
                                        "Khác"
                                    )
                                )
                            )

                        with col2:

                            st.write(
                                "### 💰 Giao dịch"
                            )

                            st.write(
                                "**Loại:** "
                                + str(
                                    data.get(
                                        "transaction_type",
                                        "chi"
                                    )
                                )
                            )

                            st.write(
                                "**Số tiền:** "
                                + format_money(
                                    data.get(
                                        "amount",
                                        0
                                    )
                                )
                            )

                            st.write(
                                "**Nội dung:** "
                                + str(
                                    data.get(
                                        "description",
                                        ""
                                    )
                                )
                            )

                        if data.get(
                            "saved",
                            False
                        ):

                            st.success(
                                "💾 Giao dịch đã được lưu vào hệ thống."
                            )

                        else:

                            st.warning(
                                "⚠️ AI đọc được hóa đơn nhưng chưa xác định được số tiền nên chưa lưu giao dịch."
                            )

                except requests.exceptions.Timeout:

                    st.error(
                        "❌ Backend xử lý quá lâu. Vui lòng thử lại."
                    )

                except requests.exceptions.ConnectionError:

                    st.error(
                        "❌ Không kết nối được Backend."
                    )

                except Exception as e:

                    st.error(
                        "❌ Lỗi xử lý ảnh: "
                        + str(e)
                    )


# =========================================================
# LỊCH SỬ
# =========================================================

def history_page():

    st.title("📋 Lịch sử giao dịch")

    transactions = get_transactions()

    if not transactions:

        st.info(
            "Chưa có giao dịch nào."
        )

        return

    display_transactions(
        transactions
    )


# =========================================================
# MAIN
# =========================================================

if not st.session_state.logged_in:

    if st.session_state.page == "Đăng ký":

        register_page()

    else:

        login_page()

else:

    sidebar()

    if st.session_state.page == "Dashboard":

        dashboard_page()

    elif st.session_state.page == "AI":

        ai_transaction_page()

    elif st.session_state.page == "Scan":

        scan_bill_page()

    elif st.session_state.page == "History":

        history_page()

    else:

        dashboard_page()
