import streamlit as st
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta

# 1. 설정 및 기본 데이터 로드
st.set_page_config(page_title="주식 예측 및 패턴 분석기", layout="wide")
st.title("🎯 시가 갭 상승 예측 & 패턴 분석기")

@st.cache_data(ttl=600)
def get_prediction_data_super_safe():
    dates = []
    # 넉넉하게 최근 30일치를 뒤져서 실제 장이 열렸던 날 3일을 찾음
    for i in range(30):
        target_date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        try:
            df = stock.get_market_ohlcv_by_ticker(target_date, market="ALL")
            # 데이터가 있고 거래대금 합계가 0보다 큰 '진짜 영업일'만 수집
            if not df.empty and df['거래대금'].sum() > 0:
                dates.append((target_date, df))
        except:
            continue
        if len(dates) == 3: break # 딱 3일치만 찾으면 종료
    
    return dates

data_bundle = get_prediction_data_super_safe()

if data_bundle and len(data_bundle) >= 3:
    # d[0]: 최근일, d[1]: 전일, d[2]: 전전일
    today_info, prev_info, pprev_info = data_bundle
    
    st.success(f"✅ 분석 완료 (기준일: {today_info[0]} / 비교일: {prev_info[0]}, {pprev_info[0]})")

    # --- 섹션 1: 과거 복기 ---
    with st.expander("📝 과거 갭 상승 종목 복기 (패턴 분석)"):
        success_cases = []
        top_prev = prev_info[1].sort_values(by='거래대금', ascending=False).head(50)
        for ticker in top_prev.index:
            if ticker in pprev_info[1].index:
                p_close = pprev_info[1].loc[ticker, '종가']
                t_open = prev_info[1].loc[ticker, '시가']
                if p_close > 0:
                    gap = ((t_open - p_close) / p_close) * 100
                    if gap >= 3.0:
                        vol_increase = pprev_info[1].loc[ticker, '거래량'] / 1000000
                        success_cases.append({
                            '종목명': stock.get_market_ticker_name(ticker), 
                            '날짜': prev_info[0],
                            '시가갭': f"{gap:.2f}%", 
                            '전날거래량(M)': f"{vol_increase:.1f}"
                        })
        if success_cases: st.table(pd.DataFrame(success_cases))
        else: st.write("해당 기간 갭 상승 종목이 없습니다.")

    # --- 섹션 2: 내일 예측 ---
    st.header("🔮 내일 시가 갭상승 후보 종목")
    st.info(f"오늘({today_info[0]}) 데이터를 기반으로 내일의 흐름을 예측합니다.")
    
    predictions = []
    today_df = today_info[1]
    prev_df = prev_info[1]
    
    for ticker in today_df.index:
        if ticker in prev_df.index:
            t_money = today_df.loc[ticker, '거래대금'] / 100000000
            if t_money < 300: continue # 거래대금 기준을 300억으로 살짝 낮춰 더 많은 후보 탐색
            
            t_vol = today_df.loc[ticker, '거래량']
            p_vol = prev_df.loc[ticker, '거래량']
            t_close = today_df.loc[ticker, '종가']
            t_high = today_df.loc[ticker, '고가']
            
            # 패턴: 거래량 1.5배 이상 증가 & 고가 부근 마감
            if p_vol > 0 and t_vol > p_vol * 1.5 and t_high > 0 and t_close > (t_high * 0.97):
                predictions.append({
                    '종목명': stock.get_market_ticker_name(ticker),
                    '거래대금(억)': f"{t_money:,.0f}",
                    '거래량증가': f"{t_vol/p_vol:.1f}배",
                    '현재가': f"{t_close:,.0f}"
                })
    
    if predictions:
        st.dataframe(pd.DataFrame(predictions), use_container_width=True)
    else:
        st.warning("조건을 충족하는 예측 종목이 없습니다. 장 마감 직전에 다시 확인해 보세요!")

else:
    st.error("데이터를 충분히 찾지 못했습니다. 인터넷 연결이나 날짜를 확인해 주세요.")
