import streamlit as st
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta

# 1. 웹 페이지 기본 설정
st.set_page_config(page_title="주식 3일 추세 & 갭 스캐너", layout="wide")

# 사이드바 필터 설정
st.sidebar.header("🎯 필터 및 분석 설정")
min_gap = st.sidebar.slider("최소 시가갭 (%)", 0.0, 10.0, 3.0, 0.5)
min_money = st.sidebar.number_input("최소 거래대금 (억원)", 0, 1000, 100)

st.title("🚀 시가 갭 & 3일 추세 정밀 분석기")
st.write("상위 50위 종목의 **오늘의 갭**과 **최근 3일간의 에너지**를 분석합니다.")

# 2. 데이터 로드 로직
@st.cache_data(ttl=60)
def get_advanced_data():
    dates = []
    # 최근 15일 중 영업일 5일치 확보 (3일 분석 + 주말 대비)
    for i in range(15):
        target_date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        df = stock.get_market_ohlcv_by_ticker(target_date, market="ALL")
        if not df.empty and df['거래대금'].sum() > 0:
            dates.append((target_date, df))
        if len(dates) == 5: break
    
    if len(dates) < 2: return pd.DataFrame(), "데이터 부족", []
    
    today_date, df_today = dates[0]
    prev_date, df_prev = dates[1]
    
    # 상위 50위 필터링
    top_50_df = df_today.sort_values(by='거래대금', ascending=False).head(50)
    
    results = []
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
            
    return pd.DataFrame(results), today_date, dates

try:
    df_final, used_date, all_dates = get_advanced_data()
    
    if not df_final.empty:
        df_final = df_final.sort_values(by='gap_rate', ascending=False)
        st.success(f"📅 분석 기준일: {used_date} | 검색된 종목: {len(df_final)}개")

        for _, row in df_final.iterrows():
            with st.expander(f"🔥 {row['name']} (갭: {row['gap_rate']:.2f}% | 거래대금: {row['money']:,.0f}억)"):
                
                # --- [추가 기능] 3일간의 흐름 분석 ---
                try:
                    # 해당 종목의 최근 3거래일 데이터 추출
                    ticker_data = []
                    for d_str, d_df in all_dates[:3]:
                        if row['ticker'] in d_df.index:
                            ticker_data.append(d_df.loc[row['ticker']])
                    
                    df_3d = pd.DataFrame(ticker_data)
                    
                    if len(df_3d) >= 2:
                        high_3d = df_3d['고가'].max()
                        low_3d = df_3d['저가'].min()
                        old_price = df_3d['종가'].iloc[-1] # 3일 전 종가
                        current_price = row['price']
                        
                        total_return = ((current_price - old_price) / old_price) * 100
                        from_high = ((high_3d - current_price) / high_3d) * 100
                        
                        st.subheader("🔍 최근 3일 추세 분석")
                        c1, c2, c3 = st.columns(3)
                        c1.metric("3일 누적 수익률", f"{total_return:.2f}%")
                        c2.metric("최고점 대비", f"-{from_high:.2f}%")
                        c3.write("🎯 **분석 의견**")
                        if total_return > 15: c3.warning("단기 과열 주의")
                        elif total_return < 0: c3.info("하락 후 반등 시도")
                        else: c3.success("점진적 상승 중")
                except:
                    st.write("3일 추세 분석 데이터를 불러올 수 없습니다.")

                st.divider()
                
                # 기존 버튼 및 차트 기능
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    st.link_button(f"🔍 테마 검색", f"https://search.naver.com/search.naver?query={row['name']}+관련주+테마")
                with col_btn2:
                    st.link_button(f"📊 상세 정보", f"https://finance.naver.com/item/main.naver?code={row['ticker']}")
                
                if st.checkbox(f"📈 {row['name']} 차트 확인", key=f"ch_{row['ticker']}"):
                    try:
                        start_dt = (datetime.strptime(used_date, "%Y%m%d") - timedelta(days=60)).strftime("%Y%m%d")
                        df_chart = stock.get_market_ohlcv(start_dt, used_date, row['ticker'])
                        import plotly.graph_objects as go
                        fig = go.Figure(data=[go.Candlestick(x=df_chart.index, open=df_chart['시가'], high=df_chart['고가'], low=df_chart['저가'], close=df_chart['종가'], increasing_line_color='red', decreasing_line_color='blue')])
                        fig.update_layout(height=300, margin=dict(l=0,r=0,b=0,t=0), xaxis_rangeslider_visible=False)
                        st.plotly_chart(fig, use_container_width=True)
                    except: st.write("차트 로딩 실패")

    else:
        st.warning("조건에 맞는 종목이 없습니다. 필터를 조절해보세요.")

except Exception as e:
    st.error(f"시스템 오류: {e}")

st.divider()
st.caption(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
