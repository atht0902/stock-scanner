import streamlit as st
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta
import time

# 1. 웹 페이지 기본 설정 및 자동 새로고침(60초)
st.set_page_config(page_title="주식 실시간 갭 스캐너", layout="wide")

# 상단 알림 필터 (기능 3)
st.sidebar.header("🎯 필터 설정")
min_gap = st.sidebar.slider("최소 시가갭 (%)", 0.0, 10.0, 3.0, 0.5)
min_money = st.sidebar.number_input("최소 거래대금 (억원)", 0, 1000, 100)

st.title("🔥 실시간 시가 갭상승 주도주")
st.write(f"현재 기준: 거래대금 {min_money}억 이상 & 시가갭 {min_gap}% 이상 종목")

# 2. 데이터 로드 로직
@st.cache_data(ttl=60) # 60초마다 캐시 만료 (기능 1의 기초)
def get_gap_data_final():
    dates = []
    for i in range(15):
        target_date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        df = stock.get_market_ohlcv_by_ticker(target_date, market="ALL")
        if not df.empty and df['거래대금'].sum() > 0:
            dates.append((target_date, df))
        if len(dates) == 2: break
    
    if len(dates) < 2: return pd.DataFrame(), "데이터 부족"
    
    today_date, df_today = dates[0]
    prev_date, df_prev = dates[1]
    
    results = []
    for ticker in df_today.index:
        if ticker in df_prev.index:
            today_money = df_today.loc[ticker, '거래대금'] / 100000000
            if today_money < min_money: continue # 거래대금 필터
            
            name = stock.get_market_ticker_name(ticker)
            prev_close = df_prev.loc[ticker, '종가']
            today_open = df_today.loc[ticker, '시가']
            gap_rate = ((today_open - prev_close) / prev_close) * 100
            
            if gap_rate < min_gap: continue # 갭 필터
            
            results.append({
                'ticker': ticker, 'name': name, 'gap_rate': gap_rate,
                'price': df_today.loc[ticker, '종가'],
                'change_rate': df_today.loc[ticker, '등락률'],
                'money': today_money
            })
            
    return pd.DataFrame(results), today_date

# 3. 화면 표시
try:
    df_final, used_date = get_gap_data_final()
    
    if not df_final.empty:
        df_final = df_final.sort_values(by='gap_rate', ascending=False)
        st.success(f"📅 분석 기준일: {used_date} | 검색된 종목: {len(df_final)}개")

        for _, row in df_final.iterrows():
            with st.expander(f"🔥 {row['name']} (시가갭: {row['gap_rate']:.2f}%)"):
                c1, c2, c3 = st.columns([1, 1, 1])
                with c1:
                    st.metric("시가 갭", f"{row['gap_rate']:.2f}%")
                with c2:
                    st.metric("거래대금", f"{row['money']:,.0f}억")
                with c3:
                    st.metric("현재 등락률", f"{row['change_rate']:.2f}%")
                
                # 기능 2: 테마/섹터 정보 확인 버튼 추가
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    st.link_button(f"🔍 {row['name']} 테마/섹터 검색", f"https://search.naver.com/search.naver?query={row['name']}+관련주+테마")
                with col_btn2:
                    st.link_button(f"📊 네이버금융 상세정보", f"https://finance.naver.com/item/main.naver?code={row['ticker']}")
                
                # 차트 표시
                try:
                    df_chart = stock.get_market_ohlcv((datetime.strptime(used_date, "%Y%m%d") - timedelta(days=60)).strftime("%Y%m%d"), used_date, row['ticker'])
                    if not df_chart.empty:
                        import plotly.graph_objects as go
                        fig = go.Figure(data=[go.Candlestick(x=df_chart.index, open=df_chart['시가'], high=df_chart['고가'], low=df_chart['저가'], close=df_chart['종가'], increasing_line_color='red', decreasing_line_color='blue')])
                        fig.update_layout(height=300, margin=dict(l=0,r=0,b=0,t=0), xaxis_rangeslider_visible=False)
                        st.plotly_chart(fig, use_container_width=True)
                except: st.write("차트 로딩 실패")
    else:
        st.warning("조건에 맞는 종목이 없습니다. 필터를 조절해보세요.")

except Exception as e:
    st.error(f"오류 발생: {e}")

# 기능 1: 화면 하단에 마지막 업데이트 시간 표시 및 자동 새로고침 안내
st.divider()
st.caption(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (60초마다 데이터 갱신)")
