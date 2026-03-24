# HairMaker ✂

헤어샵 전용 AI 헤어 스타일 추천 & 시뮬레이터

손님 얼굴 사진 한 장으로 어울리는 헤어스타일을 추천하고, 원하는 스타일을 실제 얼굴에 AI로 합성해 미리보기 합니다. 헤어 디자이너와 손님이 함께 태블릿을 보며 스타일을 결정할 수 있도록 설계된 B2B 솔루션입니다.

---

## 주요 기능

| 기능 | 설명 |
|---|---|
| 카메라 촬영 | 실시간 얼굴 감지 가이드로 최적의 사진 촬영 |
| AI 얼굴형 분석 | Claude claude-sonnet-4-6 Vision으로 얼굴형·특징 분석 |
| 스타일 추천 | 얼굴형에 맞는 헤어스타일 최대 12가지 즉시 추천 |
| AI 시뮬레이션 | FLUX Kontext Pro로 실제 얼굴에 헤어스타일 합성 (15–30초) |
| 상담 메모 | 자동 저장되는 상담 노트 |
| 결과 공유 | 인쇄 / PDF 저장 |

---

## 기술 스택

```
태블릿 브라우저 (Next.js 16)
        │
        ▼
Python FastAPI (백엔드)
    ├── Claude claude-sonnet-4-6 Vision  → 얼굴형 분석
    ├── Replicate FLUX Kontext Pro       → 헤어 시뮬레이션
    ├── OpenCV / Pillow                  → 이미지 전처리
    └── Supabase                         → DB + Storage + Auth
```

| 역할 | 기술 |
|---|---|
| 프론트엔드 | Next.js 16, TypeScript, Tailwind CSS |
| 백엔드 | Python FastAPI |
| 얼굴 분석 | Claude claude-sonnet-4-6 (Anthropic) |
| 헤어 합성 | FLUX Kontext Pro (Replicate) |
| 데이터베이스 | Supabase (PostgreSQL) |
| 파일 스토리지 | Supabase Storage |
| 인증 | Supabase Auth |

---

## 프로젝트 구조

```
HairMaker/
├── frontend/                        # Next.js 16 웹앱
│   ├── app/
│   │   ├── page.tsx                 # 대시보드 홈
│   │   ├── session/
│   │   │   ├── new/page.tsx         # 카메라 촬영
│   │   │   └── [id]/
│   │   │       ├── page.tsx         # 얼굴 분석 + 스타일 추천 (핵심 화면)
│   │   │       ├── simulate/        # AI 시뮬레이션 화면
│   │   │       └── summary/         # 상담 결과 + 인쇄
│   ├── components/
│   │   ├── camera/                  # 카메라 캡처 + 얼굴 감지
│   │   ├── analysis/                # 얼굴형 분석 카드
│   │   ├── styles/                  # 스타일 그리드 + 카드
│   │   ├── simulation/              # 시뮬레이션 결과 + 진행 표시
│   │   └── consultation/            # 상담 메모 패널
│   └── lib/
│       ├── api.ts                   # FastAPI 클라이언트
│       ├── types.ts                 # TypeScript 타입 정의
│       └── hooks/                   # useCamera, useSimulation
│
├── backend/                         # Python FastAPI
│   └── app/
│       ├── main.py                  # 앱 진입점 + CORS
│       ├── routers/                 # sessions, photos, analysis, styles, simulate
│       ├── services/
│       │   ├── claude_service.py    # 얼굴 분석 프롬프트 + Anthropic API
│       │   ├── replicate_service.py # FLUX Kontext Pro 헤어 합성
│       │   ├── image_service.py     # OpenCV 이미지 전처리
│       │   └── storage_service.py   # Supabase Storage 업로드
│       └── db/
│           ├── client.py            # Supabase 클라이언트
│           └── queries.py           # 스타일 추천 랭킹 쿼리
│
├── supabase/
│   └── schema.sql                   # DB 스키마 (Supabase SQL Editor에 실행)
├── scripts/
│   └── seed_catalog.py              # 헤어스타일 카탈로그 초기 데이터 (20개)
└── docker-compose.yml               # 로컬 개발 (backend + redis)
```

---

## 시작하기

### 1. 필요한 API 키 준비

| 서비스 | 발급 위치 |
|---|---|
| Anthropic API Key | https://console.anthropic.com |
| Replicate API Token | https://replicate.com/account/api-tokens |
| Supabase URL + Keys | https://supabase.com → 프로젝트 Settings → API |

### 2. Supabase 설정

1. [supabase.com](https://supabase.com)에서 새 프로젝트 생성
2. SQL Editor에서 `supabase/schema.sql` 전체 실행
3. Storage에서 버킷 3개 생성:
   - `session-photos` — private
   - `simulation-results` — private
   - `style-catalog` — public

### 3. 백엔드 실행

```bash
cd backend
cp .env.example .env
# .env 파일에 API 키 입력
pip install -r requirements.txt
uvicorn app.main:app --reload
# → http://localhost:8000
```

### 4. 프론트엔드 실행

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
# → http://localhost:3000
```

### 5. 헤어스타일 카탈로그 시드

```bash
cd ..  # HairMaker 루트에서
python scripts/seed_catalog.py
```

---

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|---|---|---|
| POST | `/api/v1/sessions` | 새 세션 생성 |
| GET | `/api/v1/sessions/{id}` | 세션 조회 |
| POST | `/api/v1/sessions/{id}/photo` | 사진 업로드 + 전처리 |
| GET | `/api/v1/sessions/{id}/analysis` | 얼굴 분석 (SSE 스트림) |
| GET | `/api/v1/styles` | 스타일 목록 조회 |
| POST | `/api/v1/simulate` | 시뮬레이션 작업 큐 등록 |
| GET | `/api/v1/simulate/{job_id}` | 시뮬레이션 상태 폴링 |
| PATCH | `/api/v1/sessions/{id}/notes` | 상담 메모 저장 |
| GET | `/api/v1/sessions/{id}/summary` | 세션 요약 조회 |

FastAPI 자동 문서: http://localhost:8000/docs

---

## 사용자 흐름

```
1. [새 손님 시작] 버튼 클릭
2. 카메라 화면 → 얼굴을 타원에 맞추고 촬영
3. Claude AI가 얼굴형 분석 (약 3–5초)
4. 얼굴형에 맞는 스타일 12가지 즉시 표시
5. 디자이너와 손님이 함께 스타일 선택
6. [미리보기] → AI가 실제 얼굴에 합성 (15–30초)
7. 원본과 결과를 나란히 비교
8. "이 스타일로 결정" → 상담 메모 작성
9. 결과 인쇄 or PDF 저장
```

---

## 세션당 비용 예상

| 항목 | 비용 |
|---|---|
| Claude 얼굴 분석 (1회) | ~$0.005 |
| FLUX 시뮬레이션 (2회) | ~$0.16 |
| Supabase Storage | ~$0.001 |
| **합계** | **~$0.17** |

하루 20세션 기준 월 약 $100 → 헤어샵당 월 $99–299 구독 모델로 수익화 가능

---

## 로컬 개발 (Docker)

```bash
# backend + redis 동시 실행
docker-compose up

# 프론트엔드는 별도 실행
cd frontend && npm run dev
```
