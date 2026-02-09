import streamlit as st
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="주식 예측 및 패턴 분석기", layout="wide")
st.title("🎯 시가 갭 상승 예측 & 패턴 분석기")

# 1. 데이터 로드 (최근 3일의 실제 영업일을 찾아옴)
@st.cache_data(ttl=600)
def get_final_data():
    found_dates = []
    for i in range(30):
        target_dt = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        try:
            df = stock.get_market_ohlcv_by_ticker(target_dt, market="ALL")
            if df is not None and not df.empty and df['거래대금'].sum() > 0:
                found_dates.append((target_dt, df))
        except: continue
        if len(found_dates) == 3: break
    return found_dates

with st.spinner('과거와 현재 데이터를 매칭 중입니다...'):
    data_list = get_final_data()

if data_list and len(data_list) >= 3:
    # d[0]: 오늘(월), d[1]: 전일(금), d[2]: 전전일(목)
    today_info, prev_info, pprev_info = data_list
    
    st.success(f"✅ 데이터 매칭 성공!")
    st.info(f"📍 분석 기준: {today_info[0]} | 📍 과거 복기: {prev_info[0]}")

    # --- 섹션 1: 과거(전일) 갭 상승 종목 복기 ---
    st.subheader("📝 과거(전일) 갭 상승 종목 복기")
    st.write(f"{prev_info[0]} 아침에 실제로 갭이 높게 떴던 종목들입니다.")
    
    past_results = []
    # 전일(금) 거래대금 상위 50개 분석
    top_prev = prev_info[1].sort_values(by='거래대금', ascending=False).head(50)
    for ticker in top_prev.index:
        if ticker in pprev_info[1].index:
            p_close = pprev_info[1].loc[ticker, '종가']
            t_open = prev_info[1].loc[ticker, '시가']
            if p_close > 0:
                gap = ((t_open - p_close) / p_close) * 100
                if gap >= 3.0: # 3% 이상 갭 상승만 추출
                    past_results.append({
                        '종목명': stock.get_market_ticker_name(ticker),
                        '당시 시가갭': f"{gap:.2f}%",
                        '전날 거래량 증가': f"{prev_info[1].loc[ticker, '거래량']/pprev_info[1].loc[ticker, '거래량']:.1f}배"
                    })
    
    if past_results:
        st.dataframe(pd.DataFrame(past_results), use_container_width=True)
    else:
        st.write("해당 날짜에 조건에 맞는 갭 상승 종목이 없습니다.")

    st.divider()

    # --- 섹션 2: 내일 시가 갭상승 예측 ---
    st.subheader("🔮 내일 시가 갭상승 후보")
    st.write(f"오늘({today_info[0]}) 데이터를 분석하여 내일 아침 갭 확률이 높은 종목을 추천합니다.")
    
    predictions = []
    today_df = today_info[1]
    prev_df = prev_info[1]
    
    for ticker in today_df.index:
        if ticker in prev_df.index:
            t_money = today_df.loc[ticker, '거래대금'] / 100000000
            if t_money < 300: continue
            
            t_vol = today_df.loc[ticker, '거래량']
            p_vol = prev_df.loc[ticker, '거래량']
            t_close = today_df.loc[ticker, '종가']
            t_high = today_df.loc[ticker, '고가']
            
            # 예측 로직: 거래량 1.5배 이상 & 고점 부근 마감
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
        st.warning("내일 예측 후보가 아직 없습니다.")

else:
    st.error("영업일 데이터를 찾지 못했습니다. [Clear Cache]를 한 번 눌러주세요.")
