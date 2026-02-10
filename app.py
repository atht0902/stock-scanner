import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone

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
        padding: 1.2rem 0.5rem 0.8rem;
    }
    .main-header h1 {
        font-size: clamp(1.3rem, 5vw, 2rem);
        color: #ffd700;
        margin: 0;
        white-space: nowrap;
    }
    .main-header p {
        color: #888;
        font-size: clamp(0.7rem, 2.5vw, 0.85rem);
        margin-top: 4px;
    }
    .status-box {
        padding: 14px;
        border-radius: 12px;
        border: 1px solid rgba(255,215,0,0.3);
        text-align: center;
        background: rgba(255,215,0,0.05);
        margin: 10px 0;
        font-size: 0.9rem;
    }
    .score-card {
        padding: 10px 14px;
        border-radius: 10px;
        margin: 6px 0;
        font-size: clamp(0.75rem, 2.5vw, 0.88rem);
        line-height: 1.6;
    }
    .score-high {
        background: rgba(255, 68, 68, 0.15);
        border-left: 4px solid #ff4444;
    }
    .score-mid {
        background: rgba(255, 165, 0, 0.12);
        border-left: 4px solid #ffa500;
    }
    .score-low {
        background: rgba(100, 100, 100, 0.1);
        border-left: 4px solid #666;
    }
    .signal-tag {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 20px;
        font-size: 0.7rem;
        margin: 2px 2px;
        font-weight: 600;
    }
    .tag-vol { background: rgba(0,150,255,0.2); color: #4dc9f6; }
    .tag-consec { background: rgba(0,200,100,0.2); color: #4dff91; }
    .tag-bounce { background: rgba(255,100,0,0.2); color: #ffa044; }
    .tag-sector { background: rgba(200,0,255,0.2); color: #d48fff; }
    .legend-box {
        background: rgba(255,255,255,0.03);
        border: 1px solid #333;
        border-radius: 10px;
        padding: 12px;
        margin: 8px 0 16px;
        font-size: clamp(0.68rem, 2.2vw, 0.8rem);
        color: #aaa;
        line-height: 1.7;
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
    .disclaimer {
        background: rgba(255,215,0,0.05);
        border: 1px solid rgba(255,215,0,0.15);
        border-radius: 8px;
        padding: 10px;
        font-size: 0.7rem;
        color: #888;
        text-align: center;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ===== 헤더 =====
st.markdown("""
<div class="main-header">
    <h1>🔔 홍익 미래유산 검색기</h1>
    <p>4대 시그널 기반 급등 예측 스캐너</p>
</div>
""", unsafe_allow_html=True)

# ===== 종목 + 섹터 매핑 =====
SECTOR_MAP = {
    # 반도체
    "005930.KS": ("삼성전자", "반도체"),
    "000660.KS": ("SK하이닉스", "반도체"),
    "009150.KS": ("삼성전기", "반도체"),
    "034220.KS": ("LG디스플레이", "반도체"),
    "067310.KQ": ("하나마이크론", "반도체"),
    "058470.KQ": ("리노공업", "반도체"),
    "036930.KQ": ("주성엔지니어링", "반도체"),
    "240810.KQ": ("원익IPS", "반도체"),
    "005290.KQ": ("동진쎄미켐", "반도체"),
    "089030.KQ": ("테크윙", "반도체"),
    "403870.KQ": ("HPSP", "반도체"),
    "095340.KQ": ("ISC", "반도체"),
    "039030.KQ": ("이오테크닉스", "반도체"),
    "140860.KQ": ("파크시스템스", "반도체"),
    # 2차전지/에너지
    "373220.KS": ("LG에너지솔루션", "2차전지"),
    "051910.KS": ("LG화학", "2차전지"),
    "006400.KS": ("삼성SDI", "2차전지"),
    "003670.KS": ("포스코퓨처엠", "2차전지"),
    "247540.KQ": ("에코프로비엠", "2차전지"),
    "086520.KQ": ("에코프로", "2차전지"),
    "383310.KQ": ("에코프로에이치엔", "2차전지"),
    "078600.KQ": ("대주전자재료", "2차전지"),
    "009830.KS": ("한화솔루션", "2차전지"),
    # 자동차
    "005380.KS": ("현대차", "자동차"),
    "000270.KS": ("기아", "자동차"),
    "012330.KS": ("현대모비스", "자동차"),
    "004020.KS": ("현대제철", "자동차"),
    "161390.KS": ("한국타이어앤테크놀로지", "자동차"),
    "329180.KS": ("현대오토에버", "자동차"),
    # 바이오/제약
    "207940.KS": ("삼성바이오로직스", "바이오"),
    "068270.KS": ("셀트리온", "바이오"),
    "000100.KS": ("유한양행", "바이오"),
    "128940.KS": ("한미약품", "바이오"),
    "326030.KS": ("SK바이오팜", "바이오"),
    "028300.KQ": ("HLB", "바이오"),
    "196170.KQ": ("알테오젠", "바이오"),
    "145020.KQ": ("휴젤", "바이오"),
    "068760.KQ": ("셀트리온제약", "바이오"),
    "141080.KQ": ("레고켐바이오", "바이오"),
    "298380.KQ": ("에이비엘바이오", "바이오"),
    "214150.KQ": ("클래시스", "바이오"),
    # IT/플랫폼
    "035420.KS": ("NAVER", "IT/플랫폼"),
    "035720.KS": ("카카오", "IT/플랫폼"),
    "018260.KS": ("삼성에스디에스", "IT/플랫폼"),
    "377300.KQ": ("카카오페이", "IT/플랫폼"),
    "042000.KQ": ("카페24", "IT/플랫폼"),
    "067160.KQ": ("아프리카TV", "IT/플랫폼"),
    # 게임/엔터
    "036570.KS": ("엔씨소프트", "게임/엔터"),
    "259960.KQ": ("크래프톤", "게임/엔터"),
    "263750.KQ": ("펄어비스", "게임/엔터"),
    "293490.KQ": ("카카오게임즈", "게임/엔터"),
    "112040.KQ": ("위메이드", "게임/엔터"),
    "352820.KQ": ("하이브", "게임/엔터"),
    "041510.KQ": ("에스엠", "게임/엔터"),
    "035900.KQ": ("JYP Ent.", "게임/엔터"),
    "253450.KQ": ("스튜디오드래곤", "게임/엔터"),
    # 금융
    "105560.KS": ("KB금융", "금융"),
    "055550.KS": ("신한지주", "금융"),
    "086790.KS": ("하나금융지주", "금융"),
    "316140.KS": ("우리금융지주", "금융"),
    "024110.KS": ("기업은행", "금융"),
    "138040.KS": ("메리츠금융지주", "금융"),
    "000810.KS": ("삼성화재", "금융"),
    "032830.KS": ("삼성생명", "금융"),
    "006800.KS": ("미래에셋증권", "금융"),
    "016360.KS": ("삼성증권", "금융"),
    # 조선/방산
    "009540.KS": ("한국조선해양", "조선/방산"),
    "267250.KS": ("현대중공업", "조선/방산"),
    "042660.KS": ("한화오션", "조선/방산"),
    "010140.KS": ("삼성중공업", "조선/방산"),
    "047810.KS": ("한국항공우주", "조선/방산"),
    # 철강/소재
    "005490.KS": ("POSCO홀딩스", "철강/소재"),
    "010130.KS": ("고려아연", "철강/소재"),
    "011170.KS": ("롯데케미칼", "철강/소재"),
    "003410.KS": ("쌍용C&E", "철강/소재"),
    "011790.KS": ("SKC", "철강/소재"),
    "357780.KQ": ("솔브레인", "철강/소재"),
    # 유통/소비재
    "139480.KS": ("이마트", "유통/소비재"),
    "002790.KS": ("아모레퍼시픽", "유통/소비재"),
    "271560.KS": ("오리온", "유통/소비재"),
    "021240.KS": ("코웨이", "유통/소비재"),
    "007070.KS": ("GS리테일", "유통/소비재"),
    "008770.KS": ("호텔신라", "유통/소비재"),
    # 에너지/인프라
    "096770.KS": ("SK이노베이션", "에너지/인프라"),
    "010950.KS": ("S-Oil", "에너지/인프라"),
    "015760.KS": ("한국전력", "에너지/인프라"),
    "036460.KS": ("한국가스공사", "에너지/인프라"),
    "034020.KS": ("두산에너빌리티", "에너지/인프라"),
    # 지주/통신
    "034730.KS": ("SK", "지주/통신"),
    "003550.KS": ("LG", "지주/통신"),
    "028260.KS": ("삼성물산", "지주/통신"),
    "017670.KS": ("SK텔레콤", "지주/통신"),
    "030200.KS": ("KT", "지주/통신"),
    "078930.KS": ("GS", "지주/통신"),
    "006260.KS": ("LS", "지주/통신"),
    # 물류/운송
    "011200.KS": ("HMM", "물류/운송"),
    "003490.KS": ("대한항공", "물류/운송"),
    "180640.KS": ("한진칼", "물류/운송"),
    "047050.KS": ("포스코인터내셔널", "물류/운송"),
}

# ===== 필터 UI =====
col1, col2 = st.columns(2)
with col1:
    sector_options = ["전체"] + sorted(set(v[1] for v in SECTOR_MAP.values()))
    selected_sector = st.selectbox("📂 섹터 필터", sector_options)
with col2:
    min_score = st.selectbox("🎯 최소 점수", ["전체 보기", "50점 이상", "70점 이상"])


# ===== 분석 엔진 =====
@st.cache_data(ttl=300)
def run_analysis():
    tickers = list(SECTOR_MAP.keys())
    all_results = []

    # 섹터별 등락률 집계용
    sector_changes = {}

    batch_size = 50
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        try:
            data = yf.download(
                batch, period="60d", group_by="ticker",
                progress=False, threads=True
            )
            if data.empty:
                continue

            for ticker in batch:
                try:
                    name, sector = SECTOR_MAP[ticker]

                    if len(batch) == 1:
                        df = data.copy()
                    else:
                        df = data[ticker].copy()

                    df = df.dropna(subset=["Close"])
                    if len(df) < 10:
                        continue

                    close = df["Close"].values
                    volume = df["Volume"].values
                    opens = df["Open"].values
                    highs = df["High"].values
                    lows = df["Low"].values

                    latest_close = close[-1]
                    latest_volume = volume[-1]

                    # 전일 대비 등락률
                    if len(close) >= 2 and close[-2] > 0:
                        change_pct = ((close[-1] - close[-2]) / close[-2]) * 100
                    else:
                        change_pct = 0.0

                    # ── 시그널 1: 거래량 급증 비율 (20일 평균 대비) ──
                    vol_score = 0
                    vol_ratio = 0.0
                    if len(volume) >= 21:
                        avg_vol_20 = np.mean(volume[-21:-1])
                        if avg_vol_20 > 0:
                            vol_ratio = latest_volume / avg_vol_20
                            if vol_ratio >= 5.0:
                                vol_score = 30
                            elif vol_ratio >= 3.0:
                                vol_score = 25
                            elif vol_ratio >= 2.0:
                                vol_score = 20
                            elif vol_ratio >= 1.5:
                                vol_score = 15
                            elif vol_ratio >= 1.2:
                                vol_score = 10

                    # ── 시그널 2: 연속 N일 거래량 증가 ──
                    consec_score = 0
                    consec_days = 0
                    for j in range(len(volume) - 1, 0, -1):
                        if volume[j] > volume[j - 1]:
                            consec_days += 1
                        else:
                            break
                    if consec_days >= 5:
                        consec_score = 20
                    elif consec_days >= 4:
                        consec_score = 16
                    elif consec_days >= 3:
                        consec_score = 12
                    elif consec_days >= 2:
                        consec_score = 8

                    # ── 시그널 3: 눌림목 후 반등 (MA20 근접 + 양봉) ──
                    bounce_score = 0
                    ma_distance = 0.0
                    if len(close) >= 20:
                        ma20 = np.mean(close[-20:])
                        if ma20 > 0:
                            ma_distance = ((latest_close - ma20) / ma20) * 100
                            is_bullish = close[-1] > opens[-1]
                            is_near_ma = -3.0 <= ma_distance <= 5.0
                            prev_was_down = False
                            if len(close) >= 5:
                                prev_was_down = close[-3] > close[-2]  # 직전 하락

                            if is_near_ma and is_bullish:
                                bounce_score = 20
                                if prev_was_down:
                                    bounce_score = 30  # 눌림 후 반등 보너스
                            elif is_near_ma:
                                bounce_score = 10

                    # 섹터 등락률 집계
                    if sector not in sector_changes:
                        sector_changes[sector] = []
                    sector_changes[sector].append(change_pct)

                    all_results.append({
                        "ticker": ticker,
                        "종목명": name,
                        "섹터": sector,
                        "현재가": int(latest_close),
                        "등락률": round(change_pct, 2),
                        "거래량": int(latest_volume),
                        "거래량비율": round(vol_ratio, 1),
                        "연속증가일": consec_days,
                        "MA20괴리": round(ma_distance, 1),
                        "vol_score": vol_score,
                        "consec_score": consec_score,
                        "bounce_score": bounce_score,
                    })
                except Exception:
                    continue
        except Exception:
            continue

    if not all_results:
        return pd.DataFrame()

    result_df = pd.DataFrame(all_results)

    # ── 시그널 4: 섹터 동반 상승 ──
    sector_scores = {}
    for sector, changes in sector_changes.items():
        up_count = sum(1 for c in changes if c > 0)
        total = len(changes)
        up_ratio = up_count / total if total > 0 else 0
        if up_ratio >= 0.8:
            sector_scores[sector] = 20
        elif up_ratio >= 0.6:
            sector_scores[sector] = 15
        elif up_ratio >= 0.4:
            sector_scores[sector] = 10
        else:
            sector_scores[sector] = 0

    result_df["sector_score"] = result_df["섹터"].map(sector_scores).fillna(0).astype(int)

    # ── 종합 점수 (100점 만점) ──
    result_df["종합점수"] = (
        result_df["vol_score"]
        + result_df["consec_score"]
        + result_df["bounce_score"]
        + result_df["sector_score"]
    )

    return result_df


# ===== 실행 =====
status_placeholder = st.empty()

try:
    status_placeholder.markdown(
        '<div class="status-box">⏳ 4대 시그널 분석 엔진 가동 중...<br>'
        '거래량 급증 · 연속 증가 · 눌림목 반등 · 섹터 동반상승</div>',
        unsafe_allow_html=True,
    )

    result_df = run_analysis()

    if result_df.empty:
        status_placeholder.warning("📭 데이터를 불러올 수 없습니다. 잠시 후 다시 시도해주세요.")
    else:
        # 필터 적용
        if selected_sector != "전체":
            result_df = result_df[result_df["섹터"] == selected_sector]

        if min_score == "50점 이상":
            result_df = result_df[result_df["종합점수"] >= 50]
        elif min_score == "70점 이상":
            result_df = result_df[result_df["종합점수"] >= 70]

        # 점수 순 정렬
        result_df = result_df.sort_values("종합점수", ascending=False).head(20)

        status_placeholder.empty()

        now_kst = datetime.now(KST)
        st.success(f"✅ {now_kst.strftime('%Y.%m.%d %H:%M')} 분석 완료 | {len(result_df)}종목 감지")

        # 시그널 범례
        st.markdown("""
        <div class="legend-box">
            <span class="signal-tag tag-vol">📊 거래량급증</span> 20일 평균 대비 거래량 폭증 비율<br>
            <span class="signal-tag tag-consec">📈 연속증가</span> 연속 N일 거래량 상승 패턴<br>
            <span class="signal-tag tag-bounce">🔄 눌림목반등</span> MA20 근접 후 양봉 반등 신호<br>
            <span class="signal-tag tag-sector">🏭 섹터동반</span> 동일 섹터 내 종목 동반 상승
        </div>
        """, unsafe_allow_html=True)

        # 카드형 결과 출력
        for _, row in result_df.iterrows():
            score = row["종합점수"]

            if score >= 70:
                card_class = "score-high"
                grade = "🔥"
            elif score >= 50:
                card_class = "score-mid"
                grade = "⚡"
            else:
                card_class = "score-low"
                grade = "💤"

            # 활성화된 시그널 태그
            tags = ""
            if row["vol_score"] > 0:
                tags += f'<span class="signal-tag tag-vol">📊 x{row["거래량비율"]}</span>'
            if row["consec_score"] > 0:
                tags += f'<span class="signal-tag tag-consec">📈 {row["연속증가일"]}일연속</span>'
            if row["bounce_score"] > 0:
                tags += f'<span class="signal-tag tag-bounce">🔄 MA{row["MA20괴리"]:+.1f}%</span>'
            if row["sector_score"] > 0:
                tags += f'<span class="signal-tag tag-sector">🏭 {row["섹터"]}</span>'

            change_color = "#ff4444" if row["등락률"] >= 0 else "#4488ff"
            change_str = f"{row['등락률']:+.2f}%"

            st.markdown(f"""
            <div class="score-card {card_class}">
                <b>{grade} {row['종목명']}</b>
                <span style="float:right; color:#ffd700; font-weight:bold;">{score}점</span><br>
                <span style="color:#aaa;">{row['섹터']}</span> ·
                <span>{row['현재가']:,}원</span> ·
                <span style="color:{change_color}; font-weight:bold;">{change_str}</span> ·
                <span style="color:#aaa;">거래량 {row['거래량']:,}</span><br>
                {tags}
            </div>
            """, unsafe_allow_html=True)

        # 면책 문구
        st.markdown("""
        <div class="disclaimer">
            ⚠️ 본 정보는 투자 권유가 아닌 참고용 데이터입니다.<br>
            투자 판단과 그에 따른 손익은 투자자 본인에게 있습니다.
        </div>
        """, unsafe_allow_html=True)

except Exception as e:
    status_placeholder.error(f"⚠️ 엔진 오류: {e}")

# 푸터
st.markdown(
    '<div class="footer">Produced by Hong-Ik Heritage Finder • Premium Edition v2.0</div>',
    unsafe_allow_html=True,
)