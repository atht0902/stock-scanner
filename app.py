import streamlit as st
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta

# 1. 설정 및 기본 데이터 로드
st.set_page_config(page_title="주식 예측 및 패턴 분석기", layout="wide")
st.title("🎯 시가 갭 상승 예측 & 패턴 분석기")

@st.cache_data(ttl=600)
def get_prediction_data_safe():
    dates = []
    # 최근 20일 중 실제 데이터가 있는 날짜 3일치만 정확히 골라냄
    for i in range(20):
        target_date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        try:
            df = stock.get_market_ohlcv_by_ticker(target_date, market="ALL")
            if not df.empty and df['거래대금'].sum() > 0:
                dates.append((target_date, df))
        except:
            continue
        if len(dates) == 3: break
    
    return dates if len(dates) >= 3 else None

data_bundle = get_prediction_data_safe()

if data_bundle:
    # dates[0]: 가장 최근 영업일(오늘), dates[1]: 전 영업일, dates[2]: 전전 영업일
    today_info, prev_info, pprev_info = data_bundle
    
    with st.expander("📝 과거 갭 상승 종목 복기"):
        success_cases = []
        # 상위 50위 분석
        top_prev = prev_info[1].sort_values(by='거래대금', ascending=False).head(50)
        for ticker in top_prev.index:
            # 안전장치: pprev_info[1]에 해당 티커가 있는지 확인
            if ticker in pprev_info[1].index:
                p_close = pprev_info[1].loc[ticker, '종가']
                t_open = prev_info[1].loc[ticker, '시가']
                if p_close > 0: # 0으로 나누기 방지
                    gap = ((t_open - p_close) / p_close) * 100
                    if gap >= 3.0:
                        vol_increase = pprev_info[1].loc[ticker, '거래량'] / 1000000
                        success_cases.append({'종목명': stock.get_market_ticker_name(ticker), '갭(%)': f"{gap:.2f}%", '전날 거래량(M)': f"{vol_increase:.1f}"})
        
        if success_cases:
            st.table(pd.DataFrame(success_cases))
        else:
            st.write("해당 기간 갭 상승 종목이 없습니다.")

    st.header("🔮 내일 시가 갭상승 후보 종목")
    st.info("조건: 오늘 거래대금 500억↑ + 거래량 전일대비 2배↑ + 고가권 마감")
    
    today_df = today_info[1]
    prev_df = prev_info[1]
    
    predictions = []
    # 데이터가 있는 종목들만 루프
    for ticker in today_df.index:
        if ticker in prev_df.index:
            t_money = today_df.loc[ticker, '거래대금'] / 100000000
            if t_money < 500: continue # 거래대금 미달 시 패스 (속도 향상)
            
            t_vol = today_df.loc[ticker, '거래량']
            p_vol = prev_df.loc[ticker, '거래량']
            t_close = today_df.loc[ticker, '종가']
            t_high = today_df.loc[ticker, '고가']
            
            # 예측 필터 (안전하게 계산)
            if p_vol > 0 and t_vol > p_vol * 2 and t_high > 0 and t_close > (t_high * 0.98):
                predictions.append({
                    '종목명': stock.get_market_ticker_name(ticker),
                    '오늘 거래대금': f"{t_money:,.0f}억",
                    '거래량 증가율': f"{t_vol/p_vol:.1f}배",
                    '현재가': f"{t_close:,.0f}원"
                })
    
    if predictions:
        st.dataframe(pd.DataFrame(predictions), use_container_width=True)
    else:
        st.warning("현재 조건(거래대금 500억 이상 등)을 충족하는 종목이 없습니다.")

else:
    st.error("영업일 데이터를 충분히 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.")
