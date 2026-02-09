import streamlit as st
import pandas as pd
from pykrx import stock
from datetime import datetime, timedelta
import requests

# 1. 페이지 설정 및 프리미엄 테마 (CSS)
st.set_page_config(page_title="홍익 미래 유산 검색기", layout="wide")

st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    .stApp { background-color: #0A0C10; font-family: 'Pretendard', sans-serif; }
    
    /* 제목 및 서브타이틀 */
    .main-title {
        font-size: clamp(1.3rem, 7vw, 2.5rem);
        background: linear-gradient(to right, #FFD700, #FDB931);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        text-align: center;
        padding-top: 20px;
    }
    .sub-title {
        color: #808495;
        text-align: center;
        font-size: clamp(12px, 3vw, 15px);
        margin-bottom: 25px;
        font-weight: 400;
    }

    /* 유산 스캐너 정비 중 박스 (사용자 요청 복구) */
    .maintenance-box {
        background-color: #161B22;
        padding: 35px 20px;
        border-radius: 20px;
        border: 1px solid #FDB931;
        text-align: center;
        margin-top: 10px;
        box-shadow: 0px 4px 15px rgba(253, 185, 49, 0.1);
    }

    /* 필터 및 카드 스타일 */
    .stSelectbox label { color: #FFD700 !important; font-weight: bold; }
    .streamlit-expanderHeader {
        background-color: #161B22 !important;
        border-radius: 12px !important;
        border: 1px solid #30363D !important;
    }
    [data-testid="stMetricValue"] { color: #FFD700 !important; }
    </style>
    """, unsafe_allow_html=True)

# 제목부 출력
st.markdown('<div class="main-title">🏛️ 홍익 미래 유산 검색기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">널리 주식 투자자를 이롭게 하는 미래 자산 발굴 시스템</div>', unsafe_allow_html=True)

# 2. 상단 필터 배치
col_f1, col_f2 = st.columns(2)
with col_f1:
    category = st.selectbox("📂 분류", ["🔥 거래급등 (단기이슈)", "👑 우량주 (시총상위)"])
with col_f2:
    status_filter = st.selectbox("📈 등락 필터", ["전체 보기", "상승 종목만", "급등주 (5%↑)"])

# 3. 데이터 엔진
@st.cache_data(ttl=3600)
def get_integrated_data(filter_type):
    try:
        header = {'User-Agent': 'Mozilla/5.0'}
        # 우량주 선택 시 시총 페이지, 아니면 거래량 순위 페이지
        url = "https://finance.naver.com/sise/sise_market_sum.naver?sosok=0" if "우량주" in filter_type else "https://finance.naver.com/sise/sise_quant.naver?sosok=0"
        res = requests.get(url, headers=header)
        df_list = pd.read_html(res.text, encoding='cp949')
        # 데이터가 있는 테이블 선택 (네이버 금융 구조 대응)
        df = df_list[1] if len(df_list) > 1 else df_list[0]
        return df.dropna(subset=['종목명']).head(30)
    except:
        return None

data = get_integrated_data(category)

# 4. 화면 렌더링
if data is not None and not data.empty and '
