import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import hashlib

# --- [설정] 본인의 구글 시트 주소를 여기에 입력하세요 ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1nhrngvyO-L2Cwbvr_2-I-D1qwunYtB1WJuv9QBev8Nw/edit?usp=sharing"

# 1. 연결 설정
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. 비밀번호 암호화 함수
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# 3. 데이터 로드 함수 (주소와 탭 이름을 명시하여 오류 방지)
def get_data(worksheet_name):
    return conn.read(spreadsheet=SHEET_URL, worksheet=worksheet_name, ttl=0)

# 4. 세션 상태 초기화
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_info'] = None

# --- 메인 로직 ---
def main():
    st.sidebar.title("🔥 시설 통합 관리")

    if not st.session_state['logged_in']:
        # 로그인 전 화면
        menu = ["로그인", "회원가입"]
        choice = st.sidebar.selectbox("메뉴", menu)

        if choice == "로그인":
            st.subheader("🔐 시스템 로그인")
            user = st.text_input("아이디")
            pw = st.text_input("비밀번호", type='password')
            
            if st.button("접속"):
                users_df = get_data("users")
                hashed_pw = make_hashes(pw)
                
                # 일치하는 계정 확인
                match = users_df[(users_df['username'] == user) & (users_df['password'] == hashed_pw)]
                
                if not match.empty:
                    st.session_state['logged_in'] = True
                    st.session_state['user_info'] = match.iloc[0].to_dict()
                    st.success(f"{st.session_state['user_info']['name']}님, 반갑습니다!")
                    st.rerun()
                else:
                    st.error("아이디 또는 비밀번호가 틀렸습니다.")

        elif choice == "회원가입":
            st.subheader("📝 신규 계정 등록")
            new_user = st.text_input("아이디 설정")
            new_name = st.text_input("성함")
            new_pw = st.text_input("비밀번호 설정", type='password')
            
            if st.button("등록 신청"):
                users_df = get_data("users")
                if new_user in users_df['username'].values:
                    st.warning("이미 사용 중인 아이디입니다.")
                else:
                    new_entry = pd.DataFrame([{"username": new_user, "password": make_hashes(new_pw), "name": new_name, "role": "user"}])
                    updated_users = pd.concat([users_df, new_entry], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet="users", data=updated_users)
                    st.success("계정이 생성되었습니다! 로그인을 진행해 주세요.")

    else:
        # 로그인 후 화면
        user_info = st.session_state['user_info']
        st.sidebar.info(f"접속자: {user_info['name']} ({user_info['role']})")
        
        if st.sidebar.button("로그아웃"):
            st.session_state['logged_in'] = False
            st.rerun()

        # 사이드바 메뉴 구성
        main_menu = st.sidebar.radio("업무 선택", ["대시보드", "업무 보고 작성", "기록 조회"])

        if main_menu == "대시보드":
            st.title("🏠 관리 대시보드")
            st.write(f"{user_info['name']}님, 오늘 업무를 확인하세요.")
            # 시설 데이터 요약 등을 여기에 추가할 수 있습니다.

        elif main_menu == "업무 보고 작성":
            st.title("📝 업무 보고서 작성")
            with st.form("report_form"):
                date = st.date_input("날짜")
                title = st.text_input("보고 제목")
                content = st.text_area("상세 내용 (소각량, 시설 점검 내용 등)")
                
                if st.form_submit_button("보고서 제출"):
                    reports_df = get_data("reports")
                    new_report = pd.DataFrame([{
                        "날짜": str(date),
                        "작성자": user_info['name'],
                        "제목": title,
                        "내용": content,
                        "결재상태": "대기"
                    }])
                    updated_reports = pd.concat([reports_df, new_report], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet="reports", data=updated_reports)
                    st.success("보고서가 서버에 영구 저장되었습니다.")

        elif main_menu == "기록 조회":
            st.title("📊 업무 기록 조회")
            reports_df = get_data("reports")
            st.dataframe(reports_df, use_container_width=True)

if __name__ == '__main__':
    main()
