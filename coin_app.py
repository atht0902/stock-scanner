import streamlit as st
from pycoingecko import CoinGeckoAPI
import pandas as pd
from datetime import datetime
import time

# 웹 페이지 설정
st.set_page_config(page_title="글로벌 코인 급등 스캐너", layout="wide")

# CoinGecko API 초기화
cg = CoinGeckoAPI()

# 사이드바 필터
st.sidebar.header("🎯 필터 설정")
min_change = st.sidebar.slider("최소 24h 변동률 (%)", 0.0, 50.0, 5.0, 1.0)
min_volume = st.sidebar.number_input("최소 거래량 (백만 USD)", 0, 1000, 10)
top_n = st.sidebar.slider("상위 코인 개수", 50, 500, 250, 50)
sort_by = st.sidebar.selectbox("정렬 기준", [
    "24h 변동률 (높은 순)",
    "24h 변동률 (낮은 순)", 
    "거래량 (높은 순)",
    "시가총액 (높은 순)"
])

st.title("🌍 글로벌 암호화폐 급등 스캐너")
st.write("CoinGecko API 기반 | 전 세계 코인 실시간 추적")

# 데이터 로드 함수
@st.cache_data(ttl=120)  # 2분 캐시
def get_coingecko_data(top_coins, min_vol):
    """CoinGecko에서 코인 데이터 수집"""
    try:
        # 시가총액 상위 코인 가져오기
        coins = cg.get_coins_markets(
            vs_currency='usd',
            order='market_cap_desc',
            per_page=top_coins,
            sparkline=False,
            price_change_percentage='24h,7d'
        )
        
        results = []
        
        for coin in coins:
            # 거래량 필터 (백만 달러 단위)
            volume_usd = coin.get('total_volume', 0) / 1000000
            
            if volume_usd < min_vol:
                continue
            
            # 변동률
            change_24h = coin.get('price_change_percentage_24h', 0)
            change_7d = coin.get('price_change_percentage_7d_in_currency', 0)
            
            results.append({
                'id': coin['id'],
                'symbol': coin['symbol'].upper(),
                'name': coin['name'],
                'current_price': coin.get('current_price', 0),
                'change_24h': change_24h if change_24h else 0,
                'change_7d': change_7d if change_7d else 0,
                'market_cap': coin.get('market_cap', 0),
                'volume_usd': volume_usd,
                'rank': coin.get('market_cap_rank', 999),
                'high_24h': coin.get('high_24h', 0),
                'low_24h': coin.get('low_24h', 0),
                'ath': coin.get('ath', 0),  # All Time High
                'ath_change': coin.get('ath_change_percentage', 0),
                'image': coin.get('image', '')
            })
        
        return pd.DataFrame(results)
        
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        return pd.DataFrame()

# 차트 그리기 함수
def draw_chart(coin_id, days=30):
    """CoinGecko 차트"""
    try:
        # 히스토리 데이터
        data = cg.get_coin_market_chart_by_id(
            id=coin_id,
            vs_currency='usd',
            days=days
        )
        
        if not data or 'prices' not in data:
            st.warning("차트 데이터를 불러올 수 없습니다.")
            return
        
        # 데이터프레임 변환
        df = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        import plotly.graph_objects as go
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['price'],
            mode='lines',
            name='Price',
            line=dict(color='#00d4aa', width=2),
            fill='tozeroy',
            fillcolor='rgba(0, 212, 170, 0.1)'
        ))
        
        fig.update_layout(
            height=400,
            margin=dict(l=0, r=0, b=0, t=30),
            xaxis_title="",
            yaxis_title="Price (USD)",
            title=f"가격 추이 ({days}일)",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"차트 오류: {e}")

# 메인 로직
try:
    with st.spinner('🔍 CoinGecko에서 데이터 수집 중...'):
        df_coins = get_coingecko_data(top_n, min_volume)
    
    if not df_coins.empty:
        # 변동률 필터 적용
        df_coins = df_coins[abs(df_coins['change_24h']) >= min_change].copy()
        
        # 정렬
        if sort_by == "24h 변동률 (높은 순)":
            df_coins = df_coins.sort_values(by='change_24h', ascending=False)
        elif sort_by == "24h 변동률 (낮은 순)":
            df_coins = df_coins.sort_values(by='change_24h', ascending=True)
        elif sort_by == "거래량 (높은 순)":
            df_coins = df_coins.sort_values(by='volume_usd', ascending=False)
        else:  # 시가총액
            df_coins = df_coins.sort_values(by='market_cap', ascending=False)
        
        if df_coins.empty:
            st.warning("⚠️ 조건에 맞는 코인이 없습니다. 필터를 조정해보세요.")
        else:
            st.success(f"🔥 필터 통과 코인: {len(df_coins)}개 | 분석 대상: 상위 {top_n}개")
            
            # 상위 3개 요약
            col1, col2, col3 = st.columns(3)
            
            for idx, (col, medal) in enumerate([(col1, "🥇"), (col2, "🥈"), (col3, "🥉")]):
                if idx < len(df_coins):
                    coin = df_coins.iloc[idx]
                    with col:
                        change_emoji = "🚀" if coin['change_24h'] > 0 else "📉"
                        st.metric(
                            f"{medal} {coin['symbol']}",
                            f"${coin['current_price']:,.4f}" if coin['current_price'] < 1 else f"${coin['current_price']:,.2f}",
                            f"{coin['change_24h']:+.2f}%",
                            delta_color="normal"
                        )
            
            st.divider()
            
            # 전체 코인 리스트
            for idx, row in df_coins.iterrows():
                # 가격 표시 포맷
                if row['current_price'] < 0.01:
                    price_str = f"${row['current_price']:.6f}"
                elif row['current_price'] < 1:
                    price_str = f"${row['current_price']:.4f}"
                else:
                    price_str = f"${row['current_price']:,.2f}"
                
                # 변동률 색상
                change_emoji = "🚀" if row['change_24h'] > 0 else "📉"
                change_color = "🟢" if row['change_24h'] > 0 else "🔴"
                
                with st.expander(
                    f"{change_emoji} **{row['name']}** ({row['symbol']}) - {price_str} {change_color} {row['change_24h']:+.2f}%"
                ):
                    # 메트릭
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("현재가", price_str)
                    c2.metric("24h 변동", f"{row['change_24h']:+.2f}%")
                    c3.metric("7d 변동", f"{row['change_7d']:+.2f}%")
                    c4.metric("거래량", f"${row['volume_usd']:,.1f}M")
                    
                    # 추가 정보
                    c5, c6, c7, c8 = st.columns(4)
                    c5.write(f"📊 시총순위: **#{row['rank']}**")
                    c6.write(f"💰 시가총액: **${row['market_cap']/1e9:.2f}B**")
                    c7.write(f"📈 24h 고가: **${row['high_24h']:,.4f}**")
                    c8.write(f"📉 24h 저가: **${row['low_24h']:,.4f}**")
                    
                    # ATH 정보
                    st.write(f"🏆 역대 최고가: **${row['ath']:,.2f}** (현재 {row['ath_change']:+.1f}%)")
                    
                    # 외부 링크
                    col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
                    with col_btn1:
                        st.link_button("🦎 CoinGecko", f"https://www.coingecko.com/en/coins/{row['id']}")
                    with col_btn2:
                        st.link_button("💹 CoinMarketCap", f"https://coinmarketcap.com/currencies/{row['id']}/")
                    with col_btn3:
                        st.link_button("🔍 뉴스 검색", f"https://www.google.com/search?q={row['name']}+crypto+news&tbm=nws")
                    with col_btn4:
                        st.link_button("💬 Reddit", f"https://www.reddit.com/search/?q={row['name']}")
                    
                    st.divider()
                    
                    # 차트
                    if st.checkbox(f"📈 {row['name']} 차트 보기", key=f"chart_{row['id']}"):
                        chart_period = st.radio(
                            "기간 선택",
                            [7, 30, 90, 365],
                            format_func=lambda x: f"{x}일",
                            horizontal=True,
                            key=f"period_{row['id']}"
                        )
                        draw_chart(row['id'], days=chart_period)
    
    else:
        st.warning("⚠️ 데이터를 불러올 수 없습니다.")

except Exception as e:
    st.error(f"❌ 오류 발생: {e}")

# 새로고침
st.divider()
col_r1, col_r2, col_r3 = st.columns([2, 1, 1])
with col_r1:
    st.caption(f"⏰ 마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
with col_r2:
    if st.button("🔄 새로고침"):
        st.rerun()
with col_r3:
    st.caption("🦎 Powered by CoinGecko")

st.caption("💡 Tip: CoinGecko는 전 세계 코인 데이터를 제공하며 지역 제한이 없습니다!")
