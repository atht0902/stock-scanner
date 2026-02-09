import streamlit as st
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="주식 수급 & 예측 분석기", layout="wide")
st.title("🎯 수급 기반 갭상승 예측기")

@st.cache_data(ttl=600)
def get_ultimate_market_data():
    found_dates = []
    for i in range(30):
        target_dt = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        try:
            df_ohlcv = stock.get_market_ohlcv_by_ticker(target_dt, market="ALL")
            if df_ohlcv is not None and not df_ohlcv.empty and df_ohlcv['거래대금'].sum() > 0:
                # 수급 및 시총 데이터 로드
                df_investor = stock.get_market_net_purchases_of_equities_by_ticker(target_dt, target_dt, "ALL")
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

with st.spinner('데이터를 철저하게 분석 중입니다...'):
    data_list = get_ultimate_market_data()

if data_list and len(data_list) >= 3:
    st.success(f"✅ 데이터 로드 성공 (기준: {data_list[0]['date']})")

    def process_robust_final(target_info, compare_info, mode="prediction"):
        results = []
        df_target = target_info['ohlcv']
        df_prev = compare_info['ohlcv']
        df_investor = target_info['investor']
        df_cap = target_info['cap'].sort_values(by='시가총액', ascending=False)
        df_cap['rank'] = range(1, len(df_cap) + 1)

        for ticker in df_target.index:
            # 기본적으로 이전 영업일 데이터가 있어야 비교 가능
            if ticker in df_prev.index:
                t_money = df_target.loc[ticker, '거래대금'] / 100000000
                if t_money < 300: continue
                
                t_vol = df_target.loc[ticker, '거래량']
                p_vol = df_prev.loc[ticker, '거래량']
                t_close = df_target.loc[ticker, '종가']
                t_high = df_target.loc[ticker, '고가']
                
                # 예측 모드 필터
                if mode == "prediction":
                    if not (p_vol > 0 and t_vol > p_vol * 1.5 and t_close > (t_high * 0.97)):
                        continue
                
                # --- 수급 데이터 추출 (KeyError 절대 방어 로직) ---
                try:
                    # 인덱스 존재 여부를 확인하고 값 추출
                    foreigner = df_investor.loc[ticker, '외국인'] / 100000000 if ticker in df_investor.index else 0
                    institution = df_investor.loc[ticker, '기관'] / 100000000 if ticker in df_investor.index else 0
                except:
                    foreigner, institution = 0, 0
                
                # 시총 순위 추출
                try:
                    cap_rank = df_cap.loc[ticker, 'rank'] if ticker in df_cap.index else 999
                except:
                    cap_rank = 999
                
                results.append({
                    '순위': int(cap_rank),
                    '종목명': stock.get_market_ticker_name(ticker),
                    '외인(억)': round(float(foreigner), 1),
                    '기관(억)': round(float(institution), 1),
                    '거래대금(억)': int(t_money),
                    '거래량증가': f"{t_vol/p_vol:.1f}배",
                    '현재가': f"{t_close:,.0f}"
                })
        return pd.DataFrame(results)

    # 섹션 1: 과거 복기
    with st.expander("📝 전일 갭상승 종목 수급 복기"):
        past_df = process_robust_final(data_list[1], data_list[2], mode="past")
        if not past_df.empty:
            st.dataframe(past_df.sort_values(by='순위'), use_container_width=True)

    # 섹션 2: 내일 예측
    st.subheader("🔮 내일 시가 갭상승 후보 (수급 기준)")
    pred_df = process_robust_final(data_list[0], data_list[1], mode="prediction")
    
    if not pred_df.empty:
        # 합산 수급 계산 후 내림차순 정렬
        pred_df['합산수급'] = pred_df['외인(억)'] + pred_df['기관(억)']
        final_df = pred_df.sort_values(by='합산수급', ascending=False)
        st.dataframe(final_df.drop(columns=['합산수급']), use_container_width=True)
    else:
        st.warning("현재 필터 조건을 만족하는 종목이 없습니다.")

else:
    st.error("데이터 로드에 실패했습니다. 메뉴에서 [Clear cache]를 누르거나 잠시 후 시도해 주세요.")
