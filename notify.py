"""
홍익 미래유산 검색기 - 텔레그램 알림 봇
매일 아침 자동 실행 → 60점 이상 종목 텔레그램 전송
"""

import os
import requests
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone

# ===== 설정 =====
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "여기에_봇_토큰_입력")
CHAT_ID = os.environ.get("CHAT_ID", "여기에_채팅방_ID_입력")
MIN_SCORE = 60
KST = timezone(timedelta(hours=9))

# ===== 종목 + 섹터 매핑 =====
SECTOR_MAP = {
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
    "373220.KS": ("LG에너지솔루션", "2차전지"),
    "051910.KS": ("LG화학", "2차전지"),
    "006400.KS": ("삼성SDI", "2차전지"),
    "003670.KS": ("포스코퓨처엠", "2차전지"),
    "247540.KQ": ("에코프로비엠", "2차전지"),
    "086520.KQ": ("에코프로", "2차전지"),
    "383310.KQ": ("에코프로에이치엔", "2차전지"),
    "078600.KQ": ("대주전자재료", "2차전지"),
    "009830.KS": ("한화솔루션", "2차전지"),
    "005380.KS": ("현대차", "자동차"),
    "000270.KS": ("기아", "자동차"),
    "012330.KS": ("현대모비스", "자동차"),
    "004020.KS": ("현대제철", "자동차"),
    "161390.KS": ("한국타이어앤테크놀로지", "자동차"),
    "329180.KS": ("현대오토에버", "자동차"),
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
    "035420.KS": ("NAVER", "IT/플랫폼"),
    "035720.KS": ("카카오", "IT/플랫폼"),
    "018260.KS": ("삼성에스디에스", "IT/플랫폼"),
    "377300.KQ": ("카카오페이", "IT/플랫폼"),
    "042000.KQ": ("카페24", "IT/플랫폼"),
    "067160.KQ": ("아프리카TV", "IT/플랫폼"),
    "036570.KS": ("엔씨소프트", "게임/엔터"),
    "259960.KQ": ("크래프톤", "게임/엔터"),
    "263750.KQ": ("펄어비스", "게임/엔터"),
    "293490.KQ": ("카카오게임즈", "게임/엔터"),
    "112040.KQ": ("위메이드", "게임/엔터"),
    "352820.KQ": ("하이브", "게임/엔터"),
    "041510.KQ": ("에스엠", "게임/엔터"),
    "035900.KQ": ("JYP Ent.", "게임/엔터"),
    "253450.KQ": ("스튜디오드래곤", "게임/엔터"),
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
    "009540.KS": ("한국조선해양", "조선/방산"),
    "267250.KS": ("현대중공업", "조선/방산"),
    "042660.KS": ("한화오션", "조선/방산"),
    "010140.KS": ("삼성중공업", "조선/방산"),
    "047810.KS": ("한국항공우주", "조선/방산"),
    "005490.KS": ("POSCO홀딩스", "철강/소재"),
    "010130.KS": ("고려아연", "철강/소재"),
    "011170.KS": ("롯데케미칼", "철강/소재"),
    "003410.KS": ("쌍용C&E", "철강/소재"),
    "011790.KS": ("SKC", "철강/소재"),
    "357780.KQ": ("솔브레인", "철강/소재"),
    "139480.KS": ("이마트", "유통/소비재"),
    "002790.KS": ("아모레퍼시픽", "유통/소비재"),
    "271560.KS": ("오리온", "유통/소비재"),
    "021240.KS": ("코웨이", "유통/소비재"),
    "007070.KS": ("GS리테일", "유통/소비재"),
    "008770.KS": ("호텔신라", "유통/소비재"),
    "096770.KS": ("SK이노베이션", "에너지/인프라"),
    "010950.KS": ("S-Oil", "에너지/인프라"),
    "015760.KS": ("한국전력", "에너지/인프라"),
    "036460.KS": ("한국가스공사", "에너지/인프라"),
    "034020.KS": ("두산에너빌리티", "에너지/인프라"),
    "034730.KS": ("SK", "지주/통신"),
    "003550.KS": ("LG", "지주/통신"),
    "028260.KS": ("삼성물산", "지주/통신"),
    "017670.KS": ("SK텔레콤", "지주/통신"),
    "030200.KS": ("KT", "지주/통신"),
    "078930.KS": ("GS", "지주/통신"),
    "006260.KS": ("LS", "지주/통신"),
    "011200.KS": ("HMM", "물류/운송"),
    "003490.KS": ("대한항공", "물류/운송"),
    "180640.KS": ("한진칼", "물류/운송"),
    "047050.KS": ("포스코인터내셔널", "물류/운송"),
}


def run_analysis():
    tickers = list(SECTOR_MAP.keys())
    all_results = []
    sector_changes = {}

    batch_size = 50
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        try:
            data = yf.download(
                batch, period="30d", group_by="ticker",
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

                    latest_close = close[-1]
                    latest_volume = volume[-1]

                    if len(close) >= 2 and close[-2] > 0:
                        change_pct = ((close[-1] - close[-2]) / close[-2]) * 100
                    else:
                        change_pct = 0.0

                    # 시그널 1: 거래량 급증
                    vol_score = 0
                    vol_ratio = 0.0
                    if len(volume) >= 21:
                        avg_vol_20 = np.mean(volume[-21:-1])
                        if avg_vol_20 > 0:
                            vol_ratio = latest_volume / avg_vol_20
                            if vol_ratio >= 5.0: vol_score = 30
                            elif vol_ratio >= 3.0: vol_score = 25
                            elif vol_ratio >= 2.0: vol_score = 20
                            elif vol_ratio >= 1.5: vol_score = 15
                            elif vol_ratio >= 1.2: vol_score = 10

                    # 시그널 2: 연속 N일 거래량 증가
                    consec_score = 0
                    consec_days = 0
                    for j in range(len(volume) - 1, 0, -1):
                        if volume[j] > volume[j - 1]:
                            consec_days += 1
                        else:
                            break
                    if consec_days >= 5: consec_score = 20
                    elif consec_days >= 4: consec_score = 16
                    elif consec_days >= 3: consec_score = 12
                    elif consec_days >= 2: consec_score = 8

                    # 시그널 3: 눌림목 후 반등
                    bounce_score = 0
                    ma_distance = 0.0
                    if len(close) >= 20:
                        ma20 = np.mean(close[-20:])
                        if ma20 > 0:
                            ma_distance = ((latest_close - ma20) / ma20) * 100
                            is_bullish = close[-1] > opens[-1]
                            is_near_ma = -3.0 <= ma_distance <= 5.0
                            prev_was_down = len(close) >= 5 and close[-3] > close[-2]
                            if is_near_ma and is_bullish:
                                bounce_score = 30 if prev_was_down else 20
                            elif is_near_ma:
                                bounce_score = 10

                    if sector not in sector_changes:
                        sector_changes[sector] = []
                    sector_changes[sector].append(change_pct)

                    all_results.append({
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

    # 시그널 4: 섹터 동반 상승
    sector_scores = {}
    for sector, changes in sector_changes.items():
        up_ratio = sum(1 for c in changes if c > 0) / len(changes) if changes else 0
        if up_ratio >= 0.8: sector_scores[sector] = 20
        elif up_ratio >= 0.6: sector_scores[sector] = 15
        elif up_ratio >= 0.4: sector_scores[sector] = 10
        else: sector_scores[sector] = 0

    result_df["sector_score"] = result_df["섹터"].map(sector_scores).fillna(0).astype(int)
    result_df["종합점수"] = (
        result_df["vol_score"] + result_df["consec_score"]
        + result_df["bounce_score"] + result_df["sector_score"]
    )

    return result_df


def build_message(result_df):
    now_kst = datetime.now(KST)
    weekday = ["월", "화", "수", "목", "금", "토", "일"][now_kst.weekday()]

    msg = f"🔔 홍익 미래유산 리포트\n"
    msg += f"📅 {now_kst.strftime('%Y.%m.%d')} ({weekday}) {now_kst.strftime('%H:%M')}\n"
    msg += f"━━━━━━━━━━━━━━━\n\n"

    top = result_df[result_df["종합점수"] >= MIN_SCORE].sort_values("종합점수", ascending=False)

    if top.empty:
        msg += "📭 오늘은 60점 이상 시그널 종목이 없습니다.\n"
        msg += "시장 상황을 지켜봐주세요.\n"
    else:
        for _, row in top.head(15).iterrows():
            score = row["종합점수"]
            grade = "🔥" if score >= 70 else "⚡"

            change_str = f"{row['등락률']:+.2f}%"
            msg += f"{grade} {row['종목명']} [{row['섹터']}] — {score}점\n"
            msg += f"   {row['현재가']:,}원 ({change_str})\n"

            signals = []
            if row["vol_score"] > 0:
                signals.append(f"📊거래량 x{row['거래량비율']}")
            if row["consec_score"] > 0:
                signals.append(f"📈{row['연속증가일']}일연속")
            if row["bounce_score"] > 0:
                signals.append(f"🔄눌림목반등")
            if row["sector_score"] > 0:
                signals.append(f"🏭섹터동반")

            if signals:
                msg += f"   {' | '.join(signals)}\n"
            msg += "\n"

    msg += f"━━━━━━━━━━━━━━━\n"
    msg += f"⚠️ 투자 참고용이며 매수 추천이 아닙니다.\n"
    msg += f"🔔 홍익 미래유산 검색기 v2.0"

    return msg


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("✅ 텔레그램 전송 성공!")
    else:
        print(f"❌ 전송 실패: {response.status_code} - {response.text}")


if __name__ == "__main__":
    print("🔍 분석 엔진 시작...")
    result_df = run_analysis()

    if result_df.empty:
        print("❌ 데이터를 가져올 수 없습니다.")
    else:
        message = build_message(result_df)
        print("\n📨 전송할 메시지:")
        print(message)
        print()
        send_telegram(message)