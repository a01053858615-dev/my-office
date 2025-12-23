import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. 구글 시트 연결 설정
# 시트 주소에 아까 복사한 본인의 구글 시트 링크를 넣어주세요
url = "여기에_복사한_구글시트_링크를_넣으세요"
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("📋 업무 보고 및 저장 시스템")

# 2. 데이터 불러오기 표시
st.subheader("현재 저장된 기록")
existing_data = conn.read(spreadsheet=url, usecols=[0,1,2,3,4])
st.dataframe(existing_data)

# 3. 데이터 입력 폼
st.subheader("새 보고서 작성")
with st.form(key="report_form"):
    date = st.date_input("날짜")
    author = st.text_input("작성자")
    title = st.text_input("제목")
    content = st.text_area("내용")
    
    submit_button = st.form_submit_button(label="보고서 제출")

    if submit_button:
        # 새로운 데이터를 표 형태로 만듦
        new_data = pd.DataFrame([{
            "날짜": str(date),
            "작성자": author,
            "제목": title,
            "내용": content,
            "결재상태": "대기"
        }])
        
        # 기존 데이터에 추가
        updated_df = pd.concat([existing_data, new_data], ignore_index=True)
        
        # 구글 시트에 다시 쓰기
        conn.update(spreadsheet=url, data=updated_df)
        st.success("데이터가 구글 시트에 영구 저장되었습니다!")
        st.rerun()
