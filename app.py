import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests
import base64
import re

st.set_page_config(page_title="2026 거제양정초 잔반 다이어트 AI 프로젝트", page_icon="🍱", layout="centered")

# ⚠️ 새 배포 후 발급받은 새로운 GAS 웹 앱 URL을 넣으세요!
GAS_URL = "https://script.google.com/macros/s/AKfycbzNozt2C04SOUsYLmZ6gaAzlCVlrR10S3jws5KZWJ4jNzC2yD4QV62-DPR8NoDuF121/exec"

# 스트림릿 비밀 금고에서 API 키 불러오기
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("API 키가 스트림릿 Secrets에 설정되지 않았습니다.")
    api_key = ""

if 'ai_result' not in st.session_state:
    st.session_state.ai_result = ""

if api_key and GAS_URL != "":
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-3.1-flash-lite')
    
    st.title("🍱 거제양정초 AI와 함께하는 '잔반 다이어트'")
    st.write("식판을 촬영해 AI 분석을 받고, 오늘 나의 성찰일지를 친구들과 공유해 보세요.")

    st.subheader("👤 학생 정보 입력")
    col1, col2 = st.columns(2)
    with col1:
        student_num = st.text_input("학번을 입력하세요 (예: 6101)", max_chars=4)
    with col2:
        student_name = st.text_input("이름을 입력하세요")

    st.subheader("📸 식판 촬영")
    img_file = st.camera_input("식판을 똑바로 촬영해 주세요!")

    if img_file and student_num and student_name:
        if st.session_state.ai_result == "":
            with st.spinner("AI가 식판을 분석하고 있습니다..."):
                image = Image.open(img_file)
                prompt = """
                너는 초등학교 급식 잔반 분석 전문가이자 친절한 환경 과학자야. 
                제공된 식판 사진을 보고 다음 4가지 항목에 대해 초등학생이 이해하기 쉽게 다정하고 명확한 말투로 답변해 줘.
                
                1. [잔반율]: 식판 전체 면적 대비 남은 음식의 양(남은 음식의 종류 개수도 참고)을 대략적인 백분율(%)로 알려줘. (예: 약 30% 남음, 다 먹었다면 0%)
                2. [주요 잔반]: 가장 많이 남은 음식 종류가 무엇인지 알려줘. 
                3. [환경 영향도]: 이 잔반이 유발하는 탄소 배출량의 수준을 상/중/하로 나누고, 이로 인해 지구가 받는 영향을 설명해 줘.
                4. [지구의 한마디]: 구체적인 행동 1가지를 다정하게 제안해 줘.
               
                답변 양식은 아래 서식을 무조건 지켜서 작성해 줘:
                ### 📊 AI 분석 결과
                - **잔반율**: 내용
                - **주요 잔반**: 내용
                - **환경 영향도**: 내용
                
                ### 🌍 지구의 한마디
                내용
                """
                response = model.generate_content([prompt, image])
                st.session_state.ai_result = response.text

        st.info("🤖 AI의 분석 결과를 확인하고 아래 성찰일지를 작성하세요.")
        st.markdown(st.session_state.ai_result)
        
        st.subheader("✍️ 오늘 나의 급식 성찰일지")
        reflection_text = st.text_area("오늘 음식을 남긴 이유와 다음 식사 때 실천할 나의 다짐을 적어주세요.")
        
        if st.button("🚀 성찰일지 게시판에 올리기"):
            if reflection_text:
                with st.spinner("게시판에 등록 중입니다..."):
                    bytes_data = img_file.getvalue()
                    base64_image = base64.b64encode(bytes_data).decode('utf-8')
                    data_uri = f"data:image/jpeg;base64,{base64_image}"
                    
                    payload = {
                        "num": student_num,
                        "name": student_name,
                        "feedback": st.session_state.ai_result,
                        "reflection": reflection_text,
                        "image_base64": data_uri
                    }
                    res = requests.post(GAS_URL, json=payload)
                    if res.status_code == 200:
                        st.success("🎉 성공적으로 등록되었습니다!")
                        st.session_state.ai_result = ""
                        st.rerun()
                    else:
                        st.error("등록에 실패했습니다.")

# --- 🌟 사이드바 및 동적 배경색 정렬 로직 ---
st.divider()

try:
    response = requests.get(GAS_URL)
    if response.status_code == 200:
        posts = response.json()
        
        if isinstance(posts, list) and len(posts) > 0:
            
            # 1. 데이터에서 날짜 추출 및 리스트 생성
            available_dates = []
            for post in posts:
                ts = post.get('timestamp', '')
                post_date = ts.split(' ')[0] if ts else "기록없음"
                post['date'] = post_date 
                if post_date not in available_dates and post_date != "기록없음":
                    available_dates.append(post_date)
            
            available_dates.sort(reverse=True) # 최신 날짜순 정렬
            
            # 💡 [핵심 추가] 전체 날짜 옵션을 리스트 맨 앞에 추가
            available_dates.insert(0, "🌟 전체 누적 (모든 날짜)")
            
            # 2. 사이드바 날짜 선택기
            st.sidebar.header("📊 2026 잔반 다이어트 현황판")
            selected_date = st.sidebar.selectbox("📅 날짜를 선택하세요", available_dates)
            
            # 3. 선택한 옵션에 따라 데이터 필터링
            if selected_date == "🌟 전체 누적 (모든 날짜)":
                filtered_posts = posts # 전체 데이터 사용
                display_title = "전체 누적"
            else:
                filtered_posts = [p for p in posts if p.get('date') == selected_date]
                display_title = selected_date
            
            # 4. 잔반율 평균 계산 로직 (필터링된 데이터 기준)
            total_rate = 0
            count = 0
            for p in filtered_posts:
                feedback = p.get('feedback', '')
                match = re.search(r'\*\*잔반율\*\*[^\d]*(\d+)', feedback)
                if match:
                    total_rate += int(match.group(1))
                    count += 1
            
            avg_rate = total_rate // count if count > 0 else 0
            
            # 5. 사이드바에 커다란 시계(위젯) 형태로 평균 출력
            st.sidebar.markdown(f"### 🎯 {display_title} 평균")
            st.sidebar.markdown(
                f"<div style='text-align: center; font-size: 80px; font-weight: bold; color: #444; background-color: white; border-radius: 15px; margin-bottom: 20px;'>{avg_rate}%</div>", 
                unsafe_allow_html=True
            )
            
            # 6. 현재 보고 있는 화면의 평균 잔반율에 따른 배경색상 동적 변경
            if avg_rate <= 10:
                bg_color = "rgba(76, 175, 80, 0.15)" # 초록색 (아주 낮음)
                status_msg = "🌍 지구가 아주 행복해해요!"
            elif avg_rate <= 30:
                bg_color = "rgba(255, 235, 59, 0.15)" # 노란색 (보통)
                status_msg = "👍 아주 잘하고 있어요!"
            elif avg_rate <= 50:
                bg_color = "rgba(255, 152, 0, 0.15)" # 주황색 (조금 높음)
                status_msg = "🤔 조금만 더 노력해볼까요?"
            else:
                bg_color = "rgba(244, 67, 54, 0.15)" # 붉은색 (매우 높음)
                status_msg = "🚨 잔반 다이어트가 시급해요!"
            
            st.sidebar.info(status_msg)
            
            # HTML/CSS를 화면 전체에 강제 주입하여 배경색 변경
            st.markdown(f"""
            <style>
            .stApp {{
                background-color: {bg_color};
                transition: background-color 0.5s ease;
            }}
            </style>
            """, unsafe_allow_html=True)
            
            # 7. 게시판 메인 화면 (필터링된 글만 역순 출력)
            st.header(f"👥 {display_title} 성찰 게시판")
            for post in reversed(filtered_posts):
                with st.container(border=True):
                    col_img, col_txt = st.columns([1, 2])
                    with col_img:
                        raw_img_url = post.get('image_url', '')
                        if raw_img_url and 'id=' in raw_img_url:
                            try:
                                file_id = raw_img_url.split('id=')[1]
                                safe_img_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w800"
                                st.image(safe_img_url, use_container_width=True)
                            except:
                                st.image(raw_img_url, use_container_width=True)
                        elif raw_img_url:
                             st.image(raw_img_url, use_container_width=True)
                        else:
                            st.info("📷 이미지 없음")
                    
                    with col_txt:
                        st.subheader(f"{post.get('num', '')} {post.get('name', '')}")
                        st.caption(f"🕒 등록 시간: {post.get('timestamp', '')}")
                        st.write(f"**✍️ 나의 성찰:** {post.get('reflection', '')}")
                        with st.expander("🤖 AI 피드백 다시보기"):
                            st.markdown(post.get('feedback', ''))
        else:
            st.info("아직 등록된 성찰일지가 없습니다. 첫 번째 주인공이 되어보세요!")
            
except Exception as e:
    st.error(f"게시판 데이터를 불러오는 중 문제가 발생했습니다. (에러: {e})")
