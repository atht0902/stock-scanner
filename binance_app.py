import streamlit as st
from binance.client import Client
import pandas as pd
from datetime import datetime, timedelta
import time

# 웹 페이지 설정
st.set_page_config(page_title="바이낸스 코인 급등 스캐너", layout="wide")

# 사이드바 필터
st.sidebar.header("🎯 필터 설정")
min_change = st.sidebar.slider("최소 변동률 (%)", 0.0, 30.0, 5.0, 0.5)
time_filter = st.sidebar.selectbox("분석 기간", ["1시간", "4시간", "24시간"])
quote_currency = st.sidebar.selectbox("거래쌍", ["USDT", "BTC", "ETH"])
min_volume = st.sidebar.number_input("최소 거래량 (USDT)", 0, 10000000, 100000)

st.title("🌍 바이낸스 실시간 급등 스캐너")
st.write(f"{quote_currency} 마켓 기준 | 전 세계 최대 거래소")

# Binance Client 초기화 (API 키 없이 공개 데이터만 조회)
client = Client()

# 시간 간격 매핑
INTERVAL_MAP = {
    "1시간": Client.KLINE_INTERVAL_1HOUR,
    "4시간": Client.KLINE_INTERVAL_4HOUR,
    "24시간": Client.KLINE_INTERVAL_1DAY
}

# 데이터 로드 함수
@st.cache_data(ttl=60)
def get_binance_data(quote, time_period, min_vol):
    """바이낸스 데이터 수집 및 분석"""
    try:
        # 24시간 티커 정보 (모든 심볼)
        tickers_24h = client.get_ticker()
        
        results = []
        
        for ticker in tickers_24h:
            symbol = ticker['symbol']
            
            # 선택한 거래쌍만 필터링
            if not symbol.endswith(quote):
                continue
            
            try:
                # 기본 정보
                current_price = float(ticker['lastPrice'])
                volume_24h = float(ticker['quoteVolume'])  # USDT 기준 거래량
                change_24h = float(ticker['priceChangePercent'])
                
                # 거래량 필터
                if volume_24h < min_vol:
                    continue
                
                # 선택한 시간대 변동률 계산
                if time_period == "24시간":
                    change_rate = change_24h
                else:
                    # 캔들 데이터로 계산
                    klines = client.get_klines(
                        symbol=symbol,
                        interval=INTERVAL_MAP[time_period],
                        limit=2
                    )
                    
                    if len(klines) < 2:
                        continue
                    
                    prev_close = float(klines[-2][4])  # 이전 종가
                    current = float(klines[-1][4])      # 현재 종가
                    change_rate = ((current - prev_close) / prev_close) * 100
                
                # 변동률 필터
                if change_rate < min_change:
                    continue
                
                # 코인명 추출
                base_asset = symbol.replace(quote, "")
                
                # 24시간 고가/저가
                high_24h = float(ticker['highPrice'])
                low_24h = float(ticker['lowPrice'])
                
                results.append({
                    'symbol': symbol,
                    'name': base_asset,
                    'current_price': current_price,
                    'change_rate': change_rate,
                    'change_24h': change_24h,
                    'volume_usdt': volume_24h,
                    'high_24h': high_24h,
                    'low_24h': low_24h
                })
                
            except Exception as e:
                continue
        
        return pd.DataFrame(results)
        
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        return pd.DataFrame()

# 차트 그리기 함수
def draw_binance_chart(symbol, days=30):
    """바이낸스 차트 그리기"""
    try:
        # 일봉 데이터
        klines = client.get_historical_klines(
            symbol,
            Client.KLINE_INTERVAL_1DAY,
            f"{days} days ago UTC"
        )
        
        if not klines:
            st.warning("차트 데이터를 불러올 수 없습니다.")
            return
        
        # 데이터프레임 변환
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].astype(float)
        
        import plotly.graph_objects as go
        
        fig = go.Figure(data=[go.Candlestick(
            x=df['timestamp'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            increasing_line_color='#26a69a',
            decreasing_line_color='#ef5350'
        )])
        
        fig.update_layout(
            height=400,
            margin=dict(l=0, r=0, b=0, t=30),
            xaxis_rangeslider_visible=False,
            title=f"{symbol} 일봉 차트 (최근 {days}일)"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"차트 오류: {e}")

# 메인 로직
try:
    with st.spinner('🔍 바이낸스에서 급등 코인 스캔 중...'):
        df_coins = get_binance_data(quote_currency, time_filter, min_volume)
    
    if not df_coins.empty:
        df_coins = df_coins.sort_values(by='change_rate', ascending=False)
        
        st.success(f"🔥 급등 코인 {len(df_coins)}개 발견 | 분석: {time_filter} | 거래쌍: {quote_currency}")
        
        # 상위 급등 코인 요약
        col1, col2, col3 = st.columns(3)
        if len(df_coins) >= 1:
            top1 = df_coins.iloc[0]
            col1.metric(
                f"🥇 {top1['name']}", 
                f"${top1['current_price']:,.4f}" if top1['current_price'] < 1 else f"${top1['current_price']:,.2f}",
                f"+{top1['change_rate']:.2f}%"
            )
        if len(df_coins) >= 2:
            top2 = df_coins.iloc[1]
            col2.metric(
                f"🥈 {top2['name']}", 
                f"${top2['current_price']:,.4f}" if top2['current_price'] < 1 else f"${top2['current_price']:,.2f}",
                f"+{top2['change_rate']:.2f}%"
            )
        if len(df_coins) >= 3:
            top3 = df_coins.iloc[2]
            col3.metric(
                f"🥉 {top3['name']}", 
                f"${top3['current_price']:,.4f}" if top3['current_price'] < 1 else f"${top3['current_price']:,.2f}",
                f"+{top3['change_rate']:.2f}%"
            )
        
        st.divider()
        
        # 전체 코인 리스트
        for idx, row in df_coins.iterrows():
            price_display = f"${row['current_price']:,.4f}" if row['current_price'] < 1 else f"${row['current_price']:,.2f}"
            
            with st.expander(f"🚀 {row['name']} (+{row['change_rate']:.2f}%) - {price_display}"):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("현재가", price_display)
                c2.metric(f"{time_filter} 변동", f"{row['change_rate']:.2f}%")
                c3.metric("24h 변동", f"{row['change_24h']:.2f}%")
                c4.metric("거래량(USDT)", f"${row['volume_usdt']:,.0f}")
                
                col_info1, col_info2 = st.columns(2)
                col_info1.write(f"📈 24h 고가: **${row['high_24h']:,.4f}**")
                col_info2.write(f"📉 24h 저가: **${row['low_24h']:,.4f}**")
                
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                with col_btn1:
                    st.link_button("📊 바이낸스 차트", f"https://www.binance.com/en/trade/{row['symbol']}")
                with col_btn2:
                    st.link_button("🔍 코인마켓캡", f"https://coinmarketcap.com/currencies/{row['name'].lower()}/")
                with col_btn3:
                    st.link_button("💬 트위터", f"https://twitter.com/search?q=${row['name']}")
                
                st.divider()
                
                if st.checkbox(f"📈 {row['name']} 차트 보기", key=f"chart_{row['symbol']}"):
                    draw_binance_chart(row['symbol'], days=30)
    
    else:
        st.warning("⚠️ 조건에 맞는 코인이 없습니다. 필터를 조정해보세요.")

except Exception as e:
    st.error(f"❌ 오류 발생: {e}")
    st.write("바이낸스 API 연결을 확인하세요.")

# 새로고침
st.divider()
col_refresh1, col_refresh2 = st.columns([3, 1])
with col_refresh1:
    st.caption(f"⏰ 마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
with col_refresh2:
    if st.button("🔄 새로고침"):
        st.rerun()

st.caption("💡 Tip: 바이낸스는 전 세계 최대 거래소로 2000개 이상의 코인을 지원합니다!")
st.caption("⚠️ 참고: 한국에서는 바이낸스 직접 거래가 제한될 수 있으나, 데이터 조회는 가능합니다.")