import streamlit as st
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta

# 1. 설정 및 기본 데이터 로드
st.set_page_config(page_title="주식 예측 및 추세 분석기", layout="wide")
st.title("🎯 시가 갭 상승 예측 & 패턴 분석기")

@st.cache_data(ttl=600)
def get_prediction_data():
    # 최근 10일치 데이터 확보
    dates = []
    for i in range(20):
        target_date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        df = stock.get_market_ohlcv_by_ticker(target_date, market="ALL")
        if not df.empty and df['거래대금'].sum() > 0:
            dates.append((target_date, df))
        if len(dates) == 3: break
    
    if len(dates) < 3: return None
    
    # dates[0]: 오늘, dates[1]: 어제, dates[2]: 그제
    return dates

data_bundle = get_prediction_data()

if data_bundle:
    today_info, prev_info, pprev_info = data_bundle
    
    # --- 섹션 1: 어제 갭 상승 성공 종목 복기 (패턴 학습) ---
    with st.expander("📝 어제(과거) 갭 상승 종목과 전날의 공통점"):
        success_cases = []
        # 어제 상위 50위 중 갭 3% 이상인 종목 찾기
        top_prev = prev_info[1].sort_values(by='거래대금', ascending=False).head(50)
        for ticker in top_prev.index:
            if ticker in pprev_info[1].index:
                p_close = pprev_info[1].loc[ticker, '종가']
                t_open = prev_info[1].loc[ticker, '시가']
                gap = ((t_open - p_close) / p_close) * 100
                if gap >= 3.0:
                    # 전전날(그제) 특징 분석
                    vol_increase = pprev_info[1].loc[ticker, '거래량'] / 1000000 # 백만주
                    success_cases.append({'name': stock.get_market_ticker_name(ticker), 'gap': gap, 'prev_vol': vol_increase})
        
        st.table(pd.DataFrame(success_cases))

    # --- 섹션 2: 내일 갭 상승 예측 (오늘의 패턴 포착) ---
    st.header("🔮 내일 시가 갭상승 후보 종목")
    st.info("조건: 오늘 거래대금 500억 이상 + 전일 대비 거래량 2배 폭증 + 종가가 고가 근처")
    
    today_df = today_info[1]
    prev_df = prev_info[1]
    
    predictions = []
    for ticker in today_df.sort_values(by='거래대금', ascending=False).head(100).index:
        if ticker in prev_df.index:
            t_vol = today_df.loc[ticker, '거래량']
            p_vol = prev_df.loc[ticker, '거래량']
            t_money = today_df.loc[ticker, '거래대금'] / 100000000
            t_close = today_df.loc[ticker, '종가']
            t_high = today_df.loc[ticker, '고가']
            
            # 예측 필터: 거래량이 전일 대비 2배 이상 & 거래대금 500억 이상 & 고가 마감 근처
            if t_vol > p_vol * 2 and t_money > 500 and t_close > (t_high * 0.98):
                predictions.append({
                    '종목명': stock.get_market_ticker_name(ticker),
                    '오늘 거래대금': f"{t_money:,.0f}억",
                    '거래량 증가율': f"{t_vol/p_vol:.1f}배",
                    '종가': f"{t_close:,.0f}원"
                })
    
    if predictions:
        st.dataframe(pd.DataFrame(predictions), use_container_width=True)
    else:
        st.write("오늘 조건에 맞는 예측 종목이 아직 없습니다.")

else:
    st.error("데이터를 불러올 수 없습니다.")
