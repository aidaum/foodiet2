import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests
import base64
import re

st.set_page_config(page_title="잔반 다이어트 AI 프로젝트", page_icon="🍱", layout="centered")

# --- 🌟 UI 및 모바일 카메라 최적화 CSS 주입 ---
st.markdown("""
<style>
/* 1. 제목이 한 줄로 예쁘게 들어가도록 반응형 크기 조절 */
.main-title {
    text-align: center;
    font-size: clamp(1.2rem, 3.5vw, 1.8rem); /* 화면 크기에 따라 글씨가 자동으로 커지고 작아짐 */
    font-weight: 800;
    margin-bottom: 0.5rem;
    word-break: keep-all; /* 단어 단위로 끊어지도록 설정 */
}

/* 2. 모바일 환경에서 카메라 화면 검은 여백 없애고 꽉 차게 만들기 */
[data-testid="stCameraInput"] video {
    width: 100% !important;
    height: auto !important;
    object-fit: cover !important; /* 비율을 유지하면서 여백 없이 화면을 꽉 채움 */
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# ⚠️ 새 배포 후 발급받은 새로운 GAS 웹 앱 URL을 넣으세요!
GAS_URL = "https://script.google.com/macros/s/AKfycbz4dEmc5PH6rCG8EErJIW5NMTy26g5VBdAX09EEGaLMJTcUOphfcIh44m28JefzdyPc/exec"

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
    
    # 🌟 1번 보완: 한 줄로 들어가는 깔끔한 디자인의 제목
    st.markdown("<div class='main-title'>🍱 2026 거제양정초 AI와 함께하는 잔반 다이어트</div>", unsafe_allow_html=True)
    st.write("<div style='text-align: center; color: gray; margin-bottom: 2rem;'>식판을 촬영해 AI 분석을 받고, 오늘 나의 성찰일지를 친구들과 공유해 보세요.</div>", unsafe_allow_html=True)

    st.subheader("👤 학생 정보 입력")
    col1, col2 = st.columns(2)
    with col1:
        student_num = st.text_input("학번을 입력하세요 (예: 6101)", max_chars=4)
    with col2:
        student_name = st.text_input("이름을 입력하세요")

    st.divider()

    # 🌟 2번 & 3번 보완: 사진 촬영 및 파일 업로드 선택 기능 추가
    st.subheader("📸 식판 사진 등록")
    input_method = st.radio("사진 등록 방식을 선택하세요.", ["카메라로 즉시 촬영", "갤러리/컴퓨터에서 파일 업로드"], horizontal=True)

    img_file = None
    if input_method == "카메라로 즉시 촬영":
        img_file = st.camera_input("식판을 밝은 곳에서 똑바로 촬영해 주세요!")
    else:
        img_file = st.file_uploader("기기에 저장된 식판 사진을 선택해 주세요.", type=['png', 'jpg', 'jpeg'])

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
                    
                    try:
                        # 구글 서버로 전송
                        res = requests.post(GAS_URL, json=payload)
                        
                        if res.status_code == 200:
                            result = res.json()
                            # 구글 서버에서 status가 success로 왔을 때만 진짜 성공 처리
                            if isinstance(result, dict) and result.get("status") == "success":
                                st.success("🎉 성공적으로 등록되었습니다!")
                                st.session_state.ai_result = ""
                                
                                import time
                                time.sleep(1.5) # 사용자가 성공 메시지를 읽을 수 있도록 1.5초 대기
                                st.rerun()      # 화면 새로고침
                            else:
                                # 구글 서버에서 에러가 발생한 경우 화면에 빨간색으로 출력
                                st.error(f"❌ 구글 서버 에러: {result.get('message', '알 수 없는 오류')}")
                        else:
                            st.error(f"❌ 통신 에러 (상태 코드: {res.status_code})")
                    except Exception as e:
                        st.error(f"❌ 전송 중 오류가 발생했습니다: {e}")
            else:
                st.warning("성찰일지 내용을 입력해야 등록할 수 있습니다.")

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
            
            available_dates.sort(reverse=True)
            available_dates.insert(0, "🌟 전체 누적 (모든 날짜)")
            
            # 2. 사이드바 날짜 선택기
            st.sidebar.header("📊 잔반 다이어트 현황판")
            selected_date = st.sidebar.selectbox("📅 날짜를 선택하세요", available_dates)
            
            # 3. 선택한 옵션에 따라 데이터 필터링
            if selected_date == "🌟 전체 누적 (모든 날짜)":
                filtered_posts = posts 
                display_title = "전체 누적"
            else:
                filtered_posts = [p for p in posts if p.get('date') == selected_date]
                display_title = selected_date
            
            # 4. 잔반율 평균 계산
            total_rate = 0
            count = 0
            for p in filtered_posts:
                feedback = p.get('feedback', '')
                match = re.search(r'\*\*잔반율\*\*[^\d]*(\d+)', feedback)
                if match:
                    total_rate += int(match.group(1))
                    count += 1
            
            avg_rate = total_rate // count if count > 0 else 0
            
            # 5. 사이드바 평균 출력
            st.sidebar.markdown(f"### 🎯 {display_title} 평균")
            st.sidebar.markdown(
                f"<div style='text-align: center; font-size: 80px; font-weight: bold; color: #444; background-color: white; border-radius: 15px; margin-bottom: 20px;'>{avg_rate}%</div>", 
                unsafe_allow_html=True
            )
            
            # 6. 배경색상 동적 변경
            if avg_rate <= 10:
                bg_color = "rgba(76, 175, 80, 0.15)" # 초록
                status_msg = "🌍 지구가 아주 행복해해요!"
            elif avg_rate <= 30:
                bg_color = "rgba(255, 235, 59, 0.15)" # 노란
                status_msg = "👍 아주 잘하고 있어요!"
            elif avg_rate <= 50:
                bg_color = "rgba(255, 152, 0, 0.15)" # 주황
                status_msg = "🤔 조금만 더 노력해볼까요?"
            else:
                bg_color = "rgba(244, 67, 54, 0.15)" # 빨강
                status_msg = "🚨 잔반 다이어트가 시급해요!"
            
            st.sidebar.info(status_msg)
            
            st.markdown(f"""
            <style>
            .stApp {{
                background-color: {bg_color};
                transition: background-color 0.5s ease;
            }}
            </style>
            """, unsafe_allow_html=True)
            
            # 7. 게시판 메인 화면
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
