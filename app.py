import streamlit as st
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta

# 1. 웹 페이지 기본 설정
st.set_page_config(page_title="주식 갭상승 스캐너", layout="wide")
st.title("🔥 시가 갭상승 종목 스캐너")
st.write("거래대금 상위 50위 종목 중 **시가 갭**이 발생한 주도주를 분석합니다.")

# 2. 데이터 로드 (최근 2일치 데이터를 가져와서 갭 계산)
@st.cache_data
def get_gap_data():
    # 최근 10일 중 영업일 2일 찾기
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
    
    # 거래대금 상위 50위 필터링
    df_today = df_today.sort_values(by='거래대금', ascending=False).head(50)
    
    results = []
    for ticker in df_today.index:
        if ticker in df_prev.index:
            name = stock.get_market_ticker_name(ticker)
            prev_close = df_prev.loc[ticker, '종가']
            today_open = df_today.loc[ticker, '시가']
            today_close = df_today.loc[ticker, '종가']
            today_change = df_today.loc[ticker, '등락률']
            today_money = df_today.loc[ticker, '거래대금'] / 100000000
            
            # 시가 갭 계산: ((오늘시가 - 어제종가) / 어제종가) * 100
            gap_rate = ((today_open - prev_close) / prev_close) * 100
            
            results.append({
                'ticker': ticker, 'name': name, 'gap_rate': gap_rate,
                'price': today_close, 'change_rate': today_change, 'money': today_money
            })
            
    return pd.DataFrame(results), today_date

try:
    df_final, used_date = get_gap_data()
    
    if not df_final.empty:
        # 갭 상승률 순으로 정렬
        df_final = df_final.sort_values(by='gap_rate', ascending=False)
        
        st.success(f"📅 분석 기준일: {used_date} (전일 대비 시가 상승률 순 정렬)")

        for _, row in df_final.iterrows():
            # 갭이 3% 이상이면 불꽃 아이콘, 아니면 핀 아이콘
            icon = "🔥" if row['gap_rate'] >= 3 else "📌"
            gap_color = "red" if row['gap_rate'] > 0 else "blue"
            
            with st.expander(f"{icon} {row['name']} (시가갭: {row['gap_rate']:.2f}%)"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**[수급 및 변동성]**")
                    st.markdown(f"* 시가 갭: <span style='color:{gap_color}; font-weight:bold;'>{row['gap_rate']:.2f}%</span>", unsafe_allow_html=True)
                    st.write(f"* 거래대금: {row['money']:,.1f} 억원")
                with col2:
                    st.write(f"**[가격 정보]**")
                    st.write(f"* 현재 등락률: {row['change_rate']:.2f}%")
                    st.write(f"* 종가: {row['price']:,.0f}원")
                
                st.link_button(f"🔗 {row['name']} 차트/뉴스 더보기", f"https://finance.naver.com/item/main.naver?code={row['ticker']}")
                
                # --- 차트 코드 ---
                try:
                    end_dt = used_date
                    start_dt = (datetime.strptime(used_date, "%Y%m%d") - timedelta(days=60)).strftime("%Y%m%d")
                    df_chart = stock.get_market_ohlcv(start_dt, end_dt, row['ticker'])
                    
                    if not df_chart.empty:
                        import plotly.graph_objects as go
                        fig = go.Figure(data=[go.Candlestick(
                            x=df_chart.index, open=df_chart['시가'], high=df_chart['고가'],
                            low=df_chart['저가'], close=df_chart['종가'],
                            increasing_line_color='red', decreasing_line_color='blue'
                        )])
                        fig.update_layout(height=300, margin=dict(l=0, r=0, b=0, t=0), xaxis_rangeslider_visible=False)
                        st.plotly_chart(fig, use_container_width=True)
                except:
                    st.write("차트를 불러올 수 없습니다.")
    else:
        st.warning("데이터 분석 중입니다. 잠시 후 새로고침 해주세요.")
except Exception as e:
    st.error(f"시스템 오류: {e}")
