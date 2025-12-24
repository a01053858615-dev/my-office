import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import hashlib
from datetime import datetime
import requests # API 통신용
import base64   # 올바로 인증용

# --- [설정] ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1nhrngvyO-L2Cwbvr_2-I-D1qwunYtB1WJuv9QBev8Nw/edit"
ALLBARO_API_URL = "https://연계서버주소/T400_5001_01" # 정의서 30.csv 기준
API_CERT_KEY = "발급받은_인증키" # 정의서 Request Body 1번 항목

# 1. 연결 설정
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. 유틸리티 함수
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def get_data(worksheet_name):
    df = conn.read(spreadsheet=SHEET_URL, worksheet=worksheet_name, ttl=0)
    return df.astype(str).replace(r'\.0$', '', regex=True)

# --- [핵심] 올바로 API 전송 함수 (인터페이스 30.csv 규격) ---
def send_to_allbaro(data):
    # 정의서 Header 1번: Basic Auth 생성
    auth_str = f"아이디:비밀번호"
    encoded_auth = base64.b64encode(auth_str.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {encoded_auth}",
        "Content-Type": "application/json;charset=utf-8"
    }
    
    # 정의서 Request Body 규격에 맞춘 데이터 구성
    payload = {
        "API_CERT_KEY": API_CERT_KEY,
        "ENTN_LKCD": "우리업체코드",   # 정의서 2번
        "MANF_NUMS": data['인계번호'], # 정의서 3번
        "RECV_QUNT": str(data['실중량']), # 정의서 6번
        "FULL_QUNT": str(data['총중량']), # 정의서 13번
        "EMTY_QUNT": str(data['공차중량']), # 정의서 15번
        "LOAD_QUNT": str(data['실중량']), # 정의서 16번
        "MANB_TYPE": "3" # 3:인수등록 (정의서 18번)
    }
    
    # 실제 전송 (주석 해제 시 작동)
    # response = requests.put(ALLBARO_API_URL, json=payload, headers=headers)
    # return response.json()
    return {"RESULT_CODE": "0000", "RESULT_MESSAGE": "처리완료(시뮬레이션)"}

# --- 메인 화면 로직 ---
def main():
    st.sidebar.title("🔥 시설 통합 관리 v2.0")
    
    # (로그인 로직 생략 - 이전과 동일)
    # ... 

    # 메뉴 구성 (올바로 기능 추가)
    main_menu = st.sidebar.radio("업무 선택", ["⏰ 근태 관리", "🚛 반입 및 계량(올바로)", "📊 기록 조회"])

    if main_menu == "⏰ 근태 관리":
        # (이전의 실시간 타이머 코드 삽입)
        st.title("⏰ 실시간 근태 관리")
        # ...

    elif main_menu == "🚛 반입 및 계량(올바로)":
        st.title("🚛 폐기물 반입 및 확정 입력")
        st.info("올바로시스템 '신규자료'를 기반으로 계량 정보를 입력합니다.")

        with st.form("allbaro_weighing_form"):
            col1, col2 = st.columns(2)
            with col1:
                manifest_no = st.text_input("인계번호 (배출자 작성)")
                car_no = st.text_input("차량번호")
                waste_type = st.selectbox("폐기물 종류", ["폐합성수지", "폐유", "기타"])
            
            with col2:
                # 사용자님이 강조한 '계량시설' 입력창
                gross_weight = st.number_input("총중량 (kg) - 적재함 포함", min_value=0)
                empty_weight = st.number_input("공차중량 (kg) - 빈 차량", min_value=0)
                net_weight = gross_weight - empty_weight
                st.metric("계산된 실중량 (kg)", f"{net_weight:,}")

            memo = st.text_area("특이사항")
            
            submit = st.form_submit_button("⚖️ 계량 확정 및 올바로 전송")

            if submit:
                # 1. 올바로 API 전송 시도
                result = send_to_allbaro({
                    '인계번호': manifest_no,
                    '총중량': gross_weight,
                    '공차중량': empty_weight,
                    '실중량': net_weight
                })

                if result['RESULT_CODE'] == "0000":
                    # 2. 구글 시트(기존자료/보관량) 저장
                    reports_df = get_data("reports")
                    new_entry = pd.DataFrame([{
                        "날짜": datetime.now().strftime("%Y-%m-%d"),
                        "인계번호": manifest_no,
                        "차량번호": car_no,
                        "종류": waste_type,
                        "실중량": net_weight,
                        "상태": "확정완료(올바로전송)"
                    }])
                    updated_df = pd.concat([reports_df, new_entry], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet="reports", data=updated_df)
                    
                    st.success(f"✅ 올바로 확정 성공! (인계번호: {manifest_no})")
                    st.balloons()
                else:
                    st.error(f"❌ 올바로 전송 실패: {result['RESULT_MESSAGE']}")

    elif main_menu == "📊 기록 조회":
        st.title("📊 통합 기록 대시보드")
        # 구글 시트 데이터를 가져와서 잔량 계산 시각화 가능
        # ...
