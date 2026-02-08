import streamlit as st
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta

# 1. 웹 페이지 기본 설정
st.set_page_config(page_title="주식 종목 선별기", layout="wide")
st.title("📈 오늘의 종목 선별 리스트")
st.write("시장 거래대금 상위 50위 종목 중 선별된 리스트입니다.")

# 2. 날짜 설정 (데이터가 있는 가장 최근 영업일 찾기)
@st.cache_data # 데이터를 매번 새로 받지 않고 속도를 높이기 위한 설정
def get_stock_data():
    target_date = datetime.now().strftime("%Y%m%d")
    df = stock.get_market_ohlcv_by_ticker(target_date, market="ALL")
    
    # 주말이나 장 시작 전이라 데이터가 없으면 어제로 변경
    if df.empty:
        target_date = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        df = stock.get_market_ohlcv_by_ticker(target_date, market="ALL")
    return df, target_date

try:
    df, used_date = get_stock_data()
    
    # 3. 거래대금 기준 내림차순 정렬 후 상위 50개 추출
    top_50 = df.sort_values(by='거래대금', ascending=False).head(50)
    
    st.info(f"📅 분석 기준일: {used_date} (거래대금 상위 50위 기준)")
    st.divider()

    # 4. 종목별 리스트 출력
    for ticker, row in top_50.iterrows():
        name = stock.get_market_ticker_name(ticker)
        
        # 종목별로 접었다 폈다 할 수 있는 카드 구성
        with st.expander(f"📌 {name} ({ticker})"):
            # 왼쪽/오른쪽 칸 나누기
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**[데이터 정보]**")
                st.write(f"- 💰 거래대금: **{row['거래대금'] / 100000000:.1f} 억원**")
                st.write(f"- 📊 등락률: **{row['등락률']:.2f}%**")
                st.write(f"- 📉 종가: **{row['종가']:,}원**")
            
            with col2:
                st.write("**[선별 근거]**")
                st.write("✅ 거래대금 상위 50위 이내 (시장 관심도 높음)")
                st.write("✅ 익일 시가 상승갭 패턴 분석 대상")
                st.write("✅ 관련 이슈 및 뉴스 확인 필요")

            # 네이버 금융 링크 연결
            naver_url = f"https://finance.naver.com/item/main.naver?code={ticker}"
            st.link_button(f"🔗 {name} 상세 정보/뉴스 보기", naver_url)

except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")
    st.write("장 시작 전이거나 공휴일일 수 있습니다. 잠시 후 다시 시도해 주세요.")