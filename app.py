import streamlit as st

# 1. 로그인 상태 확인 (세션 저장)
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

# 2. 로그인 화면
if not st.session_state['auth']:
    st.title("🔐 관리 시스템 로그인")
    user_id = st.text_input("아이디")
    user_pw = st.text_input("비밀번호", type="password")
    
    if st.button("로그인"):
        # 임시 아이디/비밀번호 (나중에 바꿀 수 있습니다)
        if user_id == "admin" and user_pw == "1234":
            st.session_state['auth'] = True
            st.rerun()
        else:
            st.error("정보가 일치하지 않습니다.")

# 3. 로그인 성공 시 보여줄 화면
else:
    st.sidebar.button("로그아웃", on_click=lambda: st.session_state.update({"auth": False}))
    st.title("🔥 우리 회사 오피스 메인")
    st.write("환영합니다! 이제 보안이 적용된 상태입니다.")
    
    # 여기에 앞으로 결재, 인사관리 등의 메뉴를 추가할 거예요.
    menu = st.sidebar.selectbox("메뉴 선택", ["대시보드", "전자결재", "인사관리"])
    st.info(f"현재 선택된 메뉴: {menu}")
