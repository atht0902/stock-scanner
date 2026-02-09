import streamlit as st
import pandas as pd
from pykrx import stock
from datetime import datetime, timedelta
import requests

# 1. 테마 및 애니메이션 CSS 설정
st.set_page_config(page_title="홍익 미래 유산 검색기", layout="wide")

st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    .stApp { background-color: #0A0C10; font-family: 'Pretendard', sans-serif; }
    
    .main-title {
        font-size: clamp(1.4rem, 7vw, 2.5rem);
        background: linear-gradient(to right, #FFD700, #FDB931);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        text-align: center;
        padding: 10px 0px;
    }

    /* 유산 가치 알람: 10% 이상 상승 시 황금색 테두리 및 번쩍임 효과 */
    .gold-alert {
        border: 2px solid #FFD700 !important;
        box-shadow: 0px 0px 15px rgba(255, 215, 0, 0.5);
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(255, 215, 0, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(255, 215, 0, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 215, 0, 0); }
    }

    .streamlit-expanderHeader {
        background-color: #161B22 !important;
        border-radius: 12px !important;
        border: 1px solid #30363D !important;
        color: white !important;
    }
    [data-testid="stMetricValue"] { color: #FFD700 !important; font-size: 1.4rem !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-title">🏛️ 홍익 미래 유산 검색기</div>', unsafe_allow_html=True)
st.markdown('<p style="color:#808495; text-align:center; font-size:14px; margin-bottom:25px;">널리 주식 투자자를 이롭게 하는 자산 발굴 시스템</p>', unsafe_allow_html=True)

# 2. 데이터 엔진
@st.cache_data(ttl=3600)
def get_heritage_data():
    try:
        url = "https://finance.naver.com/sise/sise_quant.naver?sosok=0"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        df = pd.read_html(res.text, encoding='cp949')[1].dropna().head(10)
        return "실시간 데이터", df[['종목명', '현재가', '등락률', '거래량']]
    except:
        return None, None

source, final_df = get_heritage_data()

# 3. 화면 렌더링
if final_df is not None:
    cols = st.columns(2)
    for i, row in final_df.reset_index().iterrows():
        with cols[i % 2]:
            name = row['종목명']
            change_str = row['등락률'].replace('%', '').replace('+', '')
            try:
                change_val = float(change_str)
            except:
                change_val = 0.0
            
            # 알람 기능: 10% 이상이면 강조 이모지 추가
            alert_icon = "🔥" if change_val >= 10 else "💎"
            
            with st.expander(f"{alert_icon} {name} ({row['등락률']})"):
                m1, m2 = st.columns(2)
                m1.metric("현재가", f"{int(row['현재가']):,}원")
                m2.metric("거래량", f"{int(row['거래량']):,}주")
                
                # 버튼 레이아웃
                b1, b2 = st.columns(2)
                with b1:
                    chart_url = f"https://finance.naver.com/item/main.naver?code={name}" # 실제로는 검색연결이 안전
                    st.link_button("📊 상세 분석", f"https://finance.naver.com/search/search.naver?query={name}", use_container_width=True)
                with b2:
                    # 간편 공유: 네이버 종목 토론실이나 정보 페이지 링크를 공유
                    share_text = f"[{name}] 현재 등락률 {row['등락률']}! 미래 유산으로 어때요?"
                    # 모바일에서 카카오톡/메시지로 복사하기 쉬운 링크 제공
                    st.link_button("🔗 공유하기", f"https://social-plugins.line.me/lineit/share?url=https://finance.naver.com/search/search.naver?query={name}", use_container_width=True)

    if any(float(str(r).replace('%','').replace('+','')) >= 10 for r in final_df['등락률'] if '%' in str(r)):
        st.info("💡 현재 가치가 급상승 중인 '황금 유산' 후보가 포착되었습니다!")

    st.divider()
    st.caption("Produced by Hong-Ik Heritage Finder • Free Edition")
else:
    st.error("서버 점검 중입니다. 내일 아침 9시에 다시 만나요!")
