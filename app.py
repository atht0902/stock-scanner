import streamlit as st
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta

# 1. 웹 페이지 기본 설정
st.set_page_config(page_title="주식 종목 선별기", layout="wide")
st.title("📈 오늘의 종목 선별 리스트")
st.write("시장 거래대금 상위 50위 종목 중 선별된 리스트입니다.")

# 2. 날짜 설정 (데이터가 있는 가장 최근 영업일 찾기)
@st.cache_data
def get_stock_data():
    for i in range(10):
        target_date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        df = stock.get_market_ohlcv_by_ticker(target_date, market="ALL")
        if not df.empty and df['거래대금'].sum() > 0:
            return df, target_date
    return pd.DataFrame(), "데이터 없음"

try:
    df, used_date = get_stock_data()
    
    if not df.empty:
        st.info(f"📅 분석 기준일: {used_date} (거래대금 상위 50위 기준)")
        
        # 거래대금 상위 50위 추출
        top_50 = df.sort_values(by='거래대금', ascending=False).head(50)
        
        for ticker in top_50.index:
            name = stock.get_market_ticker_name(ticker)
            price = top_50.loc[ticker, '종가']
            change_rate = top_50.loc[ticker, '등락률']
            volume_money = top_50.loc[ticker, '거래대금'] / 100000000  # 억원 단위
            
            with st.expander(f"📌 {name} ({ticker})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**[데이터 정보]**")
                    st.write(f"* 💰 거래대금: {volume_money:,.1f} 억원")
                    st.write(f"* 📊 등락률: {change_rate:.2f}%")
                    st.write(f"* 📉 종가: {price:,.0f}원")
                
                with col2:
                    st.write("**[선별 근거]**")
                    st.write("✅ 거래대금 상위 50위 이내 (시장 관심도 높음)")
                    st.write("✅ 익일 시가 상승갭 패턴 분석 대상")
                    st.write("✅ 관련 이슈 및 뉴스 확인 필요")
                
                # 네이버 금융 링크
                naver_url = f"https://finance.naver.com/item/main.naver?code={ticker}"
                st.link_button(f"🔗 {name} 상세 정보/뉴스 보기", naver_url)
                
                # --- 차트 코드 추가 ---
                st.divider()
                st.write(f"📊 **{name} 최근 주가 흐름**")
                try:
                    base_dt = datetime.strptime(str(used_date), "%Y%m%d")
                    start_dt = (base_dt - timedelta(days=90)).strftime("%Y%m%d")
                    df_chart = stock.get_market_ohlcv_by_ticker(start_dt, used_date, ticker)
                    
                    if not df_chart.empty:
                        import plotly.graph_objects as go
                        fig = go.Figure(data=[go.Candlestick(
                            x=df_chart.index,
                            open=df_chart['시가'], high=df_chart['고가'],
                            low=df_chart['저가'], close=df_chart['종가'],
                            increasing_line_color='red', decreasing_line_color='blue'
                        )])
                        fig.update_layout(height=400, margin=dict(l=10, r=10, b=10, t=10), xaxis_rangeslider_visible=False)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("차트 데이터를 불러올 수 없습니다.")
                except Exception as e:
                    st.error(f"차트 생성 중 오류: {e}")

    else:
        st.error("데이터를 불러올 수 없습니다. 장 시작 전이거나 휴장일일 수 있습니다.")

except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")
