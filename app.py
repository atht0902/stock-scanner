import streamlit as st
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta

# 1. 설정 및 기본 데이터 로드
st.set_page_config(page_title="주식 예측 및 패턴 분석기", layout="wide")
st.title("🎯 시가 갭 상승 예측 & 패턴 분석기")

@st.cache_data(ttl=600)
def get_prediction_data_ultimate():
    dates = []
    # 넉넉하게 최근 30일치를 거꾸로 뒤집니다.
    for i in range(30):
        target_date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        try:
            # 해당 날짜에 데이터가 존재하는지 확인
            df = stock.get_market_ohlcv_by_ticker(target_date, market="ALL")
            # 거래대금이 있고 데이터가 비어있지 않은 '진짜 영업일'만 수집
            if not df.empty and df['거래대금'].sum() > 0:
                dates.append((target_date, df))
        except:
            continue
        
        # 실제 영업일 3일치를 찾으면 즉시 중단하고 리스트 반환
        if len(dates) == 3:
            break
    
    return dates

# 데이터 가져오기 실행
with st.spinner('영업일 데이터를 역추적 중입니다...'):
    data_bundle = get_prediction_data_ultimate()

if data_bundle and len(data_bundle) >= 3:
    # d[0]: 가장 최근 영업일(오늘), d[1]: 전 영업일, d[2]: 전전 영업일
    today_info, prev_info, pprev_info = data_bundle
    
    st.success(f"✅ 분석 데이터 로드 완료")
    st.info(f"📅 분석 기준: {today_info[0]} | 비교 대상: {prev_info[0]}, {pprev_info[0]}")

    # --- 섹션 1: 과거 복기 (비교일과 그 전날 데이터 사용) ---
    with st.expander("📝 과거 갭 상승 종목 복기 (패턴 분석)"):
        success_cases = []
        # 기준일(비교 대상의 전날) 데이터가 있는지 확인
        top_prev = prev_info[1].sort_values(by='거래대금', ascending=False).head(50)
        for ticker in top_prev.index:
            if ticker in pprev_info[1].index:
                p_close = pprev_info[1].loc[ticker, '종가']
                t_open = prev_info[1].loc[ticker, '시가']
                if p_close > 0:
                    gap = ((t_open - p_close) / p_close) * 100
                    if gap >= 3.0:
                        vol_prev = pprev_info[1].loc[ticker, '거래량'] / 1000000
                        success_cases.append({
                            '종목명': stock.get_market_ticker_name(ticker), 
                            '날짜': prev_info[0],
                            '시가갭': f"{gap:.2f}%", 
                            '전일거래량(M)': f"{vol_prev:.1f}"
                        })
        if success_cases:
            st.table(pd.DataFrame(success_cases))
        else:
            st.write("해당 기간 갭 상승 종목이 없습니다.")

    # --- 섹션 2: 내일 예측 (오늘 데이터 기반) ---
    st.header("🔮 내일 시가 갭상승 후보 종목")
    st.caption(f"{today_info[0]} 장마감 기준 데이터 분석 결과")
    
    predictions = []
    today_df = today_info[1]
    prev_df = prev_info[1]
    
    for ticker in today_df.index:
        if ticker in prev_df.index:
            t_money = today_df.loc[ticker, '거래대금'] / 100000000 # 억 단위
            # 필터: 거래대금 300억 이상 (조건 완화)
            if t_money < 300: continue 
            
            t_vol = today_df.loc[ticker, '거래량']
            p_vol = prev_df.loc[ticker, '거래량']
            t_close = today_df.loc[ticker, '종가']
            t_high = today_df.loc[ticker, '고가']
            
            # 예측 로직: 거래량이 전 영업일 대비 1.5배 이상 & 고가권 마감
            if p_vol > 0 and t_vol > p_vol * 1.5 and t_high > 0 and t_close > (t_high * 0.97):
                predictions.append({
                    '종목명': stock.get_market_ticker_name(ticker),
                    '거래대금(억)': f"{t_money:,.0f}",
                    '거래량증가': f"{t_vol/p_vol:.1f}배",
                    '종가': f"{t_close:,.0f}"
                })
    
    if predictions:
        st.dataframe(pd.DataFrame(predictions), use_container_width=True)
    else:
        st.warning("현재 필터 조건을 만족하는 종목이 없습니다.")

else:
    st.error("영업일 데이터를 찾을 수 없습니다. (최근 30일 이내에 장이 열린 날이 3일 미만입니다.)")
