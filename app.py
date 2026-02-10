import streamlit as st
import FinanceDataReader as fdr
from datetime import datetime
import pandas as pd

# 1. 페이지 설정 및 테마 디자인 (CSS)
st.set_page_config(page_title="홍익 미래 유산 검색기", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stSelectbox label { color: #fffd01 !important; font-weight: bold; font-size: 1.1rem; }
    .stTable { background-color: #1a1c24; border-radius: 10px; }
    .status-msg { 
        padding: 15px; 
        border-radius: 8px; 
        background-color: #1a1c24; 
        border: 1px solid #fffd01;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    th { background-color: #262730 !important; color: #fffd01 !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. 타이틀 섹션
st.title("🔔 홍익 미래 유산 검색기")
st.write("널리 주식 투자자를 이롭게 하는 미래 자산 발굴 시스템")

# 3. 필터 UI
col1, col2 = st.columns(2)
with col1:
    category = st.selectbox("📂 분류", ["🔥 거래급등 (단기이슈)", "💎 우량주 (중장기)"])
with col2:
    filter_val = st.selectbox("📈 등락 필터", ["전체 보기", "5% 이상", "10% 이상", "15% 이상"])

# 4. 실시간 데이터 엔진 연결 (핵심 로직)
@st.cache_data(ttl=60) # 1분마다 데이터 갱신
def get_realtime_data():
    # 한국 거래소 전종목 리스트 가져오기
    df = fdr.StockListing('KRX')
    # 필요한 컬럼만 추출 (종목명, 현재가, 등락률, 거래량)
    df = df[['Name', 'Close', 'ChgRate', 'Volume']]
    df.columns = ['종목명', '현재가', '등락률', '거래량']
    return df

status_placeholder = st.empty()

try:
    status_placeholder.markdown('<div class="status-msg">⌛ 유산 스캐너 엔진 예열 중... (실시간 데이터 동기화)</div>', unsafe_allow_html=True)
    
    # 데이터 호출
    raw_df = get_realtime_data()
    
    # 필터링 로직
    if filter_val == "5% 이상":
        processed_df = raw_df[raw_df['등락률'] >= 5]
    elif filter_val == "10% 이상":
        processed_df = raw_df[raw_df['등락률'] >= 10]
    elif filter_val == "15% 이상":
        processed_df = raw_df[raw_df['등락률'] >= 15]
    else:
        processed_df = raw_df

    # 거래량 순 정렬 (거래급등 모드일 때)
    processed_df = processed_df.sort_values(by='거래량', ascending=False).head(50)
    
    # 보기 좋게 포맷팅
    processed_df['등락률'] = processed_df['등락률'].apply(lambda x: f"{x:+.2f}%")
    processed_df['거래량'] = processed_df['거래량'].apply(lambda x: f"{x:,}")
    processed_df['현재가'] = processed_df['현재가'].apply(lambda x: f"{x:,}원")

    status_placeholder.empty()
    st.success(f"✅ {datetime.now().strftime('%H:%M:%S')} 데이터 동기화 완료")
    
    # 최종 결과 출력
    st.table(processed_df)

except Exception as e:
    status_placeholder.error(f"⚠️ 엔진 연결 오류: {e}")
    st.info("API 호출 한도를 초과했거나 네트워크 문제입니다. 잠시 후 새로고침 해주세요.")

st.markdown("---")
st.caption("Produced by Hong-Ik Heritage Finder • Premium Edition")
