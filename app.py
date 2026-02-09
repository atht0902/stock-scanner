import streamlit as st
import pandas as pd
from pykrx import stock
from datetime import datetime, timedelta
import requests

# 1. 테마 및 배경 설정
st.set_page_config(page_title="홍익 미래 유산 검색기", layout="wide")

st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    .stApp { background-color: #0A0C10; font-family: 'Pretendard', sans-serif; }
    .main-title {
        font-size: clamp(1.3rem, 7vw, 2.5rem);
        background: linear-gradient(to right, #FFD700, #FDB931);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        text-align: center;
        padding: 10px 0px;
    }
    .stSelectbox label { color: #FFD700 !important; font-size: 13px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-title">🏛️ 홍익 미래 유산 검색기</div>', unsafe_allow_html=True)

# 2. 데이터 엔진 (우량주/거래량 데이터 통합)
@st.cache_data(ttl=3600)
def get_integrated_data(filter_type):
    try:
        header = {'User-Agent': 'Mozilla/5.0'}
        if filter_type == "👑 우량주 (시총상위)":
            # 네이버 시가총액 상위 페이지 (코스피)
            url = "https://finance.naver.com/sise/sise_market_sum.naver?sosok=0"
            res = requests.get(url, headers=header)
            df = pd.read_html(res.text, encoding='cp949')[1]
            df = df.dropna(subset=['종목명'])
        else:
            # 거래상위 페이지
            url = "https://finance.naver.com/sise/sise_quant.naver?sosok=0"
            res = requests.get(url, headers=header)
            df = pd.read_html(res.text, encoding='cp949')[1].dropna()
        
        return df.head(30)
    except:
        return None

# 3. 상단 필터 배치
col_f1, col_f2 = st.columns(2)
with col_f1:
    category = st.selectbox("🗂️ 분류", ["🔥 거래급등 (단기이슈)", "👑 우량주 (시총상위)"])
with col_f2:
    status_filter = st.selectbox("📈 등락 필터", ["전체 보기", "상승 종목만", "급등주 (5%↑)"])

# 데이터 로드
data = get_integrated_data(category)

# 4. 필터링 및 그리드 출력
if data is not None:
    # 컬럼명 통일 (시총 페이지와 거래상위 페이지 컬럼명이 다를 수 있음 대비)
    data = data.rename(columns={'등락률': '등락률', '현재가': '현재가'})
    
    # 숫자 변환
    data['등락률_num'] = data['등락률'].astype(str).str.replace('%','').replace('+','').str.strip().astype(float)
    
    # 등락 필터 적용
    if status_filter == "급등주 (5%↑)":
        data = data[data['등락률_num'] >= 5.0]
    elif status_filter == "상승 종목만":
        data = data[data['등락률_num'] > 0]

    # 그리드 출력 (상위 12개)
    if not data.empty:
        cols = st.columns(2)
        for i, (_, row) in enumerate(data.head(12).iterrows()):
            with cols[i % 2]:
                icon = "🔥" if row['등락률_num'] >= 10 else ("👑" if category == "👑 우량주 (시총상위)" else "💎")
                with st.expander(f"{icon} {row['종목명']} ({row['등락률']})"):
                    st.metric("현재가", f"{int(row['현재가']):,}원")
                    # 공유/분석 버튼
                    b1, b2 = st.columns(2)
                    url = f"https://finance.naver.com/search/search.naver?query={row['종목명']}"
                    b1.link_button("📊 분석", url, use_container_width=True)
                    b2.link_button("🔗 공유", f"https://social-plugins.line.me/lineit/share?url={url}", use_container_width=True)
    else:
        st.info("조건에 맞는 유산이 없습니다.")
else:
    st.error("데이터 서버 점검 중")

st.divider()
st.caption("Produced by Hong-Ik Heritage Finder • Premium Free Edition")
