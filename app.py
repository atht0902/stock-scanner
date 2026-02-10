import streamlit as st
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="홍익 미래 유산 검색기", layout="centered")

st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #0e1117; color: white; }
    .stSelectbox label { color: #fffd01 !important; font-weight: bold; }
    .status-box { 
        padding: 20px; border-radius: 10px; border: 1px solid #fffd01; 
        text-align: center; background-color: #1a1c24; margin-bottom: 20px;
    }
    th { background-color: #262730 !important; color: #fffd01 !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔔 홍익 미래 유산 검색기")
st.caption("널리 주식 투자자를 이롭게 하는 미래 자산 발굴 시스템")

col1, col2 = st.columns(2)
with col1:
    category = st.selectbox("📂 분류", ["🔥 거래급등 (단기이슈)", "💎 우량주 (중장기)"])
with col2:
    filter_val = st.selectbox("📈 등락 필터", ["전체 보기", "5% 이상", "10% 이상"])

@st.cache_data(ttl=300)
def fetch_data():
    today = datetime.now().strftime("%Y%m%d")
    # 오늘 데이터가 없으면 최근 거래일 자동 조회
    for i in range(5):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        try:
            df = stock.get_market_ohlcv(date, market="ALL")
            if len(df) > 0:
                break
        except:
            continue
    
    # 종목명 매핑
    tickers = df.index.tolist()
    names = [stock.get_market_ticker_name(t) for t in tickers]
    
    result = pd.DataFrame({
        '종목명': names,
        '현재가': df['종가'].values,
        '등락률': df['등락률'].values,
        '거래량': df['거래량'].values
    })
    return result

status_placeholder = st.empty()

try:
    status_placeholder.markdown(
        '<div class="status-box">⌛ 유산 스캐너 엔진 예열 중...</div>', 
        unsafe_allow_html=True
    )
    
    df = fetch_data()
    
    if filter_val == "5% 이상":
        df = df[df['등락률'] >= 5]
    elif filter_val == "10% 이상":
        df = df[df['등락률'] >= 10]
        
    df = df.sort_values(by='거래량', ascending=False).head(50)
    
    display_df = df.copy()
    display_df['등락률'] = display_df['등락률'].apply(lambda x: f"{x:+.2f}%")
    display_df['현재가'] = display_df['현재가'].apply(lambda x: f"{x:,.0f}원")
    display_df['거래량'] = display_df['거래량'].apply(lambda x: f"{x:,.0f}")

    status_placeholder.empty()
    st.success(f"✅ {datetime.now().strftime('%H:%M:%S')} 데이터 동기화 완료")
    st.table(display_df)

except Exception as e:
    status_placeholder.error(f"⚠️ 엔진 오류: {e}")

st.markdown("---")
st.caption("Produced by Hong-Ik Heritage Finder • Premium Edition")