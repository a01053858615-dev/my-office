import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import hashlib

# 1. 비밀번호 암호화 함수
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# 2. 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. 사용자 데이터 불러오기 함수
def get_user_data():
    # 'users' 시트의 데이터를 읽어옵니다.
    return conn.read(worksheet="users", ttl=0)

# 4. 세션 상태 초기화
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_info'] = None

# --- 메인 로직 ---
def main():
    if not st.session_state['logged_in']:
        menu = ["로그인", "회원가입"]
        choice = st.sidebar.selectbox("메뉴", menu)

        if choice == "로그인":
            st.subheader("🔑 로그인")
            username = st.text_input("아이디")
            password = st.text_input("비밀번호", type='password')

            if st.button("접속하기"):
                users_df = get_user_data()
                hashed_pw = make_hashes(password)
                
                # 아이디와 비밀번호가 일치하는 행 찾기
                user_match = users_df[(users_df['username'] == username) & (users_df['password'] == hashed_pw)]
                
                if not user_match.empty:
                    st.session_state['logged_in'] = True
                    st.session_state['user_info'] = user_match.iloc[0].to_dict()
                    st.success(f"{st.session_state['user_info']['name']}님, 환영합니다!")
                    st.rerun()
                else:
                    st.error("아이디 또는 비밀번호가 틀렸습니다.")

        elif choice == "회원가입":
            st.subheader("📝 새 계정 생성")
            new_user = st.text_input("원하는 아이디")
            new_name = st.text_input("실명")
            new_password = st.text_input("비밀번호", type='password')
            
            if st.button("가입 신청"):
                users_df = get_user_data()
                if new_user in users_df['username'].values:
                    st.warning("이미 존재하는 아이디입니다.")
                else:
                    # 새 사용자 정보 추가
                    new_data = pd.DataFrame([{
                        "username": new_user,
                        "password": make_hashes(new_password),
                        "name": new_name,
                        "role": "user" # 기본 권한은 일반 사용자
                    }])
                    updated_users = pd.concat([users_df, new_data], ignore_index=True)
                    conn.update(worksheet="users", data=updated_users)
                    st.success("회원가입이 완료되었습니다! 로그인을 진행해주세요.")

    # 로그인 후 화면
    else:
        user = st.session_state['user_info']
        st.sidebar.success(f"접속: {user['name']} ({user['role']})")
        if st.sidebar.button("로그아웃"):
            st.session_state['logged_in'] = False
            st.rerun()

        st.title("🔥 오피스 메인 화면")
        # 여기에 로그인한 사람만 볼 수 있는 기능을 넣습니다.
        if user['role'] == 'admin':
            st.write("😎 당신은 관리자입니다. 모든 결재를 승인할 수 있습니다.")
        else:
            st.write("📄 당신은 일반 사원입니다. 보고서를 작성할 수 있습니다.")

if __name__ == '__main__':
    main()
