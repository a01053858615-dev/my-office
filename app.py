import streamlit as st
from streamlit_gsheets import GSheetsConnection

# 1. 주소 설정
SHEET_URL = "1nhrngvyO-L2Cwbvr_2-I-D1qwunYtB1WJuv9QBev8Nw"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    st.title("🔍 시스템 연결 진단")
    
    # 2. 데이터 한 번 읽어보기 테스트
    df = conn.read(spreadsheet=SHEET_URL, worksheet="users", ttl=0)
    
    st.success("✅ 구글 시트 연결 성공!")
    st.write("불러온 유저 목록:", df)
    
except Exception as e:
    st.error("❌ 연결 중 오류 발생")
    st.exception(e)
