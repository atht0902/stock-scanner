import streamlit as st
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="주식 수급 & 예측 분석기", layout="wide")
st.title("🎯 수급 기반 갭상승 예측기")

# 1. 데이터 로드 함수 (최근 3일 영업일 + 수급 데이터)
@st.cache_data(ttl=600)
def get_advanced_market_data():
    found_dates = []
    for i in range(30):
        target_dt = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        try:
            df_ohlcv = stock.get_market_ohlcv_by_ticker(target_dt, market="ALL")
            if df_ohlcv is not None and not df_ohlcv.empty and df_ohlcv['거래대금'].sum() > 0:
                # 해당 날짜의 수급 데이터 가져오기 (단위: 원)
                df_investor = stock.get_market_net_purchases_of_equities_by_ticker(target_dt, target_dt, "ALL")
                # 해당 날짜의 시가총액/순위 데이터 가져오기
                df_cap = stock.get_market_cap_by_ticker(target_dt, market="ALL")
                
                found_dates.append({
                    'date': target_dt,
                    'ohlcv': df_ohlcv,
                    'investor': df_investor,
                    'cap': df_cap
                })
        except: continue
        if len(found_dates) == 3: break
    return found_dates

with st.spinner('외인/기관 수급 및 시총 데이터를 분석 중입니다...'):
    data_list = get_advanced_market_data()

if data_list and len(data_list) >= 3:
    today = data_list[0]
    prev = data_list[1]
    
    st.success(f"✅ 수급 데이터 매칭 성공 (기준일: {today['date']})")

    # --- 분석 로직 ---
    def process_stock_data(target_info, compare_info, mode="prediction"):
        results = []
        df_target = target_info['ohlcv']
        df_prev = compare_info['ohlcv']
        df_investor = target_info['investor']
        df_cap = target_info['cap'].sort_values(by='시가총액', ascending=False)
        # 시총 순위 부여
        df_cap['rank'] = range(1, len(df_cap) + 1)

        for ticker in df_target.index:
            if ticker in df_prev.index and ticker in df_investor.index:
                t_money = df_target.loc[ticker, '거래대금'] / 100000000
                if t_money < 300: continue # 거래대금 300억 이상만
                
                t_vol = df_target.loc[ticker, '거래량']
                p_vol = df_prev.loc[ticker, '거래량']
                t_close = df_target.loc[ticker, '종가']
                t_high = df_target.loc[ticker, '고가']
                
                # 예측 모드일 때 필터 (거래량 증가 & 고가마감)
                if mode == "prediction":
                    if not (p_vol > 0 and t_vol > p_vol * 1.5 and t_close > (t_high * 0.97)):
                        continue
                
                # 수급 데이터 (단위: 억)
                foreigner = df_investor.loc[ticker, '외국인'] / 100000000
                institution = df_investor.loc[ticker, '기관'] / 100000000
                cap_rank = df_cap.loc[ticker, 'rank']
                
                results.append({
                    '순위': int(cap_rank),
                    '종목명': stock.get_market_ticker_name(ticker),
                    '외인수급(억)': round(foreigner, 1),
                    '기관수급(억)': round(institution, 1),
                    '거래대금(억)': int(t_money),
                    '거래량증가': f"{t_vol/p_vol:.1f}배",
                    '현재가': f"{t_close:,.0f}"
                })
        return pd.DataFrame(results)

    # 섹션 1: 과거 복기
    with st.expander("📝 전일 갭상승 종목 수급 복기"):
        past_df = process_stock_data(data_list[1], data_list[2], mode="past")
        if not past_df.empty:
            st.dataframe(past_df.sort_values(by='순위'), use_container_width=True)

    # 섹션 2: 내일 예측
    st.subheader("🔮 내일 시가 갭상승 후보 (수급 포함)")
    pred_df = process_stock_data(data_list[0], data_list[1], mode="prediction")
    
    if not pred_df.empty:
        # 외인+기관 합산 수급이 좋은 순으로 정렬
        pred_df['합산수급'] = pred_df['외인수급(억)'] + pred_df['기관수급(억)']
        st.dataframe(pred_df.sort_values(by='합산수급', ascending=False), use_container_width=True)
        
        st.caption("💡 팁: 외인과 기관이 동시에 매수(양매수)하면서 거래량이 터진 종목은 신뢰도가 매우 높습니다.")
    else:
        st.warning("조건에 맞는 예측 후보가 없습니다.")

else:
    st.error("데이터 로드 실패. [Clear Cache]를 시도해 주세요.")
