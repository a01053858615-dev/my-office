import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import hashlib
from datetime import datetime

# --- [설정] 본인의 구글 시트 주소 ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1nhrngvyO-L2Cwbvr_2-I-D1qwunYtB1WJuv9QBev8Nw/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def get_data(worksheet_name):
    df = conn.read(spreadsheet=SHEET_URL, worksheet=worksheet_name, ttl=0)
    return df.astype(str).apply(lambda x: x.str.strip())

# --- 메인 로직 시작 ---
def main():
    st.sidebar.title("🔥 시설 통합 관리")

    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if not st.session_state['logged_in']:
        # [로그인/회원가입 로직은 기존과 동일하므로 생략 - 이전 코드를 그대로 유지하세요]
        pass 

    else:
        user_info = st.session_state['user_info']
        st.sidebar.info(f"접속자: {user_info['name']}")
        
        # 메뉴 선택
        main_menu = st.sidebar.radio("업무 선택", ["🏠 대시보드", "⏰ 근태 관리", "📝 업무 보고"])

        # --- [신규] 근태 관리 기능 ---
        if main_menu == "⏰ 근태 관리":
            st.title("⏰ 실시간 근태 관리")
            today = datetime.now().strftime("%Y-%m-%d")
            now_time = datetime.now().strftime("%H:%M:%S")
            
            # 1. 오늘 내 근태 기록이 있는지 확인
            attendance_df = get_data("attendance")
            my_today_record = attendance_df[(attendance_df['date'] == today) & 
                                            (attendance_df['username'] == user_info['username'])]

            st.info(f"📅 오늘 날짜: {today} | ⌚ 현재 시간: {now_time}")

            # 상태 판별
            if my_today_record.empty:
                # 출근 전
                st.warning("아직 출근 처리가 되지 않았습니다.")
                if st.button("🚀 출근하기", use_container_width=True):
                    new_attendance = pd.DataFrame([{
                        "date": today,
                        "username": user_info['username'],
                        "name": user_info['name'],
                        "clock_in": now_time,
                        "clock_out": "",
                        "total_hours": ""
                    }])
                    updated_df = pd.concat([attendance_df, new_attendance], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet="attendance", data=updated_df)
                    st.success(f"{now_time} 출근 처리 완료!")
                    st.rerun()

            elif my_today_record.iloc[0]['clock_out'] == "":
                # 출근함, 퇴근 전
                clock_in_time_str = my_today_record.iloc[0]['clock_in']
                clock_in_time = datetime.strptime(f"{today} {clock_in_time_str}", "%Y-%m-%d %H:%M:%S")
                elapsed = datetime.now() - clock_in_time
                
                # 타이머 표시
                st.success(f"✅ 출근 완료: {clock_in_time_str}")
                st.metric("⏳ 현재 업무 시간", f"{str(elapsed).split('.')[0]}")
                
                if st.button("🏁 퇴근하기", use_container_width=True):
                    # 퇴근 기록 업데이트
                    attendance_df.loc[(attendance_df['date'] == today) & 
                                      (attendance_df['username'] == user_info['username']), 'clock_out'] = now_time
                    
                    # 총 근무 시간 계산
                    duration = datetime.now() - clock_in_time
                    hours = duration.total_seconds() / 3600
                    attendance_df.loc[(attendance_df['date'] == today) & 
                                      (attendance_df['username'] == user_info['username']), 'total_hours'] = f"{hours:.2f}"
                    
                    conn.update(spreadsheet=SHEET_URL, worksheet="attendance", data=attendance_df)
                    st.balloons()
                    st.success(f"{now_time} 퇴근 처리 완료! 오늘 고생하셨습니다.")
                    st.rerun()
            
            else:
                # 퇴근 완료
                record = my_today_record.iloc[0]
                st.info("오늘 업무가 종료되었습니다.")
                st.write(f"출근: {record['clock_in']} | 퇴근: {record['clock_out']}")
                st.write(f"총 근무 시간: {record['total_hours']} 시간")

        # [기타 메뉴 로직...]
