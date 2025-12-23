import streamlit as st

st.title("🔥 우리 회사 관리 시스템")
st.write("사용자님의 오피스 사이트가 성공적으로 개설되었습니다!")

name = st.text_input("이름을 입력하세요")
if name:
    st.write(f"반갑습니다, {name}님! 업무를 시작해볼까요?")
