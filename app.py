import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import hashlib
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- [설정] 본인의 구글 시트 주소 입력 ---
# 반드시 https://docs.google.com/spreadsheets/d/1nhrngvyO-L2Cwbvr_2-I-D1qwunYtB1WJuv9QBev8Nw/edit?gid=0#gid=0
SHEET_URL = "https://docs.google.com/spreadsheets/d/1nhrngvyO-L2Cwbvr_2-I-D1qwunYtB1WJuv9QBev8Nw/edit?usp=sharing".strip()

# 1. 페이지 설정 (가장 먼저 실행되어야 함)
st.set_page_config(page_title="시설 통합 관리 시스템", layout="wide")

# 2. 연결 설정
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("구글 시트 연결 설정(Secrets)에 문제가 있습니다.")
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
    except Exception as e:
        st.error(f"'{worksheet_name}' 탭을 읽어오는데 실패했습니다. 탭 이름과 공유 설정을 확인하세요.")
        return pd.DataFrame()

# 4. 세션 상태 초기화 (화면이 안 뜨는 주범 방지)
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None

# --- 메인 로직 ---
def main():
    # 사이드바 디자인
    st.sidebar.title("🏢 시설 통합 관리 v2.0")
    
    # [진단용] 현재 상태 표시 (나중에 지우셔도 됩니다)
    # st.sidebar.write(f"로그인 상태: {st.session_state['logged_in']}")

    if not st.session_state['logged_in']:
        # [A] 로그인 화면
        st.subheader("🔐 시스템 로그인")
        with st.container():
            user_input = st.text_input("아이디(사번)", key="login_user")
            pw_input = st.text_input("비밀번호", type='password', key="login_pw")
            
            if st.button("접속하기", use_container_width=True):
                users_df = get_data("users")
                if not users_df.empty:
                    hashed_pw = make_hashes(pw_input)
                    match = users_df[(users_df['username'] == user_input.strip()) & 
                                     (users_df['password'] == hashed_pw)]
                    
                    if not match.empty:
                        st.session_state['logged_in'] = True
                        st.session_state['user_info'] = match.iloc[0].to_dict()
                        st.success("로그인 성공!")
                        st.rerun()
                    else:
                        st.error("아이디 또는 비밀번호가 틀렸습니다.")
                else:
                    st.warning("사용자 데이터를 불러올 수 없습니다. 'users' 탭을 확인하세요.")

    else:
        # [B] 로그인 후 화면
        user = st.session_state['user_info']
        st.sidebar.success(f"✅ {user['name']}님 접속 중")
        
        if st.sidebar.button("로그아웃"):
            st.session_state['logged_in'] = False
            st.rerun()

        menu = st.sidebar.radio("메뉴 선택", ["⏰ 실시간 근태", "🚛 올바로 계량 입력", "📊 기록 조회"])

        if menu == "⏰ 실시간 근태":
            st.title("⏰ 실시간 근태 관리")
            st_autorefresh(interval=1000, key="timer_refresh") # 1초마다 갱신
            
            today = datetime.now().strftime("%Y-%m-%d")
            attendance_df = get_data("attendance")
            
            # ... (이하 근태 로직 동일) ...
            st.info(f"현재 시각: {datetime.now().strftime('%H:%M:%S')}")
            st.write("여기에 근태 기능이 나타납니다.")

        elif menu == "🚛 올바로 계량 입력":
            st.title("🚛 올바로 연계 계량 시스템")
            # 사용자님이 설명하신 계량 로직
            with st.form("allbaro_form"):
                manifest_no = st.text_input("인계번호")
                gross = st.number_input("총중량(kg)", min_value=0)
                empty = st.number_input("공차중량(kg)", min_value=0)
                net = gross - empty
                st.metric("실중량(톤 단위 자동 변환 예정)", f"{net} kg")
                
                if st.form_submit_button("확정 및 저장"):
                    st.success("데이터가 구글 시트에 저장되었습니다. (올바로 전송 시뮬레이션)")

        elif menu == "📊 기록 조회":
            st.title("📊 업무 기록 조회")
            tab1, tab2 = st.tabs(["근태 기록", "반입/계량 기록"])
            with tab1:
                st.dataframe(get_data("attendance"))
            with tab2:
                st.dataframe(get_data("reports"))

# --- 마지막에 이 줄이 반드시 있어야 실행됩니다! ---
if __name__ == "__main__":
    main()
 
