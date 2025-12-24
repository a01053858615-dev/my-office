import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import hashlib
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- [설정] 본인의 구글 시트 주소 입력 ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1nhrngvyO-L2Cwbvr_2-I-D1qwunYtB1WJuv9QBev8Nw/edit?usp=sharing".strip()

# 1. 페이지 설정 (가장 먼저 실행)
st.set_page_config(page_title="시설 통합 관리 시스템", layout="wide")

# 2. 다우오피스 스타일 디자인 입히기 (CSS)
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .stButton>button {
        border-radius: 5px; border: 1px solid #007bff;
        background-color: #ffffff; color: #007bff; font-weight: bold;
    }
    .stButton>button:hover { background-color: #007bff; color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

# 3. 연결 및 데이터 처리 함수
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("구글 시트 연결 설정에 문제가 있습니다.")
    st.stop()

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
        st.error(f"'{worksheet_name}' 탭을 읽지 못했습니다.")
        return pd.DataFrame()

# 4. 세션 상태 초기화
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None

# --- 메인 로직 ---
def main():
    st.sidebar.title("🏢 시설 통합 관리 v2.0")

    if not st.session_state['logged_in']:
        # [로그인 화면]
        st.subheader("🔐 시스템 로그인")
        user_input = st.text_input("아이디(사번)")
        pw_input = st.text_input("비밀번호", type='password')
        
        if st.button("접속하기", use_container_width=True):
            users_df = get_data("users")
            if not users_df.empty:
                hashed_pw = make_hashes(pw_input)
                match = users_df[(users_df['username'] == user_input.strip()) & 
                                 (users_df['password'] == hashed_pw)]
                if not match.empty:
                    st.session_state['logged_in'] = True
                    st.session_state['user_info'] = match.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("아이디 또는 비밀번호가 틀렸습니다.")

    else:
        # [로그인 후 화면]
        user = st.session_state['user_info']
        st.sidebar.success(f"✅ {user['name']}님 접속 중")
        if st.sidebar.button("로그아웃"):
            st.session_state['logged_in'] = False
            st.rerun()

        menu = st.sidebar.radio("메뉴 선택", ["⏰ 실시간 근태", "🚛 올바로 계량 입력", "📊 기록 조회"])

        # 1. 근태 관리 (실시간 타이머 포함)
        if menu == "⏰ 실시간 근태":
            st.title("⏰ 실시간 근태 관리")
            st_autorefresh(interval=1000, key="timer_refresh") # 1초 자동 갱신
            
            today = datetime.now().strftime("%Y-%m-%d")
            now_dt = datetime.now()
            
            attendance_df = get_data("attendance")
            my_record = attendance_df[(attendance_df['date'] == today) & (attendance_df['username'] == user['username'])]

            st.info(f"📅 오늘: {today} | ⌚ 현재: {now_dt.strftime('%H:%M:%S')}")

            if my_record.empty:
                if st.button("🚀 출근하기", use_container_width=True):
                    new_att = pd.DataFrame([{"date": today, "username": user['username'], "name": user['name'], "clock_in": now_dt.strftime('%H:%M:%S'), "clock_out": "", "total_hours": ""}])
                    updated_att = pd.concat([attendance_df, new_att], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet="attendance", data=updated_att)
                    st.rerun()
            elif my_record.iloc[0]['clock_out'] == "":
                c_in_dt = datetime.strptime(f"{today} {my_record.iloc[0]['clock_in']}", "%Y-%m-%d %H:%M:%S")
                diff = datetime.now() - c_in_dt
                st.success(f"✅ 출근 완료: {my_record.iloc[0]['clock_in']}")
                st.metric("⏳ 현재 업무 지속 시간", str(diff).split('.')[0])
                
                if st.button("🏁 퇴근하기", use_container_width=True):
                    attendance_df.loc[(attendance_df['date'] == today) & (attendance_df['username'] == user['username']), 'clock_out'] = now_dt.strftime("%H:%M:%S")
                    duration = diff.total_seconds() / 3600
                    attendance_df.loc[(attendance_df['date'] == today) & (attendance_df['username'] == user['username']), 'total_hours'] = f"{duration:.2f}"
                    conn.update(spreadsheet=SHEET_URL, worksheet="attendance", data=attendance_df)
                    st.balloons()
                    st.rerun()
            else:
                st.info("오늘 업무를 마쳤습니다!")

        # 2. 올바로 계량 입력 (인터페이스 정의서 30.csv 로직 반영)
        elif menu == "🚛 올바로 계량 입력":
            st.title("🚛 올바로 연계 계량 시스템")
            with st.form("allbaro_form"):
                col1, col2 = st.columns(2)
                with col1:
                    manifest_no = st.text_input("인계번호 (MANF_NUMS)")
                    car_no = st.text_input("차량번호 (TRAN_NUMS)")
                with col2:
                    gross = st.number_input("총중량(kg)", min_value=0)
                    empty = st.number_input("공차중량(kg)", min_value=0)
                
                net = gross - empty
                st.metric("실중량 (LOAD_QUNT)", f"{net} kg")
                
                if st.form_submit_button("⚖️ 계량 확정 및 저장"):
                    reports_df = get_data("reports")
                    new_report = pd.DataFrame([{
                        "날짜": today, "인계번호": manifest_no, "차량번호": car_no, 
                        "총중량": gross, "공차중량": empty, "실중량": net, "상태": "확정(올바로대기)"
                    }])
                    updated_reports = pd.concat([reports_df, new_report], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet="reports", data=updated_reports)
                    st.success("계량 데이터가 구글 시트에 기록되었습니다.")

        # 3. 기록 조회
        elif menu == "📊 기록 조회":
            st.title("📊 업무 기록 조회")
            tab1, tab2 = st.tabs(["근태 기록", "반입/계량 기록"])
            with tab1: st.dataframe(get_data("attendance"), use_container_width=True)
            with tab2: st.dataframe(get_data("reports"), use_container_width=True)

if __name__ == "__main__":
    main()
