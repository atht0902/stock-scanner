import streamlit as st
import pandas as pd
from pykrx import stock
from datetime import datetime, timedelta
import requests

# 1. 페이지 설정 및 프리미엄 테마
st.set_page_config(page_title="홍익 미래 유산 검색기", layout="wide")

st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    .stApp { background-color: #0A0C10; font-family: 'Pretendard', sans-serif; }
    
    /* 반응형 골드 타이틀 */
    .main-title {
        font-size: clamp(1.4rem, 7vw, 2.8rem);
        background: linear-gradient(to right, #FFD700, #FDB931);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        text-align: center;
        padding: 15px 0px;
        line-height: 1.2;
    }
    .sub-title { color: #808495; text-align: center; font-size: 14px; margin-bottom: 30px; }
    
    /* 카드 디자인 */
    .streamlit-expanderHeader {
        background-color: #161B22 !important;
        border-radius: 12px !important;
        border: 1px solid #30363D !important;
        color: white !important;
        padding: 12px !important;
    }
    [data-testid="stMetricValue"] { color: #FFD700 !important; font-size: 1.5rem !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-title">🏛️ 홍익 미래 유산 검색기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">널리 주식 투자자를 이롭게 하는 미래 자산 발굴 시스템</div>', unsafe_allow_html=True)

# 2. 통합 데이터 로드 (에러 방지 구조)
@st.cache_data(ttl=3600)
def get_safe_data():
    # 시도 1: 네이버 금융 (밤 시간대용)
    try:
        url = "https://finance.naver.com/sise/sise_quant.naver?sosok=0" # 코스피 우선
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        df = pd.read_html(res.text, encoding='cp949')[1].dropna().head(10)
        return "실시간 포털 데이터", df[['종목명', '현재가', '등락률', '거래량']]
    except:
        pass

    # 시도 2: 거래소 (낮 시간대용)
    try:
        dt = datetime.now().strftime("%Y%m%d")
        df = stock.get_market_ohlcv_by_ticker(dt, market="ALL")
        if not df.empty:
            df = df.sort_values(by='거래대금', ascending=False).head(10)
            df['종목명'] = [stock.get_market_ticker_name(t) for t in df.index]
            return "거래소 공식 데이터", df
    except:
        return None, None

# 실행
with st.spinner('미래 유산을 발굴 중입니다...'):
    data_type, df = get_safe_data()

# 3. 화면 출력
if df is not None:
    st.markdown(f"<p style='text-align:center; color:#505465; font-size:12px;'>{data_type} 연결됨</p>", unsafe_allow_html=True)
    
    # 2열 레이아웃
    cols = st.columns(2)
    
    for i, (_,
