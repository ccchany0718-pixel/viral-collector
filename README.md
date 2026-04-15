# 📱 해외 바이럴 밈/쇼츠 자동 수집기

Reddit + YouTube에서 해외 바이럴 콘텐츠를 매일 수집하고,
Claude AI로 분석해 Markdown 파일로 저장하는 자동화 시스템입니다.

---

## 📁 폴더 구조

```
viral-collector/
│
├── collector.py              # 메인 수집기 (Reddit + YouTube → Claude 분석)
├── formatter.py              # Markdown 포맷터
├── config.py                 # API 키 및 설정
├── requirements.txt          # Python 의존성
│
├── daily_briefs/             # 날짜별 daily brief
│   └── 2025-04-15.md
│
├── weekly_reports/           # 주간 요약 리포트
│   └── 2025-W15.md
│
└── .github/
    └── workflows/
        └── daily_collect.yml  # GitHub Actions 자동 실행 워크플로우
```

---

## 🚀 처음 실행하는 방법 (초보자용)

### Step 1. Python 설치 확인

터미널(또는 명령 프롬프트)에서:
```bash
python --version
# Python 3.10 이상이면 OK
```

없으면 → https://python.org/downloads 에서 설치

---

### Step 2. 이 저장소 다운로드

```bash
git clone https://github.com/your-username/viral-collector.git
cd viral-collector
```

또는 GitHub에서 ZIP 다운로드 후 압축 해제

---

### Step 3. 의존성 설치

```bash
pip install -r requirements.txt
```

---

### Step 4. API 키 설정

#### 방법 A — 환경 변수로 설정 (권장)

**Mac/Linux:**
```bash
export ANTHROPIC_API_KEY="sk-ant-api03-..."
export YOUTUBE_API_KEY="AIza..."        # 선택사항
```

**Windows (PowerShell):**
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-api03-..."
$env:YOUTUBE_API_KEY   = "AIza..."
```

#### 방법 B — config.py 직접 수정

`config.py` 파일을 열어 빈 문자열 부분에 키 입력:
```python
"api_key": os.getenv("ANTHROPIC_API_KEY", "여기에_직접_입력"),
```

> ⚠️ 방법 B 사용 시 절대 GitHub에 push 하지 마세요!
> `.gitignore`에 `config.py`를 추가하거나 환경 변수 방식을 사용하세요.

---

### Step 5. 실행

```bash
# 오늘 daily brief 수집
python collector.py daily

# 주간 리포트 생성 (지난 7일 daily briefs 요약)
python collector.py weekly

# 수집 + 일요일이면 주간 리포트까지
python collector.py both
```

실행 후 `daily_briefs/2025-04-15.md` 파일이 생성됩니다.

---

## 🤖 GitHub Actions 자동 실행 설정

매일 자동으로 실행되게 하려면:

### Step 1. GitHub 저장소에 Secret 등록

저장소 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Secret 이름 | 값 |
|-------------|-----|
| `ANTHROPIC_API_KEY` | Anthropic API 키 |
| `YOUTUBE_API_KEY` | YouTube API 키 (선택) |

### Step 2. 워크플로우 파일 확인

`.github/workflows/daily_collect.yml` 이 이미 포함되어 있습니다.
GitHub에 push하면 자동으로 활성화됩니다.

### Step 3. 실행 시간 변경 (선택)

`daily_collect.yml`에서 cron 표현식 수정:
```yaml
- cron: "0 23 * * *"   # UTC 23:00 = KST 08:00
```

[crontab.guru](https://crontab.guru) 에서 쉽게 변경 가능

---

## 🔑 API 키 발급 방법

### Anthropic API 키 (Claude 분석용)
1. https://console.anthropic.com 접속
2. Sign up / 로그인
3. Settings → API Keys → Create Key
4. `sk-ant-api03-...` 형태의 키 복사

> 💡 없어도 동작합니다! 대신 Claude 분석 없이 메타데이터만 저장됩니다.

### YouTube Data API v3 키 (선택사항)
1. https://console.cloud.google.com 접속
2. 새 프로젝트 생성
3. API 및 서비스 → 라이브러리 → "YouTube Data API v3" 검색 → 사용 설정
4. 사용자 인증 정보 → API 키 생성
5. `AIza...` 형태의 키 복사

> 💡 없으면 Reddit만 수집합니다. Reddit은 API 키 없이 동작합니다.

---

## 📄 출력 파일 형식

```
daily_briefs/YYYY-MM-DD.md
weekly_reports/YYYY-WXX.md
```

각 항목 포함 내용:
- 제목 + 원본 링크
- 지표 (조회수 / 스코어 / 댓글수)
- 🎣 훅 (Hook)
- 📝 상황 요약
- 💥 댓글 반응 폭발 포인트
- 🚀 왜 바이럴 되는가
- 💑 부부/연인 콘텐츠 적용 가능성
- 포맷 타입 & 바이럴 점수 (1~10)

---

## 🛠 자주 묻는 질문

**Q. Reddit 수집이 안 돼요**
`config.py`의 `user_agent`를 본인 GitHub 주소로 변경해보세요.

**Q. YouTube 수집이 0개예요**
YouTube API 키 등록 여부와 API 할당량(일 10,000 단위) 초과 여부 확인.

**Q. 분석이 "자동 분석 미실행"으로 나와요**
`ANTHROPIC_API_KEY` 환경 변수가 제대로 설정됐는지 확인하세요.

**Q. 수집 서브레딧을 바꾸고 싶어요**
`config.py`의 `subreddits` 리스트를 수정하세요.
