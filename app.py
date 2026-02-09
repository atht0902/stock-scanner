import streamlit as st
import pandas as pd
from pykrx import stock
from datetime import datetime, timedelta
import requests

# 1. 테마 및 애니메이션 설정
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
    
    /* 카드 스타일 */
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

# 2. 데이터 엔진 (무료 하이브리드 소스)
@st.cache_data(ttl=3600)
def fetch_heritage():
    try:
        # 네이버 금융 실시간 데이터 시도
        url = "https://finance.naver.com/sise/sise_quant.naver?sosok=0"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        df = pd.read_html(res.text, encoding='cp949')[1].dropna().head(12)
        return "실시간 포털", df[['종목명', '현재가', '등락률', '거래량']]
    except:
        return None, None

source_name, data = fetch_heritage()

# 3. 메인 화면 구현
if data is not None:
    st.markdown(f"<p style='text-align:center; color:#505465; font-size:12px;'>출처: {source_name}</p>", unsafe_allow_html=True)
    cols = st.columns(2)
    
    for i, row in data.reset_index().iterrows():
        with cols[i % 2]:
            name = row['종목명']
            change_raw = str(row['등락률']).replace('%','').replace('+','')
            
            # 유산 가치 알람 로직 (10% 이상 상승 시 🔥)
            try:
                is_hot = float(change_raw) >= 10.0
            except:
                is_hot = False
            
            icon = "🔥" if is_hot else "💎"
            
            with st.expander(f"{icon} {name} ({row['등락률']})"):
                m1, m2 = st.columns(2)
                m1.metric("현재가", f"{int(row['현재가']):,}원")
                m2.metric("거래량", f"{int(row['거래량']):,}")
                
                # 분석 및 공유 버튼
                b1, b2 = st.columns(2)
                search_url = f"https://finance.naver.com/search/search.naver?query={name}"
                b1.link_button("📊 상세 분석", search_url, use_container_width=True)
                # 간편 공유 (모바일 대응 공유 링크)
                share_link = f"https://social-plugins.line.me/lineit/share?url={search_url}"
                b2.link_button("🔗 유산 공유", share_link, use_container_width=True)
    
    st.divider()
    st.caption("Produced by Hong-Ik Heritage Finder • Premium Free Edition")
else:
    st.markdown("""
        <div style='background-color: #161B22; padding: 25px; border-radius: 15px; border: 1px solid #FDB931; text-align: center;'>
            <h3 style='color: #FDB931; margin: 0;'>⌛ 유산 스캐너 정비 중</h3>
            <p style='color: #808495; margin-top: 10px;'>내일 아침 9시, 장이 열리면 실시간 데이터가 표시됩니다.</p>
        </div>
    """, unsafe_allow_html=True)
