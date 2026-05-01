import streamlit as st
import google.generativeai as genai
import urllib.parse
import json

# --- 1. CẤU HÌNH API ---
API_KEY = st.secrets["GEMINI_API_KEY"] # Lấy từ mục Secrets trên Streamlit Cloud
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. GIAO DIỆN ---
st.set_page_config(page_title="BEO to Google Calendar", page_icon="🏨")
st.title("🏨 BEO AI - Google Calendar Integration")

uploaded_file = st.file_uploader("Tải BEO (PDF/Ảnh)", type=["pdf", "png", "jpg", "jpeg"])

# --- 3. HÀM TẠO GOOGLE CALENDAR LINK ---
def create_google_url(ev):
    base_url = "https://www.google.com/calendar/render?action=TEMPLATE"
    
    # Định dạng ngày giờ: DD/MM/YYYY -> YYYYMMDD
    d = ev['Date'].split('/')
    date_iso = f"{d[2]}{d[1]}{d[0]}"
    
    # Giờ: HH:MM – HH:MM -> HHMMSS
    times = ev['Time'].split('–')
    start_t = times[0].strip().replace(":", "") + "00"
    end_t = times[1].strip().replace(":", "") + "00"
    
    dates = f"{date_iso}T{start_t}/{date_iso}T{end_t}"
    
    params = {
        "text": f"{ev['Function']} - {ev['End user']}",
        "dates": dates,
        "details": f"Company: {ev['Company']}\nSetup: {ev['Set up']}\nQuantity: {ev['Quantity']}\nTotal: {ev['Total Amount']}",
        "location": ev['Location'],
        "sf": "true",
        "output": "xml"
    }
    return base_url + "&" + urllib.parse.urlencode(params)

# --- 4. XỬ LÝ DỮ LIỆU ---
if uploaded_file:
    with st.spinner("AI đang tìm dòng TỔNG và trích xuất dữ liệu..."):
        # Cập nhật Prompt: Yêu cầu AI lấy từ dòng TỔNG / TOTAL
        prompt = """
        Phân tích BEO này và trả về JSON list 'events'. 
        
        YÊU CẦU QUAN TRỌNG:
        - KHÔNG tự tính toán giá tiền.
        - Tìm dòng 'TỔNG / TOTAL' hoặc dòng cuối cùng ghi số tiền tổng cộng của tài liệu để lấy 'Total Amount'.
        - Trích xuất: Date(DD/MM/YYYY), Time(HH:MM–HH:MM), Function, Location, Set up, Quantity, Company, End user.
        - Chỉ trả về JSON duy nhất.
        """
        
        file_data = uploaded_file.getvalue()
        response = model.generate_content([prompt, {"mime_type": uploaded_file.type, "data": file_data}])
        
        try:
            raw_text = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(raw_text)
            
            st.success("Đã trích xuất dữ liệu thành công!")
            
            for ev in data['events']:
                with st.expander(f"Chi tiết: {ev['Function']}", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"📅 **Ngày:** {ev['Date']}")
                        st.write(f"⏰ **Giờ:** {ev['Time']}")
                        st.write(f"🏢 **Đơn vị:** {ev['Company']}")
                    with col2:
                        st.write(f"📍 **Vị trí:** {ev['Location']}")
                        st.write(f"👥 **Số lượng:** {ev['Quantity']}")
                        st.write(f"💰 **Tổng cộng (Từ file):** {ev['Total Amount']}")
                    
                    st.link_button(f"➕ Add to Google Calendar", create_google_url(ev))
        except Exception as e:
            st.error(f"Lỗi: AI không tìm thấy cấu trúc JSON phù hợp hoặc dòng Tổng tiền.")
