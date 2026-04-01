# HairMaker — AI 헤어 스타일 추천 & 시뮬레이션

## ⚠️ 필수 행동 규칙 — 이 섹션은 반드시 따른다

### 에이전트 호출 규칙 (MANDATORY)
**모든 작업은 반드시 `.claude/agents/`에 정의된 에이전트를 통해 수행한다.**
직접 코드를 작성하거나 수정하지 않는다. 반드시 아래 에이전트를 Agent 도구로 호출한다:

1. **새 기능 개발, 복잡한 수정**: `director` 에이전트를 먼저 호출한다. director가 작업을 분석하고 팀에 위임한다.
2. **단순 코드 수정, 버그 픽스**: `programmer` 에이전트를 직접 호출한다.
3. **UI/UX 설계가 필요한 작업**: `designer` 에이전트를 호출한다.
4. **테스트, 코드 리뷰**: `qa` 에이전트를 호출한다.

### 호출 예시
```
# 새 기능 개발 시 (반드시 director부터)
→ director 에이전트 호출: "회원가입 기능을 개발해야 합니다. 코드베이스를 분석하고 작업을 분해해주세요."

# director가 내부적으로 수행하는 위임
→ designer 에이전트 호출: "회원가입 페이지 UI를 설계해주세요. 기존 컴포넌트는 ..."
→ programmer 에이전트 호출: "다음 설계에 따라 구현해주세요. ..."
→ qa 에이전트 호출: "구현된 코드를 검증해주세요."
```

### 금지 사항
- ❌ 에이전트 없이 직접 코드를 수정하는 것
- ❌ director를 건너뛰고 복잡한 기능을 바로 구현하는 것
- ❌ qa 검증 없이 작업을 완료하는 것

---

## 프로젝트 개요
미용실용 AI 기반 헤어 스타일 추천·시뮬레이션 웹앱. 고객 얼굴 분석 → 퍼스널컬러 진단 → 스타일 추천 → AI 시뮬레이션 이미지 생성.

## 기술 스택

### Frontend (`/frontend`)
- **프레임워크**: Next.js 16 + React 19 + TypeScript 5
- **스타일링**: Tailwind CSS 4
- **PWA**: @ducanh2912/next-pwa
- **AI**: TensorFlow.js (얼굴 감지)
- **기타**: QRCode.react
- **빌드**: `npm run build --webpack`
- **개발**: `npm run dev`

### Backend (`/backend`)
- **프레임워크**: FastAPI + Uvicorn
- **DB**: Supabase (PostgreSQL)
- **AI 서비스**: Anthropic Claude API, Replicate API
- **이미지처리**: Pillow, OpenCV
- **인증**: python-jose (JWT)
- **캐시**: Redis

### Database (`/supabase/schema.sql`)
- salons → designers → sessions → simulation_jobs
- hairstyles (카탈로그, face_shapes, style_tags)
- 인증: Supabase Auth + designers.auth_user_id 연동

## API 구조
```
/api/v1/sessions   — 고객 세션 CRUD
/api/v1/sessions   — 사진 업로드/처리 (photos 라우터)
/api/v1/sessions   — 얼굴 분석 (analysis 라우터)
/api/v1/styles     — 헤어스타일 카탈로그
/api/v1/simulate   — AI 시뮬레이션 실행
/health            — 헬스체크
```

## 프론트엔드 페이지 구조
```
/                          — 메인 페이지
/admin/catalog             — 헤어스타일 카탈로그 관리
/session/new               — 새 고객 세션 시작
/session/[id]              — 세션 상세 (사진촬영, 분석)
/session/[id]/simulate     — AI 시뮬레이션
/session/[id]/summary      — 결과 요약
```

## 컴포넌트 구조 (`/frontend/components`)
```
analysis/      — PersonalColorCard, FaceShapeCard
camera/        — CameraCapture
consultation/  — NotesPanel
simulation/    — SimulationResult, SimulationProgress
styles/        — StyleGrid, StyleCard
PwaInstallBanner.tsx
```

## 백엔드 서비스 (`/backend/app/services`)
```
claude_service.py     — Claude API (얼굴 분석, 추천)
replicate_service.py  — Replicate API (이미지 생성)
image_service.py      — 이미지 전처리
color_service.py      — 퍼스널컬러 분석
storage_service.py    — Supabase Storage 파일 관리
```

## 에이전트 팀 (`.claude/agents/`)

| 에이전트 | 역할 | 모델 | 핵심 도구 |
|---------|------|------|----------|
| **director** | 총괄·조율·아키텍처 | opus | Agent (팀 호출) |
| **programmer** | 풀스택 코드 구현 | sonnet | Write, Edit, Bash |
| **qa** | 테스트·코드리뷰 | sonnet | Read, Bash (수정 불가) |
| **designer** | UI/UX·컴포넌트 설계 | sonnet | Write, Edit |

### 작업 흐름 (반드시 이 순서를 따른다)
```
사용자 요청 → director (분석·분해)
  → designer (UI 설계, 필요시)
  → programmer (구현)
  → qa (검증)
  → 이슈 발견 시 → programmer (수정) → qa (재검증)
  → director (최종 보고)
```

## 코딩 컨벤션
- 컴포넌트: 파일당 하나, PascalCase
- Props: interface로 정의
- API 호출: fetch + try/catch + 에러 핸들링
- 스타일: Tailwind 유틸리티 클래스 사용
- 라이트모드: 기본 (bg-gray-50 베이스, violet-600 액센트)
- 언어: UI는 한국어, 코드/변수명은 영어
