# HairMaker 배포 가이드

## 구성

- **Backend (FastAPI)** → Railway
- **Frontend (Next.js)** → Vercel

---

## 1. Backend 배포 (Railway)

### 사전 준비

- [Upstash](https://upstash.com) Redis 인스턴스 생성
  - 리전: `us-east-1` (AWS) 또는 `us-east1` (GCP) 권장
  - **Redis URL** 복사 (형식: `rediss://default:비밀번호@xxxx.upstash.io:6379`)

### Railway 배포

1. [railway.app](https://railway.app) → **New Project** → GitHub 레포 연결
2. `backend` 디렉토리를 서비스로 설정
3. **Variables** 탭에서 환경변수 추가:

| 변수명 | 값 |
|---|---|
| `ANTHROPIC_API_KEY` | `sk-ant-...` |
| `REPLICATE_API_TOKEN` | `r8_...` |
| `SUPABASE_URL` | `https://xxxx.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | `eyJ...` |
| `SUPABASE_ANON_KEY` | `eyJ...` |
| `REDIS_URL` | `rediss://default:...@....upstash.io:6379` |
| `CORS_ORIGINS` | Vercel 배포 후 프론트엔드 URL 입력 |
| `ENVIRONMENT` | `production` |
| `PORT` | `8000` |

4. **Settings → Networking → Generate Domain** 으로 도메인 생성
5. `https://xxxx.railway.app/docs` 접속해서 API 정상 동작 확인

---

## 2. Frontend 배포 (Vercel)

1. [vercel.com](https://vercel.com) → **New Project** → GitHub 레포 연결
2. **Root Directory** → `frontend` 로 변경 (필수)
3. **Environment Variables** 추가:

| 변수명 | 값 |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://xxxx.railway.app` (Railway 백엔드 URL) |

4. **Deploy** 클릭
5. 배포 완료 후 Vercel URL 확인 (예: `https://xxxx.vercel.app`)

---

## 3. CORS 연결

Vercel 배포 완료 후 Railway backend의 `CORS_ORIGINS` 환경변수를 Vercel URL로 업데이트:

```
CORS_ORIGINS=https://xxxx.vercel.app
```

저장하면 Railway가 자동 재배포됨.

---

## 4. 재배포 방법

코드 수정 후 GitHub에 push하면 Railway/Vercel 모두 자동 재배포됨.

```bash
git add .
git commit -m "커밋 메시지"
git push
```

---

## 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| `libgl1-mesa-glx` 빌드 실패 | Debian trixie에서 패키지명 변경 | `libgl1`으로 교체 |
| `ValidationError: Field required` | Railway 환경변수 미설정 | Variables 탭에서 추가 |
| `Application failed to respond` | PORT 환경변수 미설정 | `PORT=8000` 추가 |
| `failed to fetch` | CORS 미설정 | `CORS_ORIGINS`에 Vercel URL 추가 |
