"""
collector.py  ―  해외 바이럴 밈/쇼츠 메타데이터 수집기
매일 Reddit + YouTube 에서 인기 콘텐츠를 긁어와 Claude 로 분석 후
daily_briefs/ 에 Markdown 파일로 저장합니다.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

from config import CONFIG
from formatter import format_daily_brief, format_weekly_report

# ── 경로 설정 ─────────────────────────────────────────────────────────────────
ROOT       = Path(__file__).parent
DAILY_DIR  = ROOT / "daily_briefs"
WEEKLY_DIR = ROOT / "weekly_reports"
DAILY_DIR.mkdir(exist_ok=True)
WEEKLY_DIR.mkdir(exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
# 1. Reddit 수집  (API 키 불필요 — JSON 엔드포인트 사용)
# ══════════════════════════════════════════════════════════════════════════════

def fetch_reddit_posts(subreddit: str, limit: int = 10) -> list[dict]:
    url     = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
    headers = {"User-Agent": CONFIG["reddit"]["user_agent"]}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        posts = []
        for item in r.json()["data"]["children"]:
            d = item["data"]
            is_video = d.get("is_video") or d.get("url", "").endswith((".mp4", ".gif"))
            is_short = any(kw in d.get("title", "").lower()
                           for kw in ["shorts", "tiktok", "reel", "viral", "trend", "meme"])
            if not (is_video or is_short):
                continue
            posts.append({
                "source":    "reddit",
                "subreddit": subreddit,
                "id":        d["id"],
                "title":     d.get("title", ""),
                "url":       f"https://reddit.com{d.get('permalink', '')}",
                "score":     d.get("score", 0),
                "comments":  d.get("num_comments", 0),
                "flair":     d.get("link_flair_text", ""),
                "thumbnail": d.get("thumbnail", ""),
                "created":   datetime.utcfromtimestamp(
                                 d.get("created_utc", 0)).isoformat(),
            })
        return posts
    except Exception as e:
        print(f"  [Reddit/{subreddit}] 오류: {e}")
        return []


def fetch_reddit_top_comments(subreddit: str, post_id: str) -> list[str]:
    url     = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.json?limit=5"
    headers = {"User-Agent": CONFIG["reddit"]["user_agent"]}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        comments = []
        for item in r.json()[1]["data"]["children"][:3]:
            body = item["data"].get("body", "").strip()
            if body and body != "[deleted]":
                comments.append(body[:200])
        return comments
    except Exception:
        return []


# ══════════════════════════════════════════════════════════════════════════════
# 2. YouTube Trending  (Data API v3)
# ══════════════════════════════════════════════════════════════════════════════

def fetch_youtube_trending(max_results: int = 10) -> list[dict]:
    api_key = CONFIG["youtube"].get("api_key", "")
    if not api_key:
        print("  [YouTube] API 키 없음 → 건너뜀")
        return []

    keywords = [
        "couple prank shorts",
        "husband wife funny shorts",
        "parenting funny shorts",
        "marriage relatable shorts",
        "dad mom baby funny",
        "prank shorts",
        "couple prank reaction",
        "funny prank shorts viral",
        "wife prank husband shorts",
        "baby toddler funny shorts",
    ]

    posts = []
    for keyword in keywords:
        params = {
            "part":          "snippet",
            "q":             keyword,
            "type":          "video",
            "videoDuration": "short",
            "order":         "date",
            "maxResults":    3,
            "key":           api_key,
        }
        try:
            r = requests.get(
                "https://www.googleapis.com/youtube/v3/search",
                params=params, timeout=10)
            r.raise_for_status()
            for item in r.json().get("items", []):
                vid_id = item["id"].get("videoId", "")
                snip   = item["snippet"]
                posts.append({
                    "source":      "youtube",
                    "id":          vid_id,
                    "title":       snip.get("title", ""),
                    "url":         f"https://youtu.be/{vid_id}",
                    "channel":     snip.get("channelTitle", ""),
                    "description": snip.get("description", "")[:300],
                    "created":     snip.get("publishedAt", ""),
                    "comments":    0,
                    "views":       0,
                    "likes":       0,
                    "tags":        [],
                })
        except Exception as e:
            print(f"  [YouTube/{keyword}] 오류: {e}")

    return posts[:max_results]

# ══════════════════════════════════════════════════════════════════════════════
# 3. Claude AI 분석  (Anthropic Messages API)
# ══════════════════════════════════════════════════════════════════════════════

def analyze_with_claude(post: dict) -> dict:
    api_key = CONFIG["anthropic"].get("api_key", "")
    if not api_key:
        return _fallback_analysis(post)

    prompt = f"""다음 바이럴 콘텐츠를 분석해줘. 반드시 JSON 만 출력해. 한국어 사용.

제목: {post.get('title', '')}
설명/태그: {post.get('description', post.get('flair', ''))}
댓글수: {post.get('comments', 0)}
좋아요/스코어: {post.get('likes', post.get('score', 0))}
출처: {post.get('source', '')}

아래 JSON 형식으로만 응답 (다른 텍스트, 마크다운 펜스 금지):
{{
  "hook": "첫 3초 안에 시청자를 잡는 핵심 훅 (1~2문장)",
  "situation_summary": "콘텐츠 상황 요약 (2~3문장)",
  "comment_points": ["댓글 반응 폭발 포인트1", "포인트2", "포인트3"],
  "why_viral": "왜 바이럴 되는지 핵심 이유 (2~3문장)",
  "couple_application": "부부/연인 콘텐츠 적용 아이디어 (1~2문장)",
  "format_type": "쇼츠/밈/챌린지/리액션/스토리텔링 중 하나",
  "viral_score": 숫자만(1~10)
}}"""

    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key":          api_key,
                "anthropic-version":  "2023-06-01",
                "content-type":       "application/json",
            },
            json={
                "model":      "claude-haiku-4-5-20251001",
                "max_tokens": 600,
                "messages":   [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        r.raise_for_status()
        raw = r.json()["content"][0]["text"].strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception as e:
        print(f"  [Claude 분석 오류] {e} → fallback 사용")
        return _fallback_analysis(post)


def _fallback_analysis(post: dict) -> dict:
    return {
        "hook":               "자동 분석 미실행 (config.py에 ANTHROPIC_API_KEY 입력 필요)",
        "situation_summary":  post.get("title", "")[:120],
        "comment_points":     ["수동 확인 필요"],
        "why_viral":          "분석 미실행",
        "couple_application": "수동 검토 필요",
        "format_type":        "미분류",
        "viral_score":        0,
    }


# ══════════════════════════════════════════════════════════════════════════════
# 4. 메인 파이프라인
# ══════════════════════════════════════════════════════════════════════════════

def collect_daily(date: datetime | None = None) -> list[dict]:
    date = date or datetime.now()
    print(f"\n📡 수집 시작: {date.strftime('%Y-%m-%d')}")
    all_posts: list[dict] = []

    for sub in CONFIG["reddit"]["subreddits"]:
        print(f"  Reddit r/{sub} 수집 중...")
        posts = fetch_reddit_posts(sub, limit=CONFIG["reddit"]["limit_per_sub"])
        for p in posts:
            p["comments_sample"] = fetch_reddit_top_comments(sub, p["id"])
        all_posts.extend(posts)
        print(f"    → {len(posts)}개")

    print("  YouTube 트렌딩 수집 중...")
    yt = fetch_youtube_trending(max_results=CONFIG["youtube"].get("max_results", 10))
    all_posts.extend(yt)
    print(f"    → {len(yt)}개")

    # 중복 제거
    seen, unique = set(), []
    for p in all_posts:
        if p["id"] not in seen:
            seen.add(p["id"])
            unique.append(p)

    print(f"\n🤖 Claude 분석 중... (총 {len(unique)}개)")
    for i, post in enumerate(unique, 1):
        print(f"  [{i}/{len(unique)}] {post['title'][:55]}...")
        post["analysis"] = analyze_with_claude(post)

    return unique


def save_daily_brief(posts: list[dict], date: datetime | None = None) -> Path:
    date     = date or datetime.now()
    filename = DAILY_DIR / f"{date.strftime('%Y-%m-%d')}.md"
    filename.write_text(format_daily_brief(posts, date), encoding="utf-8")
    print(f"\n✅ Daily Brief 저장 → {filename}")
    return filename


def save_weekly_report(week_start: datetime | None = None) -> Path | None:
    week_start  = week_start or (datetime.now() - timedelta(days=6))
    weekly_data = []
    for i in range(7):
        day  = week_start + timedelta(days=i)
        path = DAILY_DIR / f"{day.strftime('%Y-%m-%d')}.md"
        if path.exists():
            weekly_data.append({"date": day.strftime("%Y-%m-%d"), "path": str(path)})

    if not weekly_data:
        print("  주간 리포트: 수집된 daily brief 없음")
        return None

    week_label = f"{week_start.strftime('%Y-W%U')}"
    filename   = WEEKLY_DIR / f"{week_label}.md"
    filename.write_text(format_weekly_report(weekly_data, week_start), encoding="utf-8")
    print(f"✅ Weekly Report 저장 → {filename}")
    return filename


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "daily"

    if mode == "daily":
        posts = collect_daily()
        save_daily_brief(posts)

    elif mode == "weekly":
        save_weekly_report()

    elif mode == "both":
        posts = collect_daily()
        save_daily_brief(posts)
        if datetime.now().weekday() == 6:   # 일요일마다 주간 리포트
            save_weekly_report()

    else:
        print("사용법: python collector.py [daily|weekly|both]")
