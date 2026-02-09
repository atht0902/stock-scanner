import streamlit as st
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="주식 퀀트 분석기 v2", layout="wide")
st.title("🚀 퀀트 분석 & 차트 바로가기")

@st.cache_data(ttl=600)
def get_final_data_with_link():
    found_dates = []
    for i in range(40):
        target_dt = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        try:
            df_ohlcv = stock.get_market_ohlcv_by_ticker(target_dt, market="ALL")
            if df_ohlcv is not None and not df_ohlcv.empty and df_ohlcv['거래대금'].sum() > 0:
                df_inv = stock.get_market_net_purchases_of_equities_by_ticker(target_dt, target_dt, "ALL")
                df_fund = stock.get_market_fundamental_by_ticker(target_dt, market="ALL")
                found_dates.append({'date': target_dt, 'ohlcv': df_ohlcv, 'investor': df_inv, 'fund': df_fund})
        except: continue
        if len(found_dates) == 4: break
    return found_dates

with st.spinner('차트 데이터를 연결 중입니다...'):
    data_bundle = get_final_data_with_link()

if data_bundle and len(data_bundle) >= 3:
    st.success(f"✅ 분석 완료 (기준: {data_bundle[0]['date']})")

    def analyze_with_chart(target_idx, compare_idx, mode="prediction"):
        curr = data_bundle[target_idx]
        prev = data_bundle[compare_idx]
        results = []

        for ticker in curr['ohlcv'].index:
            try:
                if ticker not in prev['ohlcv'].index: continue
                t_ohlcv = curr['ohlcv'].loc[ticker]
                p_ohlcv = prev['ohlcv'].loc[ticker]
                
                # --- 필터 최저 수준으로 완화 (종목 무조건 보기) ---
                t_money = t_ohlcv['거래대금'] / 100000000
                if t_money < 10: continue # 10억 이상이면 다 나옴
                
                if mode in ["prediction", "backtest"]:
                    # 거래량 증가 + 고가 대비 15% 이내 마감
                    if not (t_ohlcv['거래량'] > p_ohlcv['거래량'] * 1.0 and t_ohlcv['종가'] > t_ohlcv['고가'] * 0.85):
                        continue

                # 데이터 추출
                name = stock.get_market_ticker_name(ticker)
                per = curr['fund'].loc[ticker, 'PER'] if ticker in curr['fund'].index else 0
                pbr = curr['fund'].loc[ticker, 'PBR'] if ticker in curr['fund'].index else 0
                
                # --- 네이버 증권 차트 링크 생성 ---
                chart_url = f"https://finance.naver.com/item/main.naver?code={ticker}"
                # 마크다운 형식으로 링크 생성
                name_link = f"[{name}]({chart_url})"

                res = {
                    '종목명(차트링크)': name_link,
                    'PER': round(float(per), 1),
                    'PBR': round(float(pbr), 2),
                    '외인(억)': round(float(curr['investor'].loc[ticker, '외국인']/100000000), 1) if ticker in curr['investor'].index else 0,
                    '기관(억)': round(float(curr['investor'].loc[ticker, '기관']/100000000), 1) if ticker in curr['investor'].index else 0,
                    '거래대금(억)': int(t_money),
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

    # 출력
    with st.expander("📊 과거 종목 수익 확인 (클릭 시 차트 이동)"):
        bt_df = analyze_with_chart(1, 2, mode="backtest")
        if not bt_df.empty:
            st.write("종목명을 누르면 네이버 증권으로 이동합니다.")
            st.write(bt_df.to_markdown(index=False), unsafe_allow_html=True)

    st.subheader("🔮 내일 갭상승 후보 & 가치 지표")
    pred_df = analyze_with_chart(0, 1, mode="prediction")
    if not pred_df.empty:
        st.write("종목명을 누르면 네이버 증권으로 이동합니다.")
        # 데이터프레임을 마크다운으로 렌더링하여 링크가 작동하게 함
        st.write(pred_df.to_markdown(index=False), unsafe_allow_html=True)
    else:
        st.warning("조건에 맞는 종목이 없습니다. 잠시 후 새로고침 해주세요.")

else:
    st.error("데이터 로드 중입니다.")
