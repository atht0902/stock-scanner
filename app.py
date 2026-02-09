import streamlit as st
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="주식 퀀트 분석기", layout="wide")
st.title("🚀 갭상승 예측 & 백테스트 시스템")

@st.cache_data(ttl=600)
def get_total_data_engine():
    found_dates = []
    for i in range(30):
        target_dt = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        try:
            df_ohlcv = stock.get_market_ohlcv_by_ticker(target_dt, market="ALL")
            if df_ohlcv is not None and not df_ohlcv.empty and df_ohlcv['거래대금'].sum() > 0:
                df_inv = stock.get_market_net_purchases_of_equities_by_ticker(target_dt, target_dt, "ALL")
                df_cap = stock.get_market_cap_by_ticker(target_dt, market="ALL")
                df_fund = stock.get_market_fundamental_by_ticker(target_dt, market="ALL")
                
                found_dates.append({
                    'date': target_dt, 'ohlcv': df_ohlcv, 
                    'investor': df_inv, 'cap': df_cap, 'fund': df_fund
                })
        except: continue
        if len(found_dates) == 4: break
    return found_dates

with st.spinner('데이터를 불러오고 있습니다...'):
    data_bundle = get_total_data_engine()

if data_bundle and len(data_bundle) >= 3:
    st.success(f"✅ 분석 준비 완료 (오늘: {data_bundle[0]['date']})")

    def analyze_stocks(target_idx, compare_idx, mode="prediction"):
        curr = data_bundle[target_idx]
        prev = data_bundle[compare_idx]
        results = []

        for ticker in curr['ohlcv'].index:
            try:
                if ticker not in prev['ohlcv'].index: continue
                
                t_data = curr['ohlcv'].loc[ticker]
                p_data = prev['ohlcv'].loc[ticker]
                
                # --- [필터 완화 구간] ---
                t_money = t_data['거래대금'] / 100000000
                # 1. 거래대금 기준: 300억 -> 100억으로 완화
                if t_money < 100: continue 
                
                if mode in ["prediction", "backtest"]:
                    # 2. 거래량 증가폭: 1.5배 -> 1.2배로 완화
                    # 3. 마감 강도: 고가 대비 3% 이내 -> 5% 이내로 완화
                    vol_check = t_data['거래량'] > p_data['거래량'] * 1.2
                    price_check = t_data['종가'] > t_data['고가'] * 0.95
                    if not (vol_check and price_check): continue

                # 펀더멘털 & 수급 (기존과 동일)
                per = curr['fund'].loc[ticker, 'PER'] if ticker in curr['fund'].index else 0
                pbr = curr['fund'].loc[ticker, 'PBR'] if ticker in curr['fund'].index else 0
                
                foreigner, institution = 0, 0
                if ticker in curr['investor'].index:
                    foreigner = curr['investor'].loc[ticker, '외국인'] / 100000000
                    institution = curr['investor'].loc[ticker, '기관'] / 100000000

                res = {
                    '종목명': stock.get_market_ticker_name(ticker),
                    'PER': round(float(per), 1),
                    'PBR': round(float(pbr), 2),
                    '외인(억)': round(float(foreigner), 1),
                    '기관(억)': round(float(institution), 1),
                    '거래대금(억)': int(t_money),
                    '거래량증가': f"{t_data['거래량']/p_data['거래량']:.1f}배",
                    '종가': f"{t_data['종가']:,.0f}"
                }

                if mode == "backtest":
                    next_day_ohlcv = data_bundle[target_idx-1]['ohlcv']
                    if ticker in next_day_ohlcv.index:
                        next_data = next_day_ohlcv.loc[ticker]
                        gap = ((next_data['시가'] - t_data['종가']) / t_data['종가']) * 100
                        high = ((next_data['고가'] - t_data['종가']) / t_data['종가']) * 100
                        res['실제시가갭'] = f"{gap:+.2f}%"
                        res['당일최고가'] = f"{high:+.2f}%"
                
                results.append(res)
            except: continue
            
        return pd.DataFrame(results)

    # 섹션 1: 백테스트
    with st.expander("📊 어제 추천 종목의 오늘 성적 (백테스트)"):
        bt_df = analyze_stocks(1, 2, mode="backtest")
        if not bt_df.empty:
            st.dataframe(bt_df, use_container_width=True)
        else: st.info("과거 조건에 맞는 종목이 없습니다.")

    # 섹션 2: 내일의 추천
    st.subheader("🔮 내일 시가 갭상승 후보 (필터 완화됨)")
    pred_df = analyze_stocks(0, 1, mode="prediction")
    if not pred_df.empty:
        pred_df['수급합'] = pred_df['외인(억)'] + pred_df['기관(억)']
        st.dataframe(pred_df.sort_values(by='수급합', ascending=False), use_container_width=True)
    else:
        st.warning("조건을 낮췄음에도 종목이 없습니다. 시장 거래대금이 매우 낮은 날일 수 있습니다.")

else:
    st.error("데이터 로딩 실패.")
