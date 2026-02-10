import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, timezone

# 한국 시간대
KST = timezone(timedelta(hours=9))

st.set_page_config(page_title="홍익 미래유산 검색기", layout="centered")

st.markdown("""
<style>
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 50%, #0a0a0f 100%);
        color: #e0e0e0;
    }
    [data-testid="stHeader"] { background: transparent; }
    .main-header {
        text-align: center;
        padding: 1.5rem 0.5rem 1rem;
    }
    .main-header h1 {
        font-size: clamp(1.3rem, 5vw, 2rem);
        color: #ffd700;
        margin: 0;
        white-space: nowrap;
    }
    .main-header p {
        color: #888;
        font-size: clamp(0.7rem, 2.5vw, 0.9rem);
        margin-top: 4px;
    }
    .status-box {
        padding: 14px;
        border-radius: 12px;
        border: 1px solid rgba(255,215,0,0.3);
        text-align: center;
        background: rgba(255,215,0,0.05);
        margin: 10px 0;
        font-size: 0.95rem;
    }
    .stTable table {
        width: 100%;
        font-size: clamp(0.7rem, 2.5vw, 0.9rem);
    }
    .stTable th {
        background-color: #1a1a2e !important;
        color: #ffd700 !important;
        font-size: clamp(0.7rem, 2.5vw, 0.85rem);
        padding: 8px 6px !important;
        white-space: nowrap;
    }
    .stTable td {
        padding: 6px !important;
        white-space: nowrap;
        color: #e0e0e0 !important;
    }
    .stSelectbox label {
        color: #ffd700 !important;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .footer {
        text-align: center;
        color: #555;
        font-size: 0.75rem;
        padding: 20px 0 10px;
        border-top: 1px solid #222;
        margin-top: 20px;
    }
    [data-testid="stHorizontalBlock"] { gap: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# 헤더
st.markdown("""
<div class="main-header">
    <h1>🔔 홍익 미래유산 검색기</h1>
    <p>널리 주식 투자자를 이롭게 하는 미래 자산 발굴 시스템</p>
</div>
""", unsafe_allow_html=True)

# 필터 UI
col1, col2 = st.columns(2)
with col1:
    category = st.selectbox("📂 분류", ["🔥 거래급등 (단기이슈)", "💎 우량주 (중장기)"])
with col2:
    filter_val = st.selectbox("📈 등락 필터", ["전체 보기", "5% 이상", "10% 이상"])

# ===== 한국 주요 종목 리스트 (KOSPI + KOSDAQ 상위 200개) =====
KOREAN_STOCKS = {
    # KOSPI 대형주
    "005930.KS": "삼성전자", "000660.KS": "SK하이닉스", "373220.KS": "LG에너지솔루션",
    "207940.KS": "삼성바이오로직스", "005380.KS": "현대차", "000270.KS": "기아",
    "068270.KS": "셀트리온", "035420.KS": "NAVER", "005490.KS": "POSCO홀딩스",
    "051910.KS": "LG화학", "006400.KS": "삼성SDI", "035720.KS": "카카오",
    "028260.KS": "삼성물산", "105560.KS": "KB금융", "055550.KS": "신한지주",
    "066570.KS": "LG전자", "012330.KS": "현대모비스", "032830.KS": "삼성생명",
    "003670.KS": "포스코퓨처엠", "086790.KS": "하나금융지주",
    "034730.KS": "SK", "015760.KS": "한국전력", "003550.KS": "LG",
    "138040.KS": "메리츠금융지주", "009150.KS": "삼성전기", "018260.KS": "삼성에스디에스",
    "033780.KS": "KT&G", "011200.KS": "HMM", "010130.KS": "고려아연",
    "024110.KS": "기업은행", "316140.KS": "우리금융지주", "000810.KS": "삼성화재",
    "017670.KS": "SK텔레콤", "030200.KS": "KT", "034020.KS": "두산에너빌리티",
    "003490.KS": "대한항공", "036570.KS": "엔씨소프트", "011170.KS": "롯데케미칼",
    "096770.KS": "SK이노베이션", "010950.KS": "S-Oil", "004020.KS": "현대제철",
    "161390.KS": "한국타이어앤테크놀로지", "047050.KS": "포스코인터내셔널",
    "009540.KS": "한국조선해양", "267250.KS": "현대중공업", "042660.KS": "한화오션",
    "329180.KS": "현대오토에버", "006800.KS": "미래에셋증권",
    "000100.KS": "유한양행", "002790.KS": "아모레퍼시픽", "090430.KS": "아모레G",
    "271560.KS": "오리온", "004990.KS": "롯데지주", "008770.KS": "호텔신라",
    "021240.KS": "코웨이", "036460.KS": "한국가스공사", "326030.KS": "SK바이오팜",
    "180640.KS": "한진칼", "078930.KS": "GS", "010140.KS": "삼성중공업",
    "047810.KS": "한국항공우주", "009830.KS": "한화솔루션", "006260.KS": "LS",
    "088350.KS": "한화생명", "000720.KS": "현대건설", "011790.KS": "SKC",
    "016360.KS": "삼성증권", "139480.KS": "이마트", "128940.KS": "한미약품",
    "034220.KS": "LG디스플레이", "001570.KS": "금양",
    "241560.KS": "두산밥캣", "003410.KS": "쌍용C&E", "007070.KS": "GS리테일",
    "069500.KS": "KODEX 200", "005935.KS": "삼성전자우",
    # KOSDAQ 주요 종목
    "247540.KQ": "에코프로비엠", "086520.KQ": "에코프로", "028300.KQ": "HLB",
    "403870.KQ": "HPSP", "196170.KQ": "알테오젠", "039030.KQ": "이오테크닉스",
    "041510.KQ": "에스엠", "095340.KQ": "ISC", "357780.KQ": "솔브레인",
    "006580.KQ": "대양제지", "253450.KQ": "스튜디오드래곤", "112040.KQ": "위메이드",
    "145020.KQ": "휴젤", "293490.KQ": "카카오게임즈", "035900.KQ": "JYP Ent.",
    "352820.KQ": "하이브", "377300.KQ": "카카오페이", "263750.KQ": "펄어비스",
    "067310.KQ": "하나마이크론", "060310.KQ": "3S", "033640.KQ": "네패스",
    "140860.KQ": "파크시스템스", "058470.KQ": "리노공업", "036930.KQ": "주성엔지니어링",
    "322510.KQ": "제이엘케이", "005290.KQ": "동진쎄미켐", "240810.KQ": "원익IPS",
    "078600.KQ": "대주전자재료", "068760.KQ": "셀트리온제약", "214150.KQ": "클래시스",
    "222160.KQ": "NPX반도체", "166090.KQ": "사이닉스", "089030.KQ": "테크윙",
    "365590.KQ": "에이치디현대마린솔루션", "141080.KQ": "레고켐바이오",
    "298380.KQ": "에이비엘바이오", "137310.KQ": "에스디바이오센서",
    "060280.KQ": "큐렉소", "383310.KQ": "에코프로에이치엔",
    "067160.KQ": "아프리카TV", "259960.KQ": "크래프톤", "042000.KQ": "카페24",
    "236810.KQ": "엔비티", "115390.KQ": "락앤락",
}


@st.cache_data(ttl=300)
def fetch_data():
    """Yahoo Finance에서 한국 주식 데이터 가져오기"""
    tickers = list(KOREAN_STOCKS.keys())
    results = []

    # 50개씩 나눠서 요청 (Yahoo Finance 제한 회피)
    batch_size = 50
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        try:
            data = yf.download(
                batch,
                period="5d",
                group_by="ticker",
                progress=False,
                threads=True
            )
            if data.empty:
                continue

            for ticker in batch:
                try:
                    if len(batch) == 1:
                        ticker_data = data
                    else:
                        ticker_data = data[ticker]

                    if ticker_data.empty or len(ticker_data) < 1:
                        continue

                    # 마지막 거래일 데이터
                    latest = ticker_data.iloc[-1]
                    close = latest["Close"]
                    volume = latest["Volume"]

                    # 등락률 계산
                    if len(ticker_data) >= 2:
                        prev_close = ticker_data.iloc[-2]["Close"]
                        if prev_close > 0:
                            change_pct = ((close - prev_close) / prev_close) * 100
                        else:
                            change_pct = 0.0
                    else:
                        change_pct = 0.0

                    name = KOREAN_STOCKS.get(ticker, ticker)

                    results.append({
                        "종목명": name,
                        "현재가": int(close),
                        "등락률": round(change_pct, 2),
                        "거래량": int(volume),
                    })
                except Exception:
                    continue
        except Exception:
            continue

    if not results:
        return pd.DataFrame(columns=["종목명", "현재가", "등락률", "거래량"])

    return pd.DataFrame(results)


# 실행
status_placeholder = st.empty()

try:
    status_placeholder.markdown(
        '<div class="status-box">⏳ 유산 스캐너 엔진 가동 중...</div>',
        unsafe_allow_html=True,
    )

    df = fetch_data()

    if df.empty:
        status_placeholder.warning(
            "📭 현재 조회 가능한 데이터가 없습니다. 장 마감 후 다시 시도해주세요."
        )
    else:
        # 필터 적용
        if filter_val == "5% 이상":
            df = df[df["등락률"] >= 5]
        elif filter_val == "10% 이상":
            df = df[df["등락률"] >= 10]

        # 카테고리별 정렬
        if "거래급등" in category:
            df = df.sort_values(by="거래량", ascending=False).head(30)
        else:
            # 우량주: 현재가 높은 순 (시가총액 대용)
            df = df.sort_values(by="현재가", ascending=False).head(30)

        # 포맷팅
        display_df = df.copy().reset_index(drop=True)
        display_df.index = display_df.index + 1
        display_df["등락률"] = display_df["등락률"].apply(lambda x: f"{x:+.2f}%")
        display_df["현재가"] = display_df["현재가"].apply(lambda x: f"{x:,.0f}원")
        display_df["거래량"] = display_df["거래량"].apply(lambda x: f"{x:,.0f}")

        status_placeholder.empty()

        now_kst = datetime.now(KST)
        st.success(
            f"✅ {now_kst.strftime('%Y.%m.%d %H:%M')} 동기화 완료 | TOP {len(display_df)}종목"
        )
        st.table(display_df)

except Exception as e:
    status_placeholder.error(f"⚠️ 엔진 오류: {e}")

# 푸터
st.markdown(
    '<div class="footer">Produced by Hong-Ik Heritage Finder • Premium Edition</div>',
    unsafe_allow_html=True,
)