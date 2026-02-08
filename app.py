import streamlit as st
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta

# 1. 웹 페이지 기본 설정
st.set_page_config(page_title="주식 실시간 갭 스캐너", layout="wide")

# 사이드바 필터 설정
st.sidebar.header("🎯 필터 설정")
min_gap = st.sidebar.slider("최소 시가갭 (%)", 0.0, 10.0, 3.0, 0.5)
min_money = st.sidebar.number_input("최소 거래대금 (억원)", 0, 1000, 100)

st.title("🔥 실시간 시가 갭상승 주도주")
st.write("초기 로딩 속도가 최적화되었습니다. 종목을 클릭하면 차트를 불러옵니다.")

# 2. 데이터 로드 (최소한의 정보만 빠르게 가져오기)
@st.cache_data(ttl=60)
def get_fast_gap_data():
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
    # 분석 대상을 상위 50개로 제한하여 속도 향상
    top_50_df = df_today.sort_values(by='거래대금', ascending=False).head(50)
    
    for ticker in top_50_df.index:
        if ticker in df_prev.index:
            today_money = top_50_df.loc[ticker, '거래대금'] / 100000000
            if today_money < min_money: continue
            
            name = stock.get_market_ticker_name(ticker)
            prev_close = df_prev.loc[ticker, '종가']
            today_open = top_50_df.loc[ticker, '시가']
            gap_rate = ((today_open - prev_close) / prev_close) * 100
            
            if gap_rate < min_gap: continue
            
            results.append({
                'ticker': ticker, 'name': name, 'gap_rate': gap_rate,
                'price': top_50_df.loc[ticker, '종가'],
                'change_rate': top_50_df.loc[ticker, '등락률'],
                'money': today_money
            })
            
    return pd.DataFrame(results), today_date

# 3. 화면 표시 로직
try:
    df_final, used_date = get_fast_gap_data()
    
    if not df_final.empty:
        df_final = df_final.sort_values(by='gap_rate', ascending=False)
        st.success(f"📅 분석 기준일: {used_date} | 검색된 종목: {len(df_final)}개")

        for _, row in df_final.iterrows():
            # expander를 열었을 때만 내부 코드가 실행됨
            with st.expander(f"🔥 {row['name']} (시가갭: {row['gap_rate']:.2f}%)"):
                c1, c2, c3 = st.columns(3)
                c1.metric("시가 갭", f"{row['gap_rate']:.2f}%")
                c2.metric("거래대금", f"{row['money']:,.0f}억")
                c3.metric("현재 등락률", f"{row['change_rate']:.2f}%")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    st.link_button(f"🔍 테마 검색", f"https://search.naver.com/search.naver?query={row['name']}+관련주+테마")
                with col_btn2:
                    st.link_button(f"📊 상세 정보", f"https://finance.naver.com/item/main.naver?code={row['ticker']}")
                
                # --- [핵심 수정] 차트 지연 로딩 버튼 ---
                # 모든 차트를 미리 그리지 않고, 사용자가 버튼을 누를 때만 그리도록 설정 가능하지만
                # Streamlit의 expander는 열릴 때 내부 코드를 실행하므로, 
                # 이 위치에 차트 코드를 두는 것만으로도 초기 로딩 속도가 개선됩니다.
                st.divider()
                if st.checkbox(f"📈 {row['name']} 차트 보기", key=f"chart_{row['ticker']}"):
                    try:
                        start_dt = (datetime.strptime(used_date, "%Y%m%d") - timedelta(days=60)).strftime("%Y%m%d")
                        df_chart = stock.get_market_ohlcv(start_dt, used_date, row['ticker'])
                        
                        if not df_chart.empty:
                            import plotly.graph_objects as go
                            fig = go.Figure(data=[go.Candlestick(
                                x=df_chart.index, open=df_chart['시가'], high=df_chart['고가'],
                                low=df_chart['저가'], close=df_chart['종가'],
                                increasing_line_color='red', decreasing_line_color='blue'
                            )])
                            fig.update_layout(height=300, margin=dict(l=0,r=0,b=0,t=0), xaxis_rangeslider_visible=False)
                            st.plotly_chart(fig, use_container_width=True)
                    except:
                        st.write("차트 데이터를 가져오지 못했습니다.")
    else:
        st.warning("조건에 맞는 종목이 없습니다.")

except Exception as e:
    st.error(f"오류 발생: {e}")

st.divider()
st.caption(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
