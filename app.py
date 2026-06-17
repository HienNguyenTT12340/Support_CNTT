import streamlit as st
import gspread
import pandas as pd
from datetime import datetime

# 1. KẾT NỐI GOOGLE SHEETS BẰNG LINK (Đã mở quyền chỉnh sửa)
# Thay link Google Sheet của bạn vào đây
SHEET_URL = "https://docs.google.com/spreadsheets/d/1mySA4SihCcHY1lKO53tq0EiomDx1LUKkvRZgZLmPrnc/edit?gid=0#gid=0"

try:
    # Kết nối public không cần file JSON bảo mật
    gc = gspread.public_api()
    sh = gc.open_by_url(SHEET_URL)
    worksheet = sh.get_worksheet(0) # Lấy tab đầu tiên
except Exception:
    # Nếu chạy trên Streamlit Cloud, gspread cần xác thực ẩn bằng tài khoản anonymous
    gc = gspread.oauth_from_dict({}) 
    sh = gc.open_by_url(SHEET_URL)
    worksheet = sh.get_worksheet(0)

# Cấu hình giao diện Streamlit
st.set_page_config(page_title="IT Support", layout="wide")
st.title("💻 Hệ Thống Hỗ Trợ CNTT Tối Giản")

# Hàm đọc dữ liệu từ Sheet ra DataFrame
def get_data():
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

df = get_data()

# Chia 2 Tab: Người dùng và Admin
tab_user, tab_admin = st.tabs(["🙋 Gửi & Theo dõi", "🛠️ Quản trị viên"]) [cite: 11]

# ----------------------------------------------------
# TAB USER: GỬI VÀ XEM TRẠNG THÁI
# ----------------------------------------------------
with tab_user:
    st.header("Gửi yêu cầu mới")
    with st.form("form_request", clear_on_submit=True):
        user_name = st.text_input("Tên của bạn *")
        service_type = st.selectbox("Dịch vụ cần hỗ trợ", ["Cài phần mềm", "Lỗi phần cứng", "Mất mạng mạng", "Tài khoản/Email"])
        content = st.text_area("Chi tiết lỗi *")
        submit = st.form_submit_button("Gửi hỗ trợ")
        
    if submit:
        if user_name and content:
            ticket_id = f"IT-{int(datetime.now().timestamp())}"
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Ghi trực tiếp dòng mới xuống Google Sheets
            worksheet.append_row([ticket_id, user_name, service_type, content, "Chờ duyệt", created_at])
            st.success(f"Đã gửi! Mã số của bạn là: {ticket_id}")
            st.rerun()
        else:
            st.error("Vui lòng nhập đủ Tên và Chi tiết lỗi!")

    st.markdown("---")
    st.header("📋 Lịch sử yêu cầu")
    st.dataframe(df, use_container_width=True)

# ----------------------------------------------------
# TAB ADMIN: DUYỆT TRẠNG THÁI
# ----------------------------------------------------
with tab_admin:
    st.header("Xử lý yêu cầu")
    if df.empty:
        st.info("Chưa có dữ liệu.")
    else:
        # Chọn mã yêu cầu
        ticket_list = df["Mã Yêu Cầu"].tolist()
        selected_id = st.selectbox("Chọn mã yêu cầu cần duyệt:", ticket_list)
        
        # Tìm vị trí dòng trên Google Sheet (gspread tính từ dòng 1, cộng thêm 2 do có tiêu đề)
        row_idx = df[df["Mã Yêu Cầu"] == selected_id].index[0] + 2
        current_status = df.iloc[row_idx - 2]["Trạng Thái"]
        
        st.write(f"Yêu cầu từ: **{df.iloc[row_idx - 2]['Người Gửi']}** - Nội dung: {df.iloc[row_idx - 2]['Nội Dung']}")
        st.write(f"Trạng thái hiện tại: `{current_status}`")
        
        # Cập nhật trạng thái mới
        new_status = st.selectbox("Đổi trạng thái thành:", ["Chờ duyệt", "Đang xử lý", "Đã hoàn thành"])
        
        if st.button("Cập nhật ngay"):
            # Cột "Trạng Thái" là cột thứ 5 trong Google Sheets
            worksheet.update_cell(row_idx, 5, new_status)
            st.success(f"Đã cập nhật dòng {row_idx} thành {new_status}!")
            st.rerun()
