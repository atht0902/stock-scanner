import streamlit as st
import pandas as pd
from pykrx import stock
from datetime import datetime, timedelta

st.set_page_config(page_title="퀀트 스캐너(네이버 백업)", layout="wide")
st.title("🚀 하이브리드 종목 스캐너")

# 1. [보조 데이터] 네이버 금융 실시간 거래상위 긁어오기
def get_naver_top_data():
    try:
        # 네이버 금융 '거래상위' 코스피(0), 코스닥(1) 페이지
        url_kospi = "https://finance.naver.com/sise/sise_quant.naver?sosok=0"
        url_kosdaq = "https://finance.naver.com/sise/sise_quant.naver?sosok=1"
        
        # HTML에서 표만 추출
        df_list = pd.read_html(url_kospi, encoding='cp949')
        df_kospi = df_list[1].dropna() # 실제 종목 데이터가 있는 두 번째 표
        
        df_list = pd.read_html(url_kosdaq, encoding='cp949')
        df_kosdaq = df_list[1].dropna()
        
        df_total = pd.concat([df_kospi, df_kosdaq])
        # 필요한 컬럼만 정리 (종목명, 현재가, 등락률, 거래량 등)
        return df_total[['종목명', '현재가', '등락률', '거래량']]
    except:
        return None

# 2. [주 데이터] 거래소(pykrx) 데이터 가져오기 (캐싱 강화)
@st.cache_data(ttl=300)
def get_main_data():
    target_dt = datetime.now().strftime("%Y%m%d")
    try:
        df = stock.get_market_ohlcv_by_ticker(target_dt, market="ALL")
        if df is not None and not df.empty:
            return target_dt, df
    except:
        return None, None

# --- 메인 로직 시작 ---
final_dt, market_df = get_main_data()

if market_df is not None:
    st.success(f"✅ 거래소 공식 데이터 모드 ({final_dt})")
    # ... (기존 pykrx 처리 로직) ...
    top_df = market_df.sort_values(by='거래대금', ascending=False).head(20)
    st.dataframe(top_df[['종가', '등락률', '거래대금']], use_container_width=True)

else:
    # 3. 거래소 서버가 죽었을 때 네이버 데이터를 대신 출력!
    st.warning("⚠️ 거래소 점검 중! 네이버 실시간 순위로 전환합니다.")
    naver_df = get_naver_top_data()
    
    if naver_df is not None:
        # 모바일에서도 보기 좋게 리스트업
        for index, row in naver_df.head(20).iterrows():
            with st.expander(f"🔥 {row['종목명']} ({row['등락률']})"):
                st.metric("현재가", f"{row['현재가']:,}원")
                st.write(f"거래량: {row['거래량']:,}주")
                # 네이버 차트 링크 자동 생성은 여기서도 가능
                # (종목코드가 네이버 표에는 없으므로 종목명으로 검색 링크 연결 가능)
                search_url = f"https://finance.naver.com/search/search.naver?query={row['종목명']}"
                st.link_button("📊 차트 보기", search_url, use_container_width=True)
    else:
        st.error("모든 데이터 서버가 응답하지 않습니다.")
