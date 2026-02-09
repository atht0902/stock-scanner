import streamlit as st
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="주식 무조건 검출기", layout="wide")
st.title("🔍 초저인망 종목 스캐너 (차트 연결)")

@st.cache_data(ttl=600)
def get_raw_data():
    found_dates = []
    for i in range(40):
        target_dt = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        try:
            df_ohlcv = stock.get_market_ohlcv_by_ticker(target_dt, market="ALL")
            if df_ohlcv is not None and not df_ohlcv.empty and df_ohlcv['거래대금'].sum() > 0:
                # 데이터가 없어도 에러 안 나게 빈 데이터프레임 처리
                try: df_inv = stock.get_market_net_purchases_of_equities_by_ticker(target_dt, target_dt, "ALL")
                except: df_inv = pd.DataFrame()
                try: df_fund = stock.get_market_fundamental_by_ticker(target_dt, market="ALL")
                except: df_fund = pd.DataFrame()
                
                found_dates.append({'date': target_dt, 'ohlcv': df_ohlcv, 'investor': df_inv, 'fund': df_fund})
        except: continue
        if len(found_dates) == 4: break
    return found_dates

with st.spinner('시장의 모든 물고기를 긁어모으는 중...'):
    data_bundle = get_raw_data()

if data_bundle and len(data_bundle) >= 2:
    st.info(f"📅 분석 기준일: {data_bundle[0]['date']}")

    def scan_all(target_idx, compare_idx):
        curr = data_bundle[target_idx]
        prev = data_bundle[compare_idx]
        results = []

        # 상위 거래대금 100개만 먼저 뽑아서 시도 (속도 향상 및 확실한 검출)
        top_tickers = curr['ohlcv'].sort_values(by='거래대금', ascending=False).head(100).index

        for ticker in top_tickers:
            try:
                t_ohlcv = curr['ohlcv'].loc[ticker]
                p_ohlcv = prev['ohlcv'].loc[ticker] if ticker in prev['ohlcv'].index else t_ohlcv
                
                # --- 초저인망 필터 (이건 안 걸릴 수가 없음) ---
                t_money = t_ohlcv['거래대금'] / 100000000
                if t_money < 1: continue # 거래대금 1억 이상이면 무조건 통과

                # 수급 및 가치지표 안전하게 가져오기 (없으면 0)
                per = curr['fund'].loc[ticker, 'PER'] if ticker in curr['fund'].index else 0
                pbr = curr['fund'].loc[ticker, 'PBR'] if ticker in curr['fund'].index else 0
                f_buy = curr['investor'].loc[ticker, '외국인'] / 100000000 if ticker in curr['investor'].index else 0
                i_buy = curr['investor'].loc[ticker, '기관'] / 100000000 if ticker in curr['investor'].index else 0

                name = stock.get_market_ticker_name(ticker)
                chart_url = f"https://finance.naver.com/item/main.naver?code={ticker}"
                
                results.append({
                    '종목명': f'<a href="{chart_url}" target="_blank">{name}</a>',
                    '등락률': f"{t_ohlcv['등락률']:.1f}%",
                    '거래대금(억)': int(t_money),
                    '외인(억)': round(float(f_buy), 1),
                    '기관(억)': round(float(i_buy), 1),
                    'PER': round(float(per), 1),
                    'PBR': round(float(pbr), 2)
                })
            except: continue
        return pd.DataFrame(results)

    # 결과 출력
    st.subheader("🔥 현재 시장 거래대금 상위 종목 (차트 링크)")
    df_final = scan_all(0, 1)
    if not df_final.empty:
        st.write(df_final.to_html(escape=False, index=False), unsafe_allow_html=True)
    else:
        st.warning("거래소 데이터 응답이 없습니다. 잠시 후 [Clear Cache]를 눌러주세요.")

else:
    st.error("데이터 로드 실패")
