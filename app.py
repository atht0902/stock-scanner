import streamlit as st
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta, timezone

# 한국 시간대 설정 (Streamlit Cloud는 UTC 기준이라 KST 변환 필수)
KST = timezone(timedelta(hours=9))

st.set_page_config(page_title="홍익 미래 유산 검색기", layout="centered")

st.markdown("""
<style>
    /* 전체 배경 */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 50%, #0a0a0f 100%);
        color: #e0e0e0;
    }
    [data-testid="stHeader"] { background: transparent; }

    /* 헤더 영역 */
    .main-header {
        text-align: center;
        padding: 1.5rem 0.5rem 1rem;
    }
    .main-header h1 {
        font-size: clamp(1.3rem, 5vw, 2rem);
        color: #ffd700;
        margin: 0;
        white-space: nowrap;
    }
    .main-header p {
        color: #888;
        font-size: clamp(0.7rem, 2.5vw, 0.9rem);
        margin-top: 4px;
    }

    /* 상태 박스 */
    .status-box {
        padding: 14px;
        border-radius: 12px;
        border: 1px solid rgba(255,215,0,0.3);
        text-align: center;
        background: rgba(255,215,0,0.05);
        margin: 10px 0;
        font-size: 0.95rem;
    }

    /* 테이블 스타일 */
    .stTable table {
        width: 100%;
        font-size: clamp(0.7rem, 2.5vw, 0.9rem);
    }
    .stTable th {
        background-color: #1a1a2e !important;
        color: #ffd700 !important;
        font-size: clamp(0.7rem, 2.5vw, 0.85rem);
        padding: 8px 6px !important;
        white-space: nowrap;
    }
    .stTable td {
        padding: 6px !important;
        white-space: nowrap;
        color: #e0e0e0 !important;
    }

    /* 셀렉트박스 라벨 */
    .stSelectbox label {
        color: #ffd700 !important;
        font-weight: 600;
        font-size: 0.85rem;
    }

    /* 푸터 */
    .footer {
        text-align: center;
        color: #555;
        font-size: 0.75rem;
        padding: 20px 0 10px;
        border-top: 1px solid #222;
        margin-top: 20px;
    }

    /* selectbox 간격 줄이기 */
    [data-testid="stHorizontalBlock"] { gap: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# 헤더
st.markdown("""
<div class="main-header">
    <h1>🔔 홍익 미래유산 검색기</h1>
    <p>널리 주식 투자자를 이롭게 하는 미래 자산 발굴 시스템</p>
</div>
""", unsafe_allow_html=True)

# 필터 UI
col1, col2 = st.columns(2)
with col1:
    category = st.selectbox("📂 분류", ["🔥 거래급등 (단기이슈)", "💎 우량주 (중장기)"])
with col2:
    filter_val = st.selectbox("📈 등락 필터", ["전체 보기", "5% 이상", "10% 이상"])

# 데이터 엔진
@st.cache_data(ttl=300)
def fetch_data():
    now_kst = datetime.now(KST)
    df = None
    found_date = ""

    for i in range(10):
        date = (now_kst - timedelta(days=i)).strftime("%Y%m%d")
        try:
            temp = stock.get_market_ohlcv(date, market="ALL")
            if temp is not None and len(temp) > 0:
                df = temp
                found_date = date
                break
        except Exception:
            continue

    if df is None or len(df) == 0:
        return pd.DataFrame(columns=['종목명', '현재가', '등락률', '거래량']), ""

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
    return result, found_date

# 실행
status_placeholder = st.empty()

try:
    status_placeholder.markdown(
        '<div class="status-box">⏳ 유산 스캐너 엔진 가동 중...</div>',
        unsafe_allow_html=True
    )

    df, data_date = fetch_data()

    if df.empty:
        status_placeholder.warning("📭 현재 조회 가능한 데이터가 없습니다. 장 마감 후 다시 시도해주세요.")
    else:
        # 필터 적용
        if filter_val == "5% 이상":
            df = df[df['등락률'] >= 5]
        elif filter_val == "10% 이상":
            df = df[df['등락률'] >= 10]

        # 거래량 순 정렬 (상위 30개)
        df = df.sort_values(by='거래량', ascending=False).head(30)

        # 포맷팅
        display_df = df.copy().reset_index(drop=True)
        display_df.index = display_df.index + 1
        display_df['등락률'] = display_df['등락률'].apply(lambda x: f"{x:+.2f}%")
        display_df['현재가'] = display_df['현재가'].apply(lambda x: f"{x:,.0f}원")
        display_df['거래량'] = display_df['거래량'].apply(lambda x: f"{x:,.0f}")

        status_placeholder.empty()

        # 기준일 표시
        formatted_date = f"{data_date[:4]}.{data_date[4:6]}.{data_date[6:]}"
        now_kst = datetime.now(KST)
        st.success(f"✅ {formatted_date} 기준 | {now_kst.strftime('%H:%M')} 동기화 | TOP {len(display_df)}")
        st.table(display_df)

except Exception as e:
    status_placeholder.error(f"⚠️ 엔진 오류: {e}")

# 푸터
st.markdown('<div class="footer">Produced by Hong-Ik Heritage Finder • Premium Edition</div>', unsafe_allow_html=True)