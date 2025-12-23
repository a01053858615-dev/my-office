import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import hashlib
from datetime import datetime

# --- [설정] 본인의 구글 시트 주소 입력 ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1nhrngvyO-L2Cwbvr_2-I-D1qwunYtB1WJuv9QBev8Nw/edit?usp=sharing"

# 1. 연결 설정
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. 비밀번호 암호화 함수
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# 3. 데이터 로드 및 정제 함수 (숫자 아이디 .0 제거 및 공백 제거)
def get_data(worksheet_name):
    df = conn.read(spreadsheet=SHEET_URL, worksheet=worksheet_name, ttl=0)
    df = df.astype(str)
    for col in df.columns:
        df[col] = df[col].str.replace(r'\.0$', '', regex=True).str.strip()
    return df

# 4. 세션 상태 초기화
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_info'] = None

# --- 메인 로직 시작 ---
def main():
    st.sidebar.title("🔥 시설 통합 관리")

    # [A] 로그인 전 화면
    if not st.session_state['logged_in']:
        menu = ["로그인", "회원가입"]
        choice = st.sidebar.selectbox("메뉴", menu)

        if choice == "로그인":
            st.subheader("🔐 시스템 로그인")
            user_input = st.text_input("아이디(사번)", key="login_user")
            pw_input = st.text_input("비밀번호", type='password', key="login_pw")
            
            if st.button("접속", key="login_btn"):
                users_df = get_data("users")
                hashed_pw = make_hashes(pw_input)
                
                # 데이터 정제 후 비교
                match = users_df[(users_df['username'] == user_input.strip()) & 
                                 (users_df['password'] == hashed_pw)]
                
                if not match.empty:
                    st.session_state['logged_in'] = True
                    st.session_state['user_info'] = match.iloc[0].to_dict()
                    st.success(f"{st.session_state['user_info']['name']}님, 반갑습니다!")
                    st.rerun()
                else:
                    st.error("아이디 또는 비밀번호가 틀렸습니다.")

        elif choice == "회원가입":
            st.subheader("📝 신규 계정 등록")
            new_user = st.text_input("사용할 아이디(사번)", key="reg_user")
            new_name = st.text_input("성함", key="reg_name")
            new_pw = st.text_input("비밀번호 설정", type='password', key="reg_pw")
            
            if st.button("등록 신청", key="reg_btn"):
                users_df = get_data("users")
                if new_user in users_df['username'].values:
                    st.warning("이미 사용 중인 아이디입니다.")
                else:
                    new_entry = pd.DataFrame([{"username": new_user, "password": make_hashes(new_pw), "name": new_name, "role": "user"}])
                    updated_users = pd.concat([users_df, new_entry], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet="users", data=updated_users)
                    st.success("계정이 생성되었습니다! 로그인을 해주세요.")

    # [B] 로그인 후 화면
    else:
        user_info = st.session_state['user_info']
        st.sidebar.info(f"접속자: {user_info['name']} ({user_info['role']})")
        
        if st.sidebar.button("로그아웃", key="logout_btn"):
            st.session_state['logged_in'] = False
            st.rerun()

        # 사이드바 메뉴
        main_menu = st.sidebar.radio("업무 선택", ["⏰ 근태 관리", "📝 업무 보고 작성", "📊 기록 조회"])

        # --- 1. 근태 관리 기능 ---
        if main_menu == "⏰ 근태 관리":
            st.title("⏰ 실시간 근태 관리")
            today = datetime.now().strftime("%Y-%m-%d")
            now_time = datetime.now().strftime("%H:%M:%S")
            
            attendance_df = get_data("attendance")
            my_today_record = attendance_df[(attendance_df['date'] == today) & 
                                            (attendance_df['username'] == user_info['username'])]

            st.info(f"📅 오늘 날짜: {today} | ⌚ 현재 시간: {now_time}")

            if my_today_record.empty:
                st.warning("아직 출근 전입니다.")
                if st.button("🚀 출근하기", use_container_width=True):
                    new_att = pd.DataFrame([{"date": today, "username": user_info['username'], "name": user_info['name'], "clock_in": now_time, "clock_out": "", "total_hours": ""}])
                    updated_df = pd.concat([attendance_df, new_att], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet="attendance", data=updated_df)
                    st.rerun()

            elif my_today_record.iloc[0]['clock_out'] == "":
                # 타이머 계산
                c_in_str = my_today_record.iloc[0]['clock_in']
                c_in_dt = datetime.strptime(f"{today} {c_in_str}", "%Y-%m-%d %H:%M:%S")
                diff = datetime.now() - c_in_dt
                
                st.success(f"✅ 출근 시각: {c_in_str}")
                st.metric("⏳ 현재 업무 시간", f"{str(diff).split('.')[0]}")
                
                if st.button("🏁 퇴근하기", use_container_width=True):
                    attendance_df.loc[(attendance_df['date'] == today) & (attendance_df['username'] == user_info['username']), 'clock_out'] = now_time
                    duration = datetime.now() - c_in_dt
                    attendance_df.loc[(attendance_df['date'] == today) & (attendance_df['username'] == user_info['username']), 'total_hours'] = f"{duration.total_seconds()/3600:.2f}"
                    conn.update(spreadsheet=SHEET_URL, worksheet="attendance", data=attendance_df)
                    st.balloons()
                    st.rerun()
            else:
                st.info("오늘 업무가 종료되었습니다.")
                st.write(f"출근: {my_today_record.iloc[0]['clock_in']} | 퇴근: {my_today_record.iloc[0]['clock_out']}")

        # --- 2. 업무 보고 및 조회 기능 (생략 없이 포함) ---
        elif main_menu == "📝 업무 보고 작성":
            st.title("📝 업무 보고서 작성")
            # [이전 보고서 작성 로직 반영...]
            st.write("소각로 점검 및 폐기물 반입
