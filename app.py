import streamlit as st
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="종목 스캐너 최종구조", layout="wide")
st.title("🚀 서버 지연 돌파 스캐너")

# 캐시 설정을 더 유연하게 변경
@st.cache_data(show_spinner=False)
def fetch_market_data(days_back=0):
    target_dt = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d")
    try:
        # 1. 가격 데이터 시도
        df = stock.get_market_ohlcv_by_ticker(target_dt, market="ALL")
        if df.empty: return None
        return df, target_dt
    except:
        return None

# 데이터 로딩 시도 (재시도 로직 추가)
with st.spinner('거래소 서버와 연결을 시도 중입니다...'):
    market_df = None
    final_dt = ""
    for i in range(10): # 최근 10일 중 데이터가 있는 날을 찾을 때까지
        market_df, final_dt = fetch_market_data(i)
        if market_df is not None: break
        time.sleep(0.5) # 서버 부하 방지용 짧은 휴식

if market_df is not None:
    st.success(f"✅ {final_dt} 데이터 연결 성공!")

    # 상위 30개만 가볍게 추출
    top_30 = market_df.sort_values(by='거래대금', ascending=False).head(30).copy()
    
    # 추가 데이터(수급) 시도 - 실패해도 멈추지 않음
    try:
        df_inv = stock.get_market_net_purchases_of_equities_by_ticker(final_dt, final_dt, "ALL")
    except:
        df_inv = pd.DataFrame()

    display_data = []
    for ticker in top_30.index:
        name = stock.get_market_ticker_name(ticker)
        row = top_30.loc[ticker]
        
        # 네이버 차트 링크
        link = f'<a href="https://finance.naver.com/item/main.naver?code={ticker}" target="_blank">{name}</a>'
        
        # 수급 계산 (안전하게)
        foreign = df_inv.loc[ticker, '외국인'] / 100000000 if ticker in df_inv.index else 0
        
        display_data.append({
            "종목명(차트)": link,
            "현재가": f"{int(row['종가']):,}",
            "등락률": f"{row['등락률']:.2f}%",
            "거래대금(억)": int(row['거래대금']/100000000),
            "외인수급(억)": round(foreign, 1)
        })

    # 최종 출력
    st.write(pd.DataFrame(display_data).to_html(escape=False, index=False), unsafe_allow_html=True)

else:
    st.error("❗ 현재 거래소 서버 점검 중일 가능성이 높습니다.")
    st.warning("방법: 5분 뒤 브라우저를 '새로고침' 하거나, 내일 아침에 접속하면 100% 작동합니다.")
