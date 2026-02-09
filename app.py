import streamlit as st
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta

# 1. 모바일 최적화 설정
st.set_page_config(
    page_title="친구들과 쓰는 퀀트툴",
    layout="wide", # PC에서는 넓게
    initial_sidebar_state="collapsed" # 모바일에서 메뉴 숨기기
)

st.title("📱 퀀트 스캐너 (모바일 최적화)")

# 2. 캐싱 강화 (TTL을 늘리고 데이터 보존)
@st.cache_data(ttl=3600, show_spinner=False) # 1시간 동안 캐시 유지
def get_robust_data():
    # 최근 10일 중 가장 데이터가 잘 나오는 날 찾기
    for i in range(10):
        dt = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        try:
            df = stock.get_market_ohlcv_by_ticker(dt, market="ALL")
            if df is not None and not df.empty and df['거래대금'].sum() > 0:
                # 수급 데이터도 한꺼번에 캐싱
                df_inv = stock.get_market_net_purchases_of_equities_by_ticker(dt, dt, "ALL")
                return dt, df, df_inv
        except:
            continue
    return None, None, None

with st.spinner('최신 데이터를 동기화 중입니다...'):
    target_dt, df_ohlcv, df_inv = get_robust_data()

if df_ohlcv is not None:
    st.success(f"✅ {target_dt} 데이터 로드 완료")
    
    # 데이터 가공 (거래대금 상위 20개만 - 모바일 가독성 위해 줄임)
    top_df = df_ohlcv.sort_values(by='거래대금', ascending=False).head(20).copy()
    
    # 3. 모바일용 레이아웃 (컬럼 분할)
    # 모바일에서는 컬럼이 자동으로 아래로 쌓입니다.
    for ticker in top_df.index:
        name = stock.get_market_ticker_name(ticker)
        row = top_df.loc[ticker]
        
        # 수급 계산
        f_buy = 0
        if df_inv is not None and ticker in df_inv.index:
            f_buy = df_inv.loc[ticker, '외국인'] / 100000000

        # 모바일 최적화 카드형 UI
        with st.expander(f"📍 {name} ({row['등락률']:.2f}%)"):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("현재가", f"{int(row['종가']):,}원")
                st.metric("외인수급", f"{f_buy:.1;1}억")
            with col2:
                st.metric("거래대금", f"{int(row['거래대금']/100000000)}억")
                # 차트 버튼 (새 창 열기)
                chart_url = f"https://finance.naver.com/item/main.naver?code={ticker}"
                st.link_button("📊 네이버 차트", chart_url, use_container_width=True)

else:
    st.error("❗ 현재 서버 점검 중입니다.")
    st.info("오늘 낮에 가져온 데이터가 있는지 확인 중...")
