import streamlit as st
import pandas as pd
import requests

# 1. 디자인 및 테마 설정
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
        font-weight: 900; text-align: center; padding-top: 20px;
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

# 3. 데이터 엔진 (복수 경로 스캔 방식)
@st.cache_data(ttl=30) # 30초마다 갱신
def fetch_stock_data(target):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/110.0.0.0 Safari/537.36'}
    # 거래급등은 거래량 순, 우량주는 시총 순 URL 사용
    url = "https://finance.naver.com/sise/sise_quant.naver" if "거래" in target else "https://finance.naver.com/sise/sise_market_sum.naver"
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        # 모든 테이블을 훑어서 종목명이 있는 테이블 강제 추출
        dfs = pd.read_html(response.text, encoding='cp949')
        for df in dfs:
            if '종목명' in df.columns and len(df) > 5:
                return df.dropna(subset=['종목명', '현재가'])
        return None
    except:
        return None

# 데이터 호출
data = fetch_stock_data(category)

# 4. 화면 출력 (그리드)
if data is not None and not data.empty:
    # 데이터 정리 (특수문자 제거 및 숫자화)
    data['현재가_num'] = pd.to_numeric(data['현재가'], errors='coerce')
    data['등락률_num'] = data['등락률'].astype(str).str.replace('%','').replace('+','').str.strip().apply(pd.to_numeric, errors='coerce')
    
    # 필터 적용
    temp_df = data.copy()
    if status_filter == "급등주 (5%↑)":
        temp_df = temp_df[temp_df['등락률_num'] >= 5.0]
    elif status_filter == "상승 종목만":
        temp_df = temp_df[temp_df['등락률_num'] > 0]

    if not temp_df.empty:
        cols = st.columns(2)
        # 상위 12개 유산 출력
        for i, (_, row) in enumerate(temp_df.head(12).iterrows()):
            with cols[i % 2]:
                icon = "🔥" if row['등락률_num'] >= 10 else ("👑" if "우량주" in category else "💎")
                with st.expander(f"{icon} {row['종목명']} ({row['등락률_num']}%)"):
                    st.metric("현재가", f"{int(row['현재가_num']):,}원")
                    b1, b2 = st.columns(2)
                    link = f"https://finance.naver.com/search/search.naver?query={row['종목명']}"
                    b1.link_button("📊 분석", link, use_container_width=True)
                    b2.link_button("🔗 공유", f"https://social-plugins.line.me/lineit/share?url={link}", use_container_width=True)
    else:
        st.warning("선택한 필터 조건에 맞는 종목이 없습니다.")
else:
    # ❌ 데이터 실패 시에만 정비 중 출력
    st.markdown("""
        <div class="maintenance-box">
            <h2 style='color: #FDB931; margin: 0; font-size: 24px;'>⌛ 유산 스캐너 엔진 예열 중</h2>
            <p style='color: #808495; margin-top: 15px; font-size: 15px;'>
                실시간 거래 데이터를 동기화하고 있습니다.<br>
                잠시만 기다려주시거나 <b>새로고침(F5)</b>을 눌러주세요.
            </p>
        </div>
    """, unsafe_allow_html=True)

st.divider()
st.caption("Produced by Hong-Ik Heritage Finder • Premium Edition")
