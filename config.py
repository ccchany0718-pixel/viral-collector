"""
config.py  ―  수집기 설정 파일
API 키와 수집 옵션을 여기서 관리합니다.
"""

import os

CONFIG = {

    # ── Anthropic (Claude 분석) ─────────────────────────────────────────────
    # https://console.anthropic.com/settings/keys 에서 발급
    "anthropic": {
        "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
    },

    # ── YouTube Data API v3 ─────────────────────────────────────────────────
    # https://console.cloud.google.com 에서 YouTube Data API v3 활성화 후 발급
    "youtube": {
        "api_key":     os.getenv("YOUTUBE_API_KEY", ""),
        "region":      "US",
        "max_results": 10,
    },

    # ── Reddit (API 키 불필요 — 공개 JSON 사용) ─────────────────────────────
    "reddit": {
        "user_agent": "ViralCollector/1.0 (github.com/ccchany0718-pixel/viral-collector)",
"subreddits": [
    "PublicFreakout",
    "funny",
    "videos",
    "memes",
    "nextfuckinglevel",
    "CrazyFuckingVideos",
    "interestingasfuck",
    "Pranks",
    "couples",
    "Parenting",
    "daddit",
    "Fatherhood",
    "NewParents",
],
"limit_per_sub": 5,
    },

    # ── 일반 설정 ───────────────────────────────────────────────────────────
    "general": {
        "timezone": "Asia/Seoul",
    },
}
