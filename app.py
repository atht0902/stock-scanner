import streamlit as st
import pandas as pd
from pykrx import stock
from datetime import datetime, timedelta
import requests

# 1. 모바일 최적화 및 프리미엄 테마 설정
st.set_page_config(page_title="홍익 미래 유산 검색기", layout="wide")

st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    .stApp {
        background-color: #0A0C10; /* 조금 더 깊은 블랙 네이비 */
        font-family: 'Pretendard', sans-serif;
    }

    /* 제목: 홍익 미래 유산 검색기 커스텀 */
    .main-title {
        font-size: clamp(1.4rem, 7vw, 2.8rem); 
        background: linear-gradient(to right, #FFD700, #FDB931); /* 골드 그라데이션 */
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        text-align: center;
        padding: 15px 0px;
        line-height: 1.2;
        letter-spacing: -0.07rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }

    .sub-title {
        color: #808495;
        text-align: center;
        font-size: 14px;
        margin-bottom: 30px;
    }

    /* 카드형 스타일 개선 */
    .streamlit-expanderHeader {
        background-color: #161B22 !important;
        border-radius: 12px !important;
        border: 1px solid #30363D !important;
        padding: 15px !important;
    }

    /* 메트릭 박스 스타일 */
    [data-testid="stMetricValue"] {
        color: #FFD700 !important; /* 숫자도 골드로 통일 */
    }
    </style>
    """, unsafe_allow_html=True)

# 반응형 제목 적용
st.markdown('<div class="main-title">🏛️ 홍익 미래 유산 검색기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">널리 주식 투자자를 이롭게 하는 미래 자산 발굴 시스템</div>', unsafe_allow_html=True)

# 2. 데이터 엔진 (네이버 하이브리드)
@st.cache_data(ttl=3600)
def get_heritage_data():
    try:
        url = "https://finance.naver.com/sise/sise_quant.naver?sosok=1"
        header = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=header)
        df_list = pd.read_html(res.text, encoding='cp949')
        df = df_list[1].dropna().head(12)
        return df[['종목명', '현재가', '등락률', '거래량']]
    except:
        return None

with st.spinner('미래 유산을 스캔 중입니다...'):
    data = get_heritage_data()

# 3. 레이아웃 배치
if data is not None:
    cols = st.columns(2)
    
    for i, (index, row) in enumerate(data.iterrows()):
        with cols[i % 2]:
            # 카드 내부 디자인
            with st.expander(f"📜 {row['종목명']} | {row['등락률']}"):
                m1, m2 = st.columns(2)
                m1.metric("현재가", f"{row['현재가']:,}원")
                m2.metric("거래량", f"{row['거래량']:,}")
                
                chart_url = f"https://finance.naver.com/search/search.naver?query={row['종목명']}"
                st.link_button("🧭 유산 상세 분석", chart_url, use_container_width=True)
                
    st.divider()
    st.caption("Produced by Hong-Ik Heritage Finder • Premium Edition")
else:
