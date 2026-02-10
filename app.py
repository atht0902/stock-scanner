import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# 1. 페이지 및 프리미엄 테마 설정
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
        padding-top: 20px;
    }
    .sub-title { color: #808495; text-align: center; font-size: 14px; margin-bottom: 25px; }
    .maintenance-box {
        background-color: #161B22; padding: 35px 20px; border-radius: 20px;
        border: 1px solid #FDB931; text-align: center; margin-top: 10px;
    }
    .stSelectbox label { color: #FFD700 !important; font-weight: bold; }
    .streamlit-expanderHeader { background-color: #161B22 !important; border-radius: 12px !important; border: 1px solid #30363D !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-title">🏛️ 홍익 미래 유산 검색기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">널리 주식 투자자를 이롭게 하는 미래 자산 발굴 시스템</div>', unsafe_allow_html=True)

# 2. 상단 필터
col_f1, col_f2 = st.columns(2)
with col_f1:
    category = st.selectbox("📂 분류", ["🔥 거래급등 (단기이슈)", "👑 우량주 (시총상위)"])
with col_f2:
    status_filter = st.selectbox("📈 등락 필터", ["전체 보기", "상승 종목만", "급등주 (5%↑)"])

# 3. 강화된 데이터 엔진 (데이터 누락 방지 로직)
@st.cache_data(ttl=60) # 장중이므로 캐시 시간을 1분으로 단축
def get_live_data(filter_type):
    try:
        header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        # 분류에 따른 URL 설정
        if "우량주" in filter_type:
            url = "https://finance.naver.com/sise/sise_market_sum.naver?sosok=0"
        else:
            url = "https://finance.naver.com/sise/sise_quant.naver?sosok=0"
            
        res = requests.get(url, headers=header, timeout=10)
        df_list = pd.read_html(res.text, encoding='cp949')
        
        # 유효한 테이블 찾기
        for df in df_list:
            if '종목명' in df.columns and len(df) > 5:
                # 불필요한 행 제거 및 정리
                df = df.dropna(subset=['종목명', '현재가'])
                return df.head(30)
        return None
    except Exception as e:
        return None

# 데이터 호출
with st.spinner('미래 유산을 실시간으로 스캔 중...'):
    data = get_live_data(category)

# 4. 화면 렌더링
if data is not None and not data.empty:
    # 데이터 타입 강제 변환 (에러 방지)
    data['현재가'] = pd.to_numeric(data['현재가'], errors='coerce')
    data['등락률'] = data['등락률'].astype(str).str.replace('%','').replace('+','').str.strip()
    data['등락률_num'] = pd.to_numeric(data['등락률'], errors='coerce')
    
    # 등락 필터 적용
    if status_filter == "급등주 (5%↑)":
        data = data[data['등락률_num'] >= 5.0]
    elif status_filter == "상승 종목만":
        data = data[data['등락률_num'] > 0]

    if not data.empty:
        cols = st.columns(2)
        for i, (_, row) in enumerate(data.head(12).iterrows()):
            with cols[i % 2]:
                is_hot = row['등락률_num'] >= 10.0
                icon = "🔥" if is_hot else ("👑" if "우량주" in category else "💎")
                with st.expander(f"{icon} {row['종목명']} ({row['등락률']}%)"):
                    st.metric("현재가", f"{int(row['현재가']):,}원")
                    b1, b2 = st.columns(2)
                    search_url = f"https://finance.naver.com/search/search.naver?query={row['종목명']}"
                    b1.link_button("📊 분석", search_url, use_container_width=True)
                    b2.link_button("🔗 공유", f"https://social-plugins.line.me/lineit/share?url={search_url}", use_container_width=True)
    else:
        st.warning("현재 조건에 맞는 종목이 없습니다. 필터를 변경해 보세요!")
else:
    # 정비 중 카드 (데이터 수집 실패 시)
    st.markdown("""
        <div class="maintenance-box">
            <h2 style='color: #FDB931; margin: 0; font-size: 24px;'>⌛ 유산 스캐너 정비 중</h2>
            <p style='color: #808495; margin-top: 15px; font-size: 15px;'>
                데이터를 불러오는 중입니다. 잠시 후 새로고침(F5) 해주세요.<br>
                장 시작 직후에는 데이터 동기화에 시간이 걸릴 수 있습니다.
            </p>
        </div>
    """, unsafe_allow_html=True)

st.divider()
st.caption("Produced by Hong-Ik Heritage Finder • Premium Edition")
