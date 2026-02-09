import streamlit as st
import pandas as pd
from pykrx import stock
from datetime import datetime, timedelta
import requests

# 1. 테마 및 배경색 설정 (CSS 주입)
st.set_page_config(page_title="QUANT X", layout="wide")

st.markdown("""
    <style>
    /* 메인 배경색 */
    .stApp {
        background-color: #0E1117;
    }
    /* 제목 스타일링 */
    h1 {
        color: #FFD700; /* 골드 포인트 */
        font-family: 'Pretendard', sans-serif;
        font-weight: 800;
        text-align: center;
        padding-bottom: 20px;
    }
    /* 카드형 스타일 (Expander 고치기) */
    .streamlit-expanderHeader {
        background-color: #1A1C24 !important;
        border-radius: 10px !important;
        border: 1px solid #30333D !important;
        color: white !important;
    }
    /* 메트릭 박스 글자색 */
    [data-testid="stMetricValue"] {
        color: #00FFA3 !important; /* 민트색 포인트 */
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 QUANT X : VIP DASHBOARD")

# 2. 데이터 엔진 (네이버 하이브리드)
@st.cache_data(ttl=3600)
def get_dashboard_data():
    try:
        # 네이버 실시간 거래상위 데이터 긁기
        url = "https://finance.naver.com/sise/sise_quant.naver?sosok=1" # 코스닥 중심
        header = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=header)
        df_list = pd.read_html(res.text, encoding='cp949')
        df = df_list[1].dropna().head(12)
        return df[['종목명', '현재가', '등락률', '거래량']]
    except:
        return None

# 데이터 로드
with st.spinner('차트를 동기화 중입니다...'):
    data = get_dashboard_data()

# 3. 레이아웃 배치
if data is not None:
    st.markdown("<p style='text-align:center; color:#808495;'>실시간 거래 데이터 분석 완료</p>", unsafe_allow_html=True)
    
    # 2열로 배치하여 모바일과 PC 모두 대응
    cols = st.columns(2)
    
    for i, (index, row) in enumerate(data.iterrows()):
        # 왼쪽 오른쪽 번갈아가며 배치
        with cols[i % 2]:
            # 카드 디자인
            with st.expander(f"💎 {row['종목명']} ({row['등락률']})"):
                m1, m2 = st.columns(2)
                m1.metric("현재가", f"{row['현재가']:,}원")
                m2.metric("거래량", f"{row['거래량']:,}")
                
                # 버튼 스타일링
                search_url = f"https://finance.naver.com/search/search.naver?query={row['종목명']}"
                st.link_button("📊 상세 차트 분석", search_url, use_container_width=True)
                
    st.divider()
    st.caption("Produced by Gemini-X • Data provided by Naver Finance")
else:
    st.error("서버 점검 중입니다. 내일 아침 다시 만나요!")

