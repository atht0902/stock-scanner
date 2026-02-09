import streamlit as st
import pandas as pd
from pykrx import stock
from datetime import datetime, timedelta
import requests

# 1. 페이지 기본 설정 (모바일 대응)
st.set_page_config(page_title="퀀트 하이브리드", layout="wide")
st.title("🚀 밤에도 쌩쌩한 하이브리드 스캐너")

# 2. 철벽 캐싱 함수 (데이터를 메모리에 1시간 보관)
@st.cache_data(ttl=3600)
def get_naver_backup():
    try:
        # 네이버 금융 '거래상위' (코스피)
        url = "https://finance.naver.com/sise/sise_quant.naver?sosok=0"
        # 헤더를 추가하여 차단 방지
        header = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=header)
        df_list = pd.read_html(res.text, encoding='cp949')
        df = df_list[1].dropna().head(15) # 상위 15개만 가볍게
        return df[['종목명', '현재가', '등락률', '거래량']]
    except:
        return None

@st.cache_data(ttl=3600)
def get_krx_main():
    # 최근 영업일 찾기 로직
    for i in range(5):
        dt = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        try:
            df = stock.get_market_ohlcv_by_ticker(dt, market="ALL")
            if df is not None and not df.empty:
                return dt, df.sort_values(by='거래대금', ascending=False).head(15)
        except: continue
    return None, None

# --- 메인 실행부 ---
with st.spinner('안전한 통로로 데이터를 불러오는 중...'):
    # 메인(KRX) 시도
    dt, krx_df = get_krx_main()
    # 보조(Naver) 로드 (미리 캐싱)
    naver_df = get_naver_backup()

# 3. 화면 렌더링 (모바일 반응형)
if krx_df is not None:
    st.success(f"✅ 거래소 공식 모드 가동 ({dt})")
    source_df = krx_df
    
    for ticker in source_df.index:
        name = stock.get_market_ticker_name(ticker)
        row = source_df.loc[ticker]
        
        # 모바일 카드형 레이아웃
        with st.expander(f"📍 {name} ({row['등락률']:.2f}%)"):
            c1, c2 = st.columns(2)
            c1.metric("현재가", f"{int(row['종가']):,}원")
            c2.metric("거래대금", f"{int(row['거래대금']/100000000)}억")
            st.link_button("📊 네이버 차트", f"https://finance.naver.com/item/main.naver?code={ticker}", use_container_width=True)

elif naver_df is not None:
    st.warning("⚠️ 거래소 서버 점검 중! 네이버 모드로 전환되었습니다.")
    
    for _, row in naver_df.iterrows():
        with st.expander(f"🔥 {row['종목명']} ({row['등락률']})"):
            c1, c2 = st.columns(2)
            c1.metric("현재가", f"{row['현재가']:,}원")
            c2.write(f"거래량: {row['거래량']:,}주")
            # 종목코드가 없으므로 '검색' 페이지로 연결
            st.link_button("🔍 종목 상세/차트", f"https://finance.naver.com/search/search.naver?query={row['종목명']}", use_container_width=True)

else:
    st.error("❗ 모든 서버가 잠시 휴식 중입니다. 5분 뒤 다시 시도해주세요!")
