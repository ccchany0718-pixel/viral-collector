"""
viral_collector/formatter.py
수집된 메타데이터를 Markdown 형식으로 변환
"""

import datetime


def _score_to_hype(score: int) -> str:
    if score >= 100000: return "🔥🔥🔥 초바이럴"
    elif score >= 50000: return "🔥🔥 강바이럴"
    elif score >= 10000: return "🔥 바이럴"
    elif score >= 1000:  return "📈 상승세"
    else:                return "👀 주목"

def _source_badge(source: str) -> str:
    return {"reddit": "🟠 Reddit", "youtube": "🔴 YouTube"}.get(source, f"🌐 {source}")

def _guess_why_viral(item: dict) -> str:
    text = (item.get("title", "") + " " + " ".join(item.get("tags", []))).lower()
    reasons = []
    if any(w in text for w in ["fail","mistake","oops","wrong"]):   reasons.append("공감형 실패/실수 콘텐츠")
    if any(w in text for w in ["surprise","unexpected","plot twist","wait for it"]): reasons.append("반전/서프라이즈 구조")
    if any(w in text for w in ["wholesome","heartwarming","cute","adorable"]):       reasons.append("훈훈함·감동 유발")
    if any(w in text for w in ["funny","hilarious","lol","comedy"]):                 reasons.append("유머/웃음 코드")
    if any(w in text for w in ["satisfying","perfect","asmr"]):                      reasons.append("만족감/도파민 자극")
    if any(w in text for w in ["couple","marriage","husband","wife","partner"]):      reasons.append("관계/커플 공감 콘텐츠")
    if any(w in text for w in ["life hack","tip","trick","how to","tutorial"]):       reasons.append("유용한 꿀팁/정보 전달")
    if any(w in text for w in ["challenge","trend","viral"]):                         reasons.append("챌린지·트렌드 편승")
    score = item.get("score", 0) + item.get("view_count", 0) // 1000
    if score > 50000: reasons.append("압도적 참여 지표 (알고리즘 부스트)")
    return " / ".join(reasons) if reasons else "추가 분석 필요"

def _couple_applicability(item: dict) -> str:
    text = (item.get("title", "") + " " + " ".join(item.get("tags", []))).lower()
    score = 0; notes = []
    if any(w in text for w in ["couple","husband","wife","marriage","partner","together"]): score+=3; notes.append("커플/부부 소재 직접 매칭")
    if any(w in text for w in ["love","sweet","romantic","anniversary"]):                   score+=2; notes.append("애정·로맨스 요소")
    if any(w in text for w in ["family","home","daily life","routine"]):                    score+=2; notes.append("일상·가족 소재")
    if any(w in text for w in ["funny","wholesome","relatable"]):                           score+=1; notes.append("공감·훈훈 포맷 활용 가능")
    if any(w in text for w in ["fail","argue","fight"]):                                    score+=1; notes.append("갈등→해결 구조로 역용 가능")
    if score >= 5:   level = "⭐⭐⭐ 높음 — 직접 포맷 차용 가능"
    elif score >= 3: level = "⭐⭐ 중간 — 각색 후 활용"
    elif score >= 1: level = "⭐ 낮음 — 아이디어 참고용"
    else:            level = "➖ 해당 없음"
    detail = " · ".join(notes) if notes else "직접 연관 키워드 없음"
    return f"{level}\n  > {detail}"

def _extract_hook(title: str) -> str:
    t = title.strip()
    if "?" in t: return f'질문형 훅 → 호기심 자극: "{t[:60]}"'
    if any(t.lower().startswith(w) for w in ["watch","wait","look","see","check","this","when"]): return f'명령형 훅 → 즉각 행동 유도: "{t[:60]}"'
    if any(w in t.lower() for w in ["pov:","story:","i was","my "]): return f'1인칭 서사형 → 몰입감 유발: "{t[:60]}"'
    if any(t.startswith(str(n)) for n in range(1,20)): return f'숫자 서두 → 정보 기대감 유발: "{t[:60]}"'
    return f'제목이 곧 훅: "{t[:60]}"'

def format_item_block(item: dict, rank: int) -> str:
    title    = item.get("title", "(제목 없음)")
    url      = item.get("url", "")
    source   = _source_badge(item.get("source", ""))
    score    = item.get("score", 0) or item.get("view_count", 0)
    comments = item.get("num_comments", item.get("comment_count", 0))
    top_c    = item.get("top_comments", [])

    situation_parts = []
    if item.get("subreddit"):     situation_parts.append(f"r/{item['subreddit']}")
    if item.get("channel"):       situation_parts.append(f"채널: {item['channel']}")
    if item.get("upvote_ratio"):  situation_parts.append(f"업보트율: {item['upvote_ratio']*100:.0f}%")
    situation = " · ".join(situation_parts) or "정보 없음"

    comment_lines = "\n".join(f'  - "{c[:150]}"' for c in top_c[:3]) or "  - 댓글 데이터 없음"

    return f"""
---

### {rank}. {title}

| 항목 | 내용 |
|------|------|
| 📌 출처 | {source} |
| 🔗 링크 | [{url[:60]}]({url}) |
| 📊 반응 | {_score_to_hype(score)} ({score:,}) · 👁 조회 {item.get("views", 0):,} · 👍 {item.get("likes", 0):,} |
| 💬 댓글 수 | {comments:,}개 |
| 🏷️ 상황 | {situation} |

**🎣 훅 분석**
{_extract_hook(title)}

**🚀 왜 뜨는가**
{_guess_why_viral(item)}

**💬 댓글 포인트**
{comment_lines}

**💑 부부예찬 적용 가능성**
{_couple_applicability(item)}
"""

def format_daily_brief(items: list, date_str: str) -> str:
    weekday_map = {0:"월요일",1:"화요일",2:"수요일",3:"목요일",4:"금요일",5:"토요일",6:"일요일"}
    try:    weekday = weekday_map[datetime.date.fromisoformat(date_str).weekday()]
    except: weekday = ""

    header = f"""# 🎬 바이럴 쇼츠 Daily Brief — {date_str} ({weekday})

> 자동 수집 | 영상 원본 없음 · 메타데이터 & 분석만 포함
> 수집 건수: **{len(items)}개**

## 📋 오늘의 하이라이트

| 순위 | 제목 | 출처 | 반응 |
|------|------|------|------|
"""
    for i, item in enumerate(items[:10], 1):
        header += f"| {i} | {item.get('title','')[:40]}... | {item.get('source','')} | {(item.get('score',0) or item.get('view_count',0)):,} |\n"

    body = "\n---\n\n## 🔍 상세 분석\n"
    for i, item in enumerate(items, 1):
        body += format_item_block(item, i)

    footer = f"""

---

## 📝 오늘의 메모

<!-- 직접 메모 추가 가능 -->

---
*생성: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")} · viral-collector v1*
"""
    return header + body + footer

def format_weekly_report(week_files: list, week_label: str) -> str:
    date_range = f"{week_files[-1][0]} ~ {week_files[0][0]}" if week_files else ""
    report = f"""# 📊 주간 바이럴 리포트 — {week_label}

> 기간: {date_range} | 수집 일수: {len(week_files)}일

## 이번 주 요약

| 날짜 | 파일 |
|------|------|
"""
    for date_str, _ in week_files:
        report += f"| {date_str} | [daily_briefs/{date_str}.md](../daily_briefs/{date_str}.md) |\n"

    report += """
---

## 🔥 이번 주 트렌드 패턴

### 반복 등장한 포맷
- ( 분석 후 기입 )

### 주목할 훅 패턴
- ( 분석 후 기입 )

### 부부예찬 활용 아이디어
- ( 분석 후 기입 )

"""
    for date_str, _ in week_files:
        report += f"- [{date_str}](../daily_briefs/{date_str}.md)\n"

    report += f"\n---\n*생성: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} · viral-collector v1*\n"
    return report
