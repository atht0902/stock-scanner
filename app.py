import streamlit as st
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="주식 퀀트 시스템", layout="wide")
st.title("🚀 갭상승 예측 & 백테스트 시스템")

@st.cache_data(ttl=600)
def get_all_in_one_data():
    found_dates = []
    for i in range(30):
        target_dt = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        try:
            df_ohlcv = stock.get_market_ohlcv_by_ticker(target_dt, market="ALL")
            if df_ohlcv is not None and not df_ohlcv.empty and df_ohlcv['거래대금'].sum() > 0:
                # 수급, 시총, 펀더멘털(PER/PBR) 한꺼번에 로드
                df_investor = stock.get_market_net_purchases_of_equities_by_ticker(target_dt, target_dt, "ALL")
                df_cap = stock.get_market_cap_by_ticker(target_dt, market="ALL")
                df_fund = stock.get_market_fundamental_by_ticker(target_dt, market="ALL")
                
                found_dates.append({
                    'date': target_dt, 'ohlcv': df_ohlcv, 
                    'investor': df_investor, 'cap': df_cap, 'fund': df_fund
                })
        except: continue
        if len(found_dates) == 4: break # 백테스트를 위해 4일치 데이터 확보
    return found_dates

with st.spinner('데이터 엔진 가동 중...'):
    data_list = get_all_in_one_data()

if data_list and len(data_list) >= 3:
    # d[0]:오늘, d[1]:어제, d[2]:그제
    st.info(f"📅 데이터 기준: {data_list[0]['date']} | 백테스트 대상: {data_list[1]['date']}")

    def process_data(target_idx, compare_idx, mode="prediction"):
        curr = data_list[target_idx]
        prev = data_list[compare_idx]
        results = []

        for ticker in curr['ohlcv'].index:
            if ticker in prev['ohlcv'].index:
                t_ohlcv = curr['ohlcv'].loc[ticker]
                p_ohlcv = prev['ohlcv'].loc[ticker]
                
                # 예측 필터 (어제 종가 대비 오늘 시가 갭을 노리는 자리)
                if mode == "prediction" or mode == "backtest":
                    vol_up = t_ohlcv['거래량'] > p_ohlcv['거래량'] * 1.5
                    close_high = t_ohlcv['종가'] > (t_ohlcv['고가'] * 0.97)
                    if not (vol_up and close_high and t_ohlcv['거래대금'] > 30000000000): continue

                # 저평가 지표 (PER, PBR)
                per = curr['fund'].loc[ticker, 'PER'] if ticker in curr['fund'].index else 0
                pbr = curr['fund'].loc[ticker, 'PBR'] if ticker in curr['fund'].index else 0
                
                # 수급
                inv = curr['investor'].loc[ticker] if ticker in curr['investor'].index else None
                foreigner = inv['외국인'] / 100000000 if inv is not None else 0
                institution = inv['기관'] / 100000000 if inv is not None else 0

                res = {
                    '종목명': stock.get_market_ticker_name(ticker),
                    'PER': round(per, 1),
                    'PBR': round(pbr, 2),
                    '외인(억)': round(foreigner, 1),
                    '기관(억)': round(institution, 1),
                    '거래량증가': f"{t_ohlcv['거래량']/p_ohlcv['거래량']:.1f}배",
                    '종가': f"{t_ohlcv['종가']:,.0f}"
                }

                # 백테스트 모드일 때: 다음 날(오늘)의 시가/고가 수익률 계산
                if mode == "backtest":
                    next_day = data_list[target_idx-1]['ohlcv'].loc[ticker]
                    gap_profit = ((next_day['시가'] - t_ohlcv['종가']) / t_ohlcv['종가']) * 100
                    high_profit = ((next_day['고가'] - t_ohlcv['종가']) / t_ohlcv['종가']) * 100
                    res['실제시가갭'] = f"{gap_profit:+.2f}%"
                    res['당일최고가'] = f"{high_profit:+.2f}%"
                
                results.append(res)
        return pd.DataFrame(results)

    # --- 섹션 1: 백테스트 (어제의 예측이 오늘 어땠나?) ---
    with st.expander("📊 어제 종목들의 오늘 성적표 (백테스트)"):
        st.write(f"설명: {data_list[1]['date']}에 포착된 종목의 다음 날({data_list[0]['date']}) 수익률")
        bt_df = process_data(1, 2, mode="backtest")
        if not bt_df.empty:
            st.dataframe(bt_df, use_container_width=True)
        else: st.write("어제 조건에 부합한 종목이 없습니다.")

    # --- 섹션 2: 내일 예측 + 저평가 지표 ---
    st.subheader("🔮 내일 시가 갭상승 후보 & 밸류에이션")
    pred_df = process_data(0, 1, mode="prediction")
    if not pred_df.empty:
        pred_df['수급합'] = pred_df['외인(억)'] + pred_df['기관(억)']
        st.dataframe(pred_df.sort_values(by='수급합', ascending=False), use_container_width=True)
    else: st.warning("조건에 맞는 종목이 없습니다.")

else:
    st.error("데이터 로딩 중... [Clear cache]를 눌러보세요.")
