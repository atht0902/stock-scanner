import streamlit as st
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="주식 예측 및 패턴 분석기", layout="wide")
st.title("🎯 시가 갭 상승 예측 & 패턴 분석기")

# 캐시 이름을 바꿔서 강제로 새로 읽게 만듭니다 (v2)
@st.cache_data(ttl=600)
def get_data_v2():
    found_dates = []
    # 오늘부터 과거 30일까지 넉넉하게 스캔
    for i in range(30):
        target_dt = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        try:
            # OHLCV 데이터를 시도
            df = stock.get_market_ohlcv_by_ticker(target_dt, market="ALL")
            # 데이터가 존재하고 실제 거래가 일어난 날인지 검증
            if df is not None and not df.empty and df['거래대금'].sum() > 0:
                found_dates.append((target_dt, df))
        except:
            continue
        
        # 3일치 찾으면 즉시 종료
        if len(found_dates) == 3:
            break
    return found_dates

with st.spinner('과거 영업일을 끈질기게 찾는 중...'):
    data_list = get_data_v2()

if data_list and len(data_list) >= 3:
    today_info, prev_info, pprev_info = data_list
    st.success(f"✅ 데이터 로드 성공!")
    st.info(f"기준일: {today_info[0]} | 전일: {prev_info[0]} | 전전일: {pprev_info[0]}")
    
    # --- 이하 분석 로직은 동일 (생략 가능하지만 전체 덮어쓰기용으로 유지) ---
    st.subheader("🔮 내일 시가 갭상승 후보")
    predictions = []
    for ticker in today_info[1].index:
        if ticker in prev_info[1].index:
            t_money = today_info[1].loc[ticker, '거래대금'] / 100000000
            if t_money < 300: continue
            
            t_vol = today_info[1].loc[ticker, '거래량']
            p_vol = prev_info[1].loc[ticker, '거래량']
            t_close = today_info[1].loc[ticker, '종가']
            t_high = today_info[1].loc[ticker, '고가']
            
            if p_vol > 0 and t_vol > p_vol * 1.5 and t_close > (t_high * 0.97):
                predictions.append({
                    '종목명': stock.get_market_ticker_name(ticker),
                    '거래대금(억)': f"{t_money:,.0f}",
                    '거래량증가': f"{t_vol/p_vol:.1f}배",
                    '현재가': f"{t_close:,.0f}"
                })
    if predictions:
        st.dataframe(pd.DataFrame(predictions), use_container_width=True)
    else:
        st.warning("조건에 맞는 종목이 없습니다.")
else:
    st.error("캐시를 비운 후 다시 시도해 주세요. (우측 상단 메뉴 -> Clear cache)")
