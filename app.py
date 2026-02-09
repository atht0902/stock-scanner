import streamlit as st
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="주식 퀀트 분석기", layout="wide")
st.title("🚀 갭상승 예측 & 백테스트 시스템")

@st.cache_data(ttl=600)
def get_final_engine_data():
    found_dates = []
    for i in range(40): # 스캔 범위를 좀 더 확대
        target_dt = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        try:
            df_ohlcv = stock.get_market_ohlcv_by_ticker(target_dt, market="ALL")
            if df_ohlcv is not None and not df_ohlcv.empty and df_ohlcv['거래대금'].sum() > 0:
                df_inv = stock.get_market_net_purchases_of_equities_by_ticker(target_dt, target_dt, "ALL")
                df_fund = stock.get_market_fundamental_by_ticker(target_dt, market="ALL")
                
                found_dates.append({
                    'date': target_dt, 'ohlcv': df_ohlcv, 
                    'investor': df_inv, 'fund': df_fund
                })
        except: continue
        if len(found_dates) == 4: break
    return found_dates

with st.spinner('데이터를 정밀 분석 중입니다...'):
    data_bundle = get_final_engine_data()

if data_bundle and len(data_bundle) >= 3:
    st.success(f"✅ 분석 완료 (최근 영업일: {data_bundle[0]['date']})")

    def analyze_robust(target_idx, compare_idx, mode="prediction"):
        curr = data_bundle[target_idx]
        prev = data_bundle[compare_idx]
        results = []

        for ticker in curr['ohlcv'].index:
            try:
                if ticker not in prev['ohlcv'].index: continue
                
                t_ohlcv = curr['ohlcv'].loc[ticker]
                p_ohlcv = prev['ohlcv'].loc[ticker]
                
                # --- 필터 대폭 완화 (종목 검출 우선) ---
                t_money = t_ohlcv['거래대금'] / 100000000
                if t_money < 50: continue  # 50억 이상이면 일단 통과
                
                if mode in ["prediction", "backtest"]:
                    # 거래량 1.1배 이상 & 종가가 당일 고가 근처(10% 이내)면 통과
                    if not (t_ohlcv['거래량'] > p_ohlcv['거래량'] * 1.1 and t_ohlcv['종가'] > t_ohlcv['고가'] * 0.90):
                        continue

                # 데이터 안전 추출
                per = curr['fund'].loc[ticker, 'PER'] if ticker in curr['fund'].index else 0
                pbr = curr['fund'].loc[ticker, 'PBR'] if ticker in curr['fund'].index else 0
                
                f_buy, i_buy = 0, 0
                if ticker in curr['investor'].index:
                    f_buy = curr['investor'].loc[ticker, '외국인'] / 100000000
                    i_buy = curr['investor'].loc[ticker, '기관'] / 100000000

                res = {
                    '종목명': stock.get_market_ticker_name(ticker),
                    'PER': round(float(per), 1),
                    'PBR': round(float(pbr), 2),
                    '외인(억)': round(float(f_buy), 1),
                    '기관(억)': round(float(i_buy), 1),
                    '거래대금(억)': int(t_money),
                    '등락률': f"{t_ohlcv['등락률']:.1f}%",
                    '종가': f"{t_ohlcv['종가']:,.0f}"
                }

                if mode == "backtest":
                    next_day = data_bundle[target_idx-1]['ohlcv']
                    if ticker in next_day.index:
                        n_data = next_day.loc[ticker]
                        res['실제시가갭'] = f"{((n_data['시가']-t_ohlcv['종가'])/t_ohlcv['종가'])*100:+.2f}%"
                        res['당일고가'] = f"{((n_data['고가']-t_ohlcv['종가'])/t_ohlcv['종가'])*100:+.2f}%"
                
                results.append(res)
            except: continue
        return pd.DataFrame(results)

    # 1. 백테스트
    with st.expander("📊 과거 종목 수익 확인"):
        bt_df = analyze_robust(1, 2, mode="backtest")
        st.dataframe(bt_df, use_container_width=True)

    # 2. 내일 예측
    st.subheader("🔮 내일 갭상승 후보 리스트")
    pred_df = analyze_robust(0, 1, mode="prediction")
    if not pred_df.empty:
        # 수급 좋은 순서로 정렬
        pred_df['수급'] = pred_df['외인(억)'] + pred_df['기관(억)']
        st.dataframe(pred_df.sort_values(by='수급', ascending=False).drop(columns=['수급']), use_container_width=True)
    else:
        st.warning("현재 시장에 필터를 통과한 종목이 없습니다. 잠시 후 다시 시도해주세요.")

else:
    st.error("영업일 데이터를 찾을 수 없습니다.")
