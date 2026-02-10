import streamlit as st
import pandas as pd
import requests
import time

# 1. 프리미엄 테마 및 CSS (철학 문구 포함)
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

# 3. 초강력 실시간 데이터 엔진 (장중 전용)
@st.cache_data(ttl=10) # 10초마다 갱신하여 실시간성 확보
def get_stock_data(filter_type):
    header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    url = "https://finance.naver.com/sise/sise_market_sum.naver?sosok=0" if "우량주" in filter_type else "https://finance.naver.com/sise/sise_quant.naver?sosok=0"
    
    try:
        response = requests.get(url, headers=header, timeout=5)
        # 테이블을 더 정밀하게 파싱 (여러 테이블 중 실 데이터 테이블 자동 선택)
        dfs = pd.read_html(response.text, encoding='cp949')
        for df in dfs:
            if '종목명' in df.columns and len(df) > 10:
                df = df.dropna(subset=['종목명', '현재가'])
                return df.head(40)
        return None
    except:
        return None

data = get_stock_data(category)

# 4. 화면 출력 로직
if data is not None and not data.empty:
    # 수치형 변환 작업 (에러 방지 강화)
    data['현재가_clean'] = pd.to_numeric(data['현재가'], errors='coerce')
    data['등락률_val'] = data['등락률'].astype(str).str.replace('%','').replace('+','').str.strip()
    data['등락률_num'] = pd.to_numeric(data['등락률_val'], errors='coerce')
    
    # 등락 필터 적용
    if status_filter == "급등주 (5%↑)":
        data = data[data['등락률_num'] >= 5.0]
    elif status_filter == "상승 종목만":
        data = data[data['등락률_num'] > 0]

    if not data.empty:
        # 2열 그리드 배치
        cols = st.columns(2)
        for i, (_, row) in enumerate(data.head(14).iterrows()):
            with cols[i % 2]:
                is_hot = row['등락률_num'] >= 10.0
                icon = "🔥" if is_hot else ("👑" if "우량주" in category else "💎")
                with st.expander(f"{icon} {row['종목명']} (+{row['등락률_val']}%)"):
                    st.metric("현재가", f"{int(row['현재가_clean']):,}원")
                    b1, b2 = st.columns(2)
                    link = f"https://finance.naver.com/search/search.naver?query={row['종목명']}"
                    b1.link_button("📊 분석", link, use_container_width=True)
                    b2.link_button("🔗 공유", f"https://social-plugins.line.me/lineit/share?url={link}", use_container_width=True)
    else:
        st.warning("현재 필터 조건에 맞는 종목이 없습니다.")
else:
    # 정비 중 박스 (데이터 로드 실패 시 보조 로직)
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
