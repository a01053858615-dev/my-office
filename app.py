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

# 3. 데이터 로드 함수
# 기존 get_data 함수를 이 내용으로 덮어쓰세요
def get_data(worksheet_name):
    # 1. 데이터를 먼저 읽어옵니다.
    df = conn.read(spreadsheet=SHEET_URL, worksheet=worksheet_name, ttl=0)
    
    # 2. 모든 데이터를 문자로 변환합니다.
    df = df.astype(str)
    
    # 3. 데이터 뒤에 붙은 '.0'을 제거하고 앞뒤 공백을 깎아냅니다.
    # (숫자 아이디가 소수점으로 변하는 현상 방지)
    for col in df.columns:
        df[col] = df[col].str.replace(r'\.0$', '', regex=True).str.strip()
        
    return df

# 4. 세션 상태 초기화
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_info'] = None

# --- 메인 로직 ---
def main():
    st.sidebar.title("🔥 시설 통합 관리")

    if not st.session_state['logged_in']:
        menu = ["로그인", "회원가입"]
        choice = st.sidebar.selectbox("메뉴", menu)

        if choice == "로그인":
            st.subheader("🔐 시스템 로그인")
            user_input = st.text_input("아이디", key="login_user")
            pw_input = st.text_input("비밀번호", type='password', key="login_pw")
            
            # 버튼에 key="login_btn"을 추가하여 중복 오류를 방지합니다.
            if st.button("접속", key="login_btn"):
                users_df = get_data("users")
                hashed_pw = make_hashes(pw_input)
                
                # [디버그 정보] 로그인이 안 될 때 아래 내용을 확인해 보세요.
                st.write("--- 🔍 로그인 체크 중 ---")
                st.write(f"입력 아이디: [{user_input}]")
                st.write(f"시트 내 아이디 목록: {users_df['username'].tolist()}")
                
                # 일치하는 계정 확인
                match = users_df[(users_df['username'] == user_input) & 
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
            new_user = st.text_input("아이디 설정", key="reg_user")
            new_name = st.text_input("성함", key="reg_name")
            new_pw = st.text_input("비밀번호 설정", type='password', key="reg_pw")
            
            if st.button("등록 신청", key="reg_btn"):
                users_df = get_data("users")
                if new_user in users_df['username'].values:
                    st.warning("이미 사용 중인 아이디입니다.")
                else:
                    new_entry = pd.DataFrame([{
                        "username": new_user, 
                        "password": make_hashes(new_pw), 
                        "name": new_name, 
                        "role": "user"
                    }])
                    updated_users = pd.concat([users_df, new_entry], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet="users", data=updated_users)
                    st.success("계정이 생성되었습니다! 로그인을 진행해 주세요.")

    else:
        # 로그인 후 화면
        user_info = st.session_state['user_info']
        st.sidebar.info(f"접속자: {user_info['name']} ({user_info['role']})")
        
        if st.sidebar.button("로그아웃", key="logout_btn"):
            st.session_state['logged_in'] = False
            st.rerun()

        st.title("🏠 관리 대시보드")
        st.write(f"[{user_info['name']}]님, 환영합니다. 현재 권한은 [{user_info['role']}]입니다.")

if __name__ == '__main__':
    main()
