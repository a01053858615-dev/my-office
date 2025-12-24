import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import hashlib
from datetime import datetime

# --- [설정] ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1nhrngvyO-L2Cwbvr_2-I-D1qwunYtB1WJuv9QBev8Nw/edit?usp=sharing".strip()

# 1. 페이지 설정
st.set_page_config(page_title="시설 통합 관리 시스템", layout="wide")

# 2. 디자인 (CSS)
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .stButton>button { border-radius: 5px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 3. 연결 설정
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Secrets 설정(JSON 키)을 확인해주세요.")
    st.stop()

# 4. 함수 정의
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

# 5. 세션 상태
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None

# --- 메인 로직 ---
def main():
    st.sidebar.title("🏢 시설 통합 관리 v2.0")

    if not st.session_state['logged_in']:
        st.subheader("🔐 시스템 로그인")
        user_id = st.text_input("아이디(사번)")
        user_pw = st.text_input("비밀번호", type='password')
        
        if st.button("접속하기", use_container_width=True):
            users_df = get_data("users")
            if not users_df.empty:
                hashed_pw = make_hashes(user_pw)
                match = users_df[(users_df['username'] == user_id.strip()) & 
                                 (users_df['password'] == hashed_pw)]
                if not match.empty:
                    st.session_state['logged_in'] = True
                    st.session_state['user_info'] = match.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("로그인 정보가 틀립니다.")

    else:
        user = st.session_state['user_info']
        st.sidebar.success(f"✅ {user['name']}님")
        if st.sidebar.button("로그아웃"):
            st.session_state['logged_in'] = False
            st.rerun()

        menu = st.sidebar.radio("메뉴", ["⏰ 근태 관리", "🚛 올바로 계량", "📊 기록 조회"])

        if menu == "⏰ 근태 관리":
            st.title("⏰ 근태 관리")
            # 자동 타이머 대신 수동 갱신 버튼
            st.button("🔄 시각 동기화 (새로고침)")
            
            today = datetime.now().strftime("%Y-%m-%d")
            now_dt = datetime.now()
            attendance_df = get_data("attendance")
            my_record = attendance_df[(attendance_df['date'] == today) & (attendance_df['username'] == user['username'])]

            st.info(f"📅 오늘: {today} | ⌚ 현재: {now_dt.strftime('%H:%M:%S')}")

            if my_record.empty:
                if st.button("🚀 출근하기", use_container_width=True):
                    new_att = pd.DataFrame([{"date": today, "username": user['username'], "name": user['name'], "clock_in": now_dt.strftime('%H:%M:%S'), "clock_out": "", "total_hours": ""}])
                    conn.update(spreadsheet=SHEET_URL, worksheet="attendance", data=pd.concat([attendance_df, new_att], ignore_index=True))
                    st.rerun()
            elif my_record.iloc[0]['clock_out'] == "":
                st.success(f"✅ 출근 시각: {my_record.iloc[0]['clock_in']}")
                if st.button("🏁 퇴근하기", use_container_width=True):
                    attendance_df.loc[(attendance_df['date'] == today) & (attendance_df['username'] == user['username']), 'clock_out'] = now_dt.strftime("%H:%M:%S")
                    conn.update(spreadsheet=SHEET_URL, worksheet="attendance", data=attendance_df)
                    st.balloons()
                    st.rerun()
            else:
                st.info("오늘 업무가 완료되었습니다.")

        elif menu == "🚛 올바로 계량":
            st.title("🚛 올바로 계량 정보 입력")
            with st.form("allbaro_form"):
                manifest_no = st.text_input("인계번호 (MANF_NUMS)")
                car_no = st.text_input("차량번호 (TRAN_NUMS)")
                gross = st.number_input("총중량(kg)", min_value=0)
                empty = st.number_input("공차중량(kg)", min_value=0)
                st.metric("계산된 실중량", f"{gross - empty} kg")
                
                if st.form_submit_button("⚖️ 계량 확정 저장"):
                    reports_df = get_data("reports")
                    new_row = pd.DataFrame([{"날짜": today, "인계번호": manifest_no, "차량번호": car_no, "실중량": gross-empty, "상태": "확정"}])
                    conn.update(spreadsheet=SHEET_URL, worksheet="reports", data=pd.concat([reports_df, new_row], ignore_index=True))
                    st.success("구글 시트에 저장되었습니다.")

        elif menu == "📊 기록 조회":
            st.title("📊 통합 기록 조회")
            st.subheader("⏰ 근태 기록")
            st.dataframe(get_data("attendance"), use_container_width=True)
            st.subheader("🚛 반입 기록")
            st.dataframe(get_data("reports"), use_container_width=True)

if __name__ == "__main__":
    main()
