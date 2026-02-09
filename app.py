import streamlit as st
import pandas as pd
from pykrx import stock
from datetime import datetime, timedelta
import requests

# 1. 테마 및 반응형 디자인 설정
st.set_page_config(page_title="홍익 미래 유산 검색기", layout="wide")

st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    .stApp { background-color: #0A0C10; font-family: 'Pretendard', sans-serif; }
    .main-title {
        font-size: clamp(1.4rem, 7vw, 2.5rem);
        background: linear-gradient(to right, #FFD700, #FDB931);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        text-align: center;
        padding: 10px 0px;
    }
    .sub-title { color: #808495; text-align: center; font-size: 14px; margin-bottom: 25px; }
    .streamlit-expanderHeader {
        background-color: #161B22 !important;
        border-radius: 12px !important;
        border: 1px solid #30363D !important;
        color: white !important;
    }
    [data-testid="stMetricValue"] { color: #FFD700 !important; font-size: 1.4rem !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-title">🏛️ 홍익 미래 유산 검색기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">널리 주식 투자자를 이롭게 하는 자산 발굴 시스템</div>', unsafe_allow_html=True)

# 2. 데이터 수집 함수 (안정성 강화)
@st.cache_data(ttl=3600)
def get_heritage_data():
    # 시도 1: 네이버 금융 실시간 순위
    try:
        url = "https://finance.naver.com/sise/sise_quant.naver?sosok=0"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        df = pd.read_html(res.text, encoding='cp949')[1].dropna().head(10)
        return "실시간 포털 순위", df[['종목명', '현재가', '등락률', '거래량']]
    except:
        pass

    # 시도 2: 거래소 공식 데이터 (영업일 기준)
    try:
        today = datetime.now().strftime("%Y%m%d")
        df_krx = stock.get_market_ohlcv_by_ticker(today, market="ALL")
        if not df_krx.empty:
            df_krx = df_krx.sort_values(by='거래대금', ascending=False).head(10)
            df_krx['종목명'] = [stock.get_market_ticker_name(t) for t in df_krx.index]
            return "거래소 공식 마감 데이터", df_krx
    except:
        return None, None

# 데이터 실행
with st.spinner('미래 유산을 발굴하는 중...'):
    source, final_df = get_heritage_data()

# 3. 화면 렌더링
if final_df is not None:
    st.markdown(f"<p style='text-align:center; color:#505465; font-size:12px;'>데이터 출처: {source}</p>", unsafe_allow_html=True)
    
    # 2열 배치 (모바일 자동 스택)
    cols = st.columns(2)
    
    for i, row in final_df.reset_index().iterrows():
        with cols[i % 2]:
            name = row['종목명']
            change = row['등락률']
            # 가격/거래량 정보 추출 (데이터 소스에 따라 컬럼명이 다를 수 있음 대응)
            price = row.get('현재가', row.get('종가', 0))
            volume = row.get('거래량', row.get('거래대금', 0))
            
            with st.expander(f"💎 {name} ({change})"):
                m1, m2 = st.columns(2)
                m1.metric("현재가", f"{int(price):,}원")
                # 거래량 단위 처리 (억 단위/주 단위 구분 없이 출력)
                val_text = f"{int(volume/100000000)}억" if volume > 10000000 else f"{int(volume):,}주"
                m2.metric("규모", val_text)
                
                url = f"https://finance.naver.com/search/search.naver?query={name}"
                st.link_button("📊 상세 유산 분석", url, use_container_width=True)
    
    st.divider()
    st.caption("Produced by Hong-Ik Heritage Finder • Premium Edition")

else:
    st.error("현재 모든 데이터 서버가 응답하지 않습니다. 잠시 후 다시 시도해주세요.")
