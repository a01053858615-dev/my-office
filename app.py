# app.py의 로그인 버튼 클릭 부분 (if st.button("접속하기"): 아래에 추가)
            if st.button("접속하기", use_container_width=True):
                users_df = get_data("users")
                
                # 진단용: 시트에서 읽어온 데이터가 있는지 확인
                if users_df.empty:
                    st.error("구글 시트에서 사용자 정보를 가져오지 못했습니다.")
                else:
                    # 진단용: 입력한 아이디와 시트의 아이디가 일치하는게 있는지 확인
                    st.write(f"입력한 아이디: {user_input.strip()}")
                    st.write(f"시트 내 아이디 목록: {users_df['username'].tolist()}")
                    
                    hashed_pw = make_hashes(pw_input)
                    match = users_df[(users_df['username'] == user_input.strip()) & 
                                     (users_df['password'] == hashed_pw)]
                    
                    if not match.empty:
                        # ... 성공 로직 ...
