import streamlit as st
from streamlit_gsheets import GSheetsConnection

# 주소 대신 시트 제목을 적어보세요
SHEET_TITLE = "시설관리DB" # 본인의 시트 제목으로 수정

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # spreadsheet 매개변수에 주소 대신 제목을 넣어봅니다.
    df = conn.read(spreadsheet=SHEET_TITLE, worksheet="users", ttl=0)
    st.success("✅ 드디어 연결 성공!")
    st.write(df)
except Exception as e:
    st.error("❌ 아직 시트를 찾지 못했습니다.")
    st.write(e)
