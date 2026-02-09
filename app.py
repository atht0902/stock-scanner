import streamlit as st
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="종목 스캐너 최종", layout="wide")
st.title("🚀 서버 지연 돌파 스캐너")

@st.cache_data(ttl=300)
def get_safe_data():
    # 최근 10일 중 가장 가까운 영업일 데이터 찾기
    for i in range(10):
        dt = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        try:
            df = stock.get_market_ohlcv_by_ticker(dt, market="ALL")
            if df is not None and not df.empty and df['거래대금'].sum() > 0:
                return dt, df
        except:
            continue
    return None, None

# 튜플 언패킹 에러 방지 (가장 중요!)
data_res = get_safe_data()

if data_res and data_res[0] is not None:
    final_dt, market_df = data_res
    st.success(f"✅ {final_dt} 데이터 연결 성공!")

    # 상위 30개 추출
    top_30 = market_df.sort_values(by='거래대금', ascending=False).head(30).copy()
    
    # 수급 데이터 시도
    try:
        df_inv = stock.get_market_net_purchases_of_equities_by_ticker(final_dt, final_dt, "ALL")
    except:
        df_inv = pd.DataFrame()

    display_data = []
    for ticker in top_30.index:
        name = stock.get_market_ticker_name(ticker)
        row = top_30.loc[ticker]
        link = f'<a href="https://finance.naver.com/item/main.naver?code={ticker}" target="_blank" style="text-decoration:none; color:#007bff; font-weight:bold;">{name}</a>'
        
        foreign = 0
        if not df_inv.empty and ticker in df_inv.index:
            foreign = df_inv.loc[ticker, '외국인'] / 100000000

        display_data.append({
            "종목명(차트)": link,
            "현재가": f"{int(row['종가']):,}",
            "등락률": f"{row['등락률']:.2f}%",
            "거래대금(억)": int(row['거래대금']/100000000),
            "외인수급(억)": round(float(foreign), 1)
        })

    st.write("### 🔥 거래 상위 종목 리스트")
    st.write(pd.DataFrame(display_data).to_html(escape=False, index=False), unsafe_allow_html=True)

else:
    st.error("❗ 거래소 서버가 응답하지 않습니다.")
    st.info("현재 밤 시간대 서버 점검 중일 수 있습니다. 10분 뒤에 다시 시도하거나 내일 아침에 확인해 주세요!")
