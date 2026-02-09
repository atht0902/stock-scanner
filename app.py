import streamlit as st
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="최속 종목 스캐너", layout="wide")
st.title("🔍 실시간 거래 상위 50 스캐너")

@st.cache_data(ttl=300) # 캐시를 5분으로 단축
def get_slim_data():
    # 가장 최근 영업일 딱 하루치만 집중 공략
    target_dt = datetime.now().strftime("%Y%m%d")
    for i in range(10): # 최근 10일 중 가장 가까운 평일 찾기
        dt = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        try:
            df = stock.get_market_ohlcv_by_ticker(dt, market="ALL")
            if not df.empty and df['거래대금'].sum() > 0:
                # 성공하면 기본 정보와 함께 반환
                return dt, df
        except: continue
    return None, None

dt, df_ohlcv = get_slim_data()

if df_ohlcv is not None:
    st.success(f"📅 데이터 확인 완료: {dt}")
    
    # 1. 거래대금 상위 50개 선정
    top_50 = df_ohlcv.sort_values(by='거래대금', ascending=False).head(50).copy()
    
    # 2. 부가 데이터 (수급/펀더멘털) 한 번에 가져오기 (루프 방지)
    try:
        df_fund = stock.get_market_fundamental_by_ticker(dt, market="ALL")
        df_inv = stock.get_market_net_purchases_of_equities_by_ticker(dt, dt, "ALL")
    except:
        df_fund = pd.DataFrame()
        df_inv = pd.DataFrame()

    results = []
    for ticker in top_50.index:
        name = stock.get_market_ticker_name(ticker)
        ohlcv = top_50.loc[ticker]
        
        # 링크 생성
        chart_url = f"https://finance.naver.com/item/main.naver?code={ticker}"
        name_link = f'<a href="{chart_url}" target="_blank" style="text-decoration:none; color:#007bff; font-weight:bold;">{name}</a>'
        
        # 데이터 매칭 (없으면 0)
        per = df_fund.loc[ticker, 'PER'] if ticker in df_fund.index else 0
        pbr = df_fund.loc[ticker, 'PBR'] if ticker in df_fund.index else 0
        f_buy = df_inv.loc[ticker, '외국인'] / 100000000 if ticker in df_inv.index else 0
        i_buy = df_inv.loc[ticker, '기관'] / 100000000 if ticker in df_inv.index else 0

        results.append({
            "종목명(차트링크)": name_link,
            "현재가": f"{ohlcv['종가']:,.0f}",
            "등락률": f"{ohlcv['등락률']:.2f}%",
            "거래대금(억)": int(ohlcv['거래대금']/100000000),
            "외인(억)": round(f_buy, 1),
            "기관(억)": round(i_buy, 1),
            "PER": round(per, 1),
            "PBR": round(pbr, 2)
        })

    # 테이블 출력
    st.write("### 🔥 오늘 거래대금 TOP 50")
    st.write("종목명을 클릭하면 네이버 증권 차트로 연결됩니다.")
    final_df = pd.DataFrame(results)
    st.write(final_df.to_html(escape=False, index=False), unsafe_allow_html=True)

else:
    st.error("데이터 서버 응답이 지연되고 있습니다. 잠시 후 다시 새로고침 해주세요.")
