import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import datetime
import json
import io

# --- 1. CẤU HÌNH API ---
# Thay API Key của bạn vào đây
API_KEY = st.secrets["AIzaSyAWVJemE1vdVllQdp8m4B8wlo886aMjFvI"] 
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. GIAO DIỆN WEB ---
st.set_page_config(page_title="BEO to Outlook Converter", layout="wide")
st.title("🏨 BEO AI Converter")
st.subheader("Trích xuất lịch sự kiện từ PDF/Ảnh sang file Outlook (.ics)")

uploaded_file = st.file_uploader("Tải file BEO (PDF hoặc Ảnh chụp)", type=["pdf", "png", "jpg", "jpeg"])

# --- 3. LOGIC XỬ LÝ ---
def generate_ics(events):
    """Tạo nội dung file .ics chuẩn"""
    ics = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//BEO AI//VN", "CALSCALE:GREGORIAN", "METHOD:PUBLISH"]
    for ev in events:
        try:
            # Xử lý ngày giờ
            date_str = ev['Date'].replace("/", "")
            start_time = ev['Time'].split("–")[0].strip().replace(":", "")
            end_time = ev['Time'].split("–")[1].strip().replace(":", "")
            
            dtstart = f"{date_str[4:]}{date_str[2:4]}{date_str[:2]}T{start_time}00"
            dtend = f"{date_str[4:]}{date_str[2:4]}{date_str[:2]}T{end_time}00"
            
            ics.append("BEGIN:VEVENT")
            ics.append(f"SUMMARY:{ev['Function']} - {ev['End user']}")
            ics.append(f"DTSTART:{dtstart}")
            ics.append(f"DTEND:{dtend}")
            ics.append(f"LOCATION:{ev['Location']}")
            desc = f"Setup: {ev['Set up']}\\nQuantity: {ev['Quantity']}\\nTotal: {ev['Total Amount']}\\nCompany: {ev['Company']}"
            ics.append(f"DESCRIPTION:{desc}")
            # Nhắc nhở 8h sáng
            ics.append("BEGIN:VALARM")
            ics.append(f"TRIGGER;VALUE=DATE-TIME:{dtstart[:8]}T080000")
            ics.append("ACTION:DISPLAY")
            ics.append("DESCRIPTION:Nhắc nhở sự kiện BEO hôm nay")
            ics.append("END:VALARM")
            ics.append("END:VEVENT")
        except:
            continue
    ics.append("END:VCALENDAR")
    return "\n".join(ics)

if uploaded_file:
    with st.spinner("AI đang đọc dữ liệu BEO..."):
        # Chuyển đổi file để AI đọc
        if uploaded_file.type == "application/pdf":
            reader = PdfReader(uploaded_file)
            content = " ".join([page.extract_text() for page in reader.pages])
        else:
            content = uploaded_file.getvalue() # Nếu là ảnh

        prompt = """
        Phân tích BEO này và trả về JSON list 'events'. 
        Các trường: Date(DD/MM/YYYY), Time(HH:MM–HH:MM), Function, Location, Set up, Quantity, Company, End user.
        Tính 'Total Amount' = Price * Quantity. Chỉ trả về JSON.
        """
        
        response = model.generate_content([prompt, uploaded_file] if uploaded_file.type != "application/pdf" else [prompt, content])
        
        try:
            data = json.loads(response.text.replace("```json", "").replace("```", ""))
            st.success("Đã trích xuất thành công!")
            st.table(data['events'])
            
            ics_data = generate_ics(data['events'])
            st.download_button("⬇️ Tải file .ics cho Outlook", ics_data, file_name="BEO_Schedule.ics", mime="text/calendar")
        except:
            st.error("AI không thể đọc được cấu trúc file này. Hãy thử chụp ảnh rõ hơn.")
