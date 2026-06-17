import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# ĐƯỜNG DẪN CẤU HÌNH (Thay thông tin của bạn vào đây)
# 1. Link Apps Script bạn vừa copy ở Bước 1
API_URL = "https://script.google.com/macros/s/AKfycbz_wIoCEjetiJ5j0D1CszZYWfYrYaQclM2lTlFl9Sr-oKI1wbNbObHtOwmgkDIJrKae/exec"

# 2. Link Google Sheets của bạn (Đổi đuôi /edit... thành /export?format=csv để đọc dữ liệu công khai)
SHEET_ID = "MÃ_ID_TRÊN_LINK_SHEET_CỦA_BẠN" 
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# Cấu hình giao diện
st.set_page_config(page_title="IT Support Portal", layout="wide")
st.title("💻 Hệ Thống Hỗ Trợ CNTT")

# Hàm đọc dữ liệu nhanh bằng Pandas
def load_data():
    try:
        # Thêm biến ngẫu nhiên để tránh Google trả về cache cũ khi làm mới
        return pd.read_csv(f"{CSV_URL}&nocache={int(datetime.now().timestamp())}")
    except Exception:
        return pd.DataFrame(columns=["Mã Yêu Cầu", "Người Gửi", "Loại Dịch Vụ", "Nội Dung", "Trạng Thái", "Ngày Tạo"])

df = load_data()

tab_user, tab_admin = st.tabs(["🙋 Gửi & Theo dõi", "🛠️ Quản trị viên"])

# ----------------------------------------------------
# TAB USER: GỬI YÊU CẦU
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
            
            # Gửi dữ liệu qua Apps Script để ghi vào Sheet
            payload = {
                "action": "append",
                "row": [ticket_id, user_name, service_type, content, "Chờ duyệt", created_at]
            }
            response = requests.post(API_URL, json=payload)
            
            if response.status_code == 200:
                st.success(f"Đã gửi thành công! Mã số: {ticket_id}")
                st.rerun()
            else:
                st.error("Có lỗi xảy ra khi kết nối dữ liệu!")
        else:
            st.error("Vui lòng điền đủ thông tin!")

    st.markdown("---")
    st.header("📋 Lịch sử yêu cầu")
    st.dataframe(df, use_container_width=True)

# ----------------------------------------------------
# TAB ADMIN: DUYỆT TRẠNG THÁI
# ----------------------------------------------------
with tab_admin:
    st.header("Xử lý yêu cầu")
    if df.empty or len(df) == 0:
        st.info("Chưa có dữ liệu yêu cầu nào.")
    else:
        ticket_list = df["Mã Yêu Cầu"].tolist()
        selected_id = st.selectbox("Chọn mã yêu cầu cần duyệt:", ticket_list)
        
        ticket_info = df[df["Mã Yêu Cầu"] == selected_id].iloc[0]
        st.write(f"Yêu cầu từ: **{ticket_info['Người Gửi']}** - Nội dung: {ticket_info['Nội Dung']}")
        st.write(f"Trạng thái hiện tại: `{ticket_info['Trạng Thái']}`")
        
        new_status = st.selectbox("Đổi trạng thái thành:", ["Chờ duyệt", "Đang xử lý", "Đã hoàn thành"])
        
        if st.button("Cập nhật ngay"):
            # Gửi lệnh cập nhật qua Apps Script
            payload = {
                "action": "update",
                "ticket_id": selected_id,
                "new_status": new_status
            }
            response = requests.post(API_URL, json=payload)
            
            if response.status_code == 200:
                st.success(f"Đã cập nhật trạng thái {selected_id} thành {new_status}!")
                st.rerun()
            else:
                st.error("Cập nhật thất bại!")
