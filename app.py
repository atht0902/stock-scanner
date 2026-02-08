import streamlit as st
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta

# 1. 웹 페이지 기본 설정
st.set_page_config(page_title="주식 종목 선별기", layout="wide")
st.title("📈 오늘의 종목 선별 리스트")
st.write("시장 거래대금 상위 50위 종목 중 선별된 리스트입니다.")

# 2. 날짜 설정 (최근 영업일 찾기)
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
        st.info(f"📅 분석 기준일: {used_date}")
        
        # 거래대금 상위 50위
        top_50 = df.sort_values(by='거래대금', ascending=False).head(50)
        
        for ticker in top_50.index:
            name = stock.get_market_ticker_name(ticker)
            price = top_50.loc[ticker, '종가']
            open_price = top_50.loc[ticker, '시가']
            change_rate = top_50.loc[ticker, '등락률']
            volume_money = top_50.loc[ticker, '거래대금'] / 100000000 
            
            # --- 갭 상승 강조 로직 (임시: 시가가 종가보다 높게 시작하면 강조) ---
            is_gap = open_price > (price / (1 + change_rate/100))
            label = f"🔥 {name}" if is_gap else f"📌 {name}"

            with st.expander(f"{label} ({ticker})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**[데이터 정보]**")
                    st.write(f"* 💰 거래대금: {volume_money:,.1f} 억원")
                    st.write(f"* 📊 등락률: {change_rate:.2f}%")
                
                with col2:
                    st.write("**[분석 요약]**")
                    st.write("✅ 거래대금 상위 50위 (수급 집중)")
                    if is_gap: st.write("✅ **시가 갭 발생 확인**")
                
                st.link_button(f"🔗 {name} 상세 정보 보기", f"https://finance.naver.com/item/main.naver?code={ticker}")
                
                # --- 차트 (날짜 처리를 더 강력하게 수정) ---
                st.divider()
                try:
                    # 차트용 날짜를 별도로 계산
                    end_dt = datetime.strptime(used_date, "%Y%m%d")
                    start_dt = (end_dt - timedelta(days=60)).strftime("%Y%m%d")
                    
                    # 'ALL'을 빼고 ticker만 전달 (핵심 수정)
                    df_chart = stock.get_market_ohlcv(start_dt, used_date, ticker)
                    
                    if not df_chart.empty:
                        import plotly.graph_objects as go
                        fig = go.Figure(data=[go.Candlestick(
                            x=df_chart.index,
                            open=df_chart['시가'], high=df_chart['고가'],
                            low=df_chart['저가'], close=df_chart['종가'],
                            increasing_line_color='red', decreasing_line_color='blue'
                        )])
                        fig.update_layout(height=350, margin=dict(l=0, r=0, b=0, t=0), xaxis_rangeslider_visible=False)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.write("⚠️ 차트 데이터를 생성할 수 없습니다.")
                except:
                    st.write("⚠️ 차트 로딩 실패")

    else:
        st.error("데이터를 가져올 수 없습니다.")
except Exception as e:
    st.error(f"오류 발생: {e}")
