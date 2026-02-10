import streamlit as st
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta

# 1. 디자인 (다크 모드 & 골드 포인트)
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

# 2. 헤더
st.title("🔔 홍익 미래 유산 검색기")
st.caption("널리 주식 투자자를 이롭게 하는 미래 자산 발굴 시스템")

# 3. 필터 UI
col1, col2 = st.columns(2)
with col1:
    category = st.selectbox("📂 분류", ["🔥 거래급등 (단기이슈)", "💎 우량주 (중장기)"])
with col2:
    filter_val = st.selectbox("📈 등락 필터", ["전체 보기", "5% 이상", "10% 이상"])

# 4. 데이터 엔진
@st.cache_data(ttl=300)
def fetch_data():
    df = None

    for i in range(10):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        try:
            temp = stock.get_market_ohlcv(date, market="ALL")
            if temp is not None and len(temp) > 0:
                df = temp
                break
        except Exception:
            continue

    if df is None or len(df) == 0:
        return pd.DataFrame(columns=['종목명', '현재가', '등락률', '거래량'])

    # 종목명 매핑
    tickers = df.index.tolist()
    names = []
    for t in tickers:
        try:
            names.append(stock.get_market_ticker_name(t))
        except Exception:
            names.append(t)

    result = pd.DataFrame({
        '종목명': names,
        '현재가': df['종가'].values,
        '등락률': df['등락률'].values,
        '거래량': df['거래량'].values
    })
    return result

# 5. 실행
status_placeholder = st.empty()

try:
    status_placeholder.markdown(
        '<div class="status-box">⌛ 유산 스캐너 엔진 예열 중...</div>',
        unsafe_allow_html=True
    )

    df = fetch_data()

    if df.empty:
        status_placeholder.warning("📭 현재 조회 가능한 데이터가 없습니다. 잠시 후 다시 시도해주세요.")
    else:
        # 필터 적용
        if filter_val == "5% 이상":
            df = df[df['등락률'] >= 5]
        elif filter_val == "10% 이상":
            df = df[df['등락률'] >= 10]

        # 거래량 순 정렬 (상위 50개)
        df = df.sort_values(by='거래량', ascending=False).head(50)

        # 화면 표시용 포맷팅
        display_df = df.copy().reset_index(drop=True)
        display_df.index = display_df.index + 1
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