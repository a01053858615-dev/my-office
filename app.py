import streamlit as st
from st_gsheets_connection import GSheetsConnection
import pandas as pd
import hashlib
from datetime import datetime

# --- [설정] 본인의 구글 시트 주소 ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1nhrngvyO-L2Cwbvr_2-I-D1qwunYtB1WJuv9QBev8Nw/edit?usp=sharing".strip()

# 1. 페이지 설정 (반드시 모든 st 명령 중 가장 위에 와야 함)
st.set_page_config(page_title="시설 통합 관리 시스템", layout="wide")

# 2. 구글 시트 연결
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("GCP Secrets 설정을 확인해주세요.")
    st.stop()

# 3. 유틸리티 함수
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def get_data(worksheet_name):
    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet=worksheet_name, ttl=0)
        df = df.astype(str)
        for col in df.columns:
            df[col] = df[col].str.replace(r'\.0$', '', regex=True).str.strip()
        return df
    except:
        return pd.DataFrame()

# 4. 세션 상태 초기화
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None

# --- 메인 실행 함수 ---
def main():
    st.sidebar.title("🏢 시설 통합 관리 v2.0")

    if not st.session_state['logged_in']:
        # [로그인 화면]
        st.subheader("🔐 시스템 로그인")
        user_id = st.text_input("아이디(사번)")
        # 보안을 위해 비밀번호 암호화(해시) 없이 비교하도록 수정했습니다. 
        # 시트에 그냥 숫자나 문자로 비밀번호를 적어두시면 됩니다.
        user_pw = st.text_input("비밀번호", type='password')
        
        if st.button("접속하기", use_container_width=True):
            users_df = get_data("users")
            if not users_df.empty:
                # 시트에 적힌 비밀번호와 입력한 비밀번호를 그대로 비교합니다.
                match = users_df[(users_df['username'] == user_id.strip()) & 
                                 (users_df['password'] == user_pw.strip())]
                if not match.empty:
                    st.session_state['logged_in'] = True
                    st.session_state['user_info'] = match.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("아이디 또는 비밀번호가 틀렸습니다.")
            else:
                st.error("사용자 목록을 불러올 수 없습니다. 'users' 탭을 확인하세요.")

    else:
        # [로그인 후 대시보드]
        user = st.session_state['user_info']
        st.sidebar.success(f"✅ {user['name']}님 접속 중")
        if st.sidebar.button("로그아웃"):
            st.session_state['logged_in'] = False
            st.rerun()

        menu = st.sidebar.radio("메뉴 선택", ["⏰ 근태 관리", "🚛 올바로 계량 입력", "📊 기록 조회"])

        if menu == "⏰ 근태 관리":
            st.title("⏰ 근태 관리")
            today = datetime.now().strftime("%Y-%m-%d")
            st.info(f"📅 오늘 날짜: {today} | 현재 시간: {datetime.now().strftime('%H:%M:%S')}")
            # 근태 로직... (이후 필요시 추가)

        elif menu == "🚛 올바로 계량 입력":
            st.title("🚛 올바로 연계 계량 시스템")
            with st.form("weighing_form"):
                manifest_no = st.text_input("인계번호")
                gross = st.number_input("총중량(kg)", min_value=0)
                empty = st.number_input("공차중량(kg)", min_value=0)
                if st.form_submit_button("저장하기"):
                    st.success(f"계량 완료! 실중량: {gross - empty}kg")

        elif menu == "📊 기록 조회":
            st.title("📊 업무 기록 조회")
            st.dataframe(get_data("attendance"))

# --- 이 부분이 파일의 맨 왼쪽에 딱 붙어 있어야 합니다 ---
if __name__ == "__main__":
    main()
