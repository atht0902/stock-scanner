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
    
    /* 전체 배경색 및 폰트 */
    .stApp {
        background-color: #0A0C10;
        font-family: 'Pretendard', sans-serif;
    }

    /* 반응형 골드 그라데이션 타이틀 */
    .main-title {
        font-size: clamp(1.4rem, 7vw, 2.8rem); 
        background: linear-gradient(to right, #FFD700, #FDB931);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        text-align: center;
        padding: 15px 0px;
        line-height: 1.2;
        letter-spacing: -0.05rem;
    }

    .sub-title {
        color: #808495;
        text-align: center;
        font-size: 14px;
        margin-bottom: 30px;
    }

    /* 카드 스타일 최적화 */
    .streamlit-expanderHeader {
        background-color: #161B22 !important;
        border-radius: 12px !important;
        border: 1px solid #30363D !important;
        color: white !important;
    }

    /* 지표 숫자 색상 */
    [data-testid="stMetricValue"] {
        color: #FFD700 !important;
    }

    /* 하단 안내창 커스텀 */
    .error-box {
        background-color: #161B22;
        padding: 25px;
        border-radius: 15px;
        border: 1px solid #FDB931;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# 타이틀 표시
st.markdown('<div class="main-title">🏛️ 홍익 미래 유산 검색기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">널리 주식 투자자를 이롭게 하는 미래 자산 발굴 시스템</div>', unsafe_allow_html=True)

# 2. 하이브리드 데이터 로드 함수 (캐싱 적용)
@st.cache_data(ttl=3600)
def fetch_all_data():
    # 시도 1: 네이버 금융 실시간 데이터
    try:
        url = "https://finance.naver.com/sise/sise_quant.naver?sosok=1"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        df_list = pd.read_html(res.text, encoding='cp949')
        if len(df_list) > 1:
            df = df_list[1].dropna().head(12)
            return "naver", df[['종목명', '현재가', '등락률', '거래량']]
    except:
        pass

    # 시도 2: 거래소 데이터 (최근 영업일)
    for i in range(5):
        dt = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        try:
            df = stock.get_market_ohlcv_by_ticker(dt, market="ALL")
            if not df.empty:
                top_df = df.sort_values(by='거래대금', ascending=False).head(12)
                return "krx", top_df
        except:
            continue
            
    return None, None

# 데이터 호출
with st.spinner('미래 유산 목록을 동기화 중입니다...'):
    mode, data = fetch_all_data()

# 3. 레이아웃 렌더링
if data is not None:
    st.markdown(f"<p style='text-align:center; color:#505465; font-size:12px;'>Source: {mode.upper()} Real-time Feed</p>", unsafe_allow_html=True)
    
    # 2열 구성 (모바일 자동 스택)
    cols =
